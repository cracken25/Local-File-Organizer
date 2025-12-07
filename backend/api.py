"""
FastAPI backend for File Organizer Desktop GUI.
Provides REST API endpoints for classification, review, and migration.
"""
import os
import yaml
import shutil
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from enum import Enum

# Import existing modules
from classifier import TaxonomyClassifier
from file_utils import collect_file_paths, separate_files_by_type, read_file_data
from data_processing_common import compute_operations, execute_operations
from text_data_processing import process_text_files
from image_data_processing import process_image_files
from output_filter import filter_specific_output
from nexa_adapter import NexaVLMInference, NexaTextInference  # Use adapter for compatibility

# Import database
from database import Database, DocumentItem, ItemStatus

# Import config store
from config_store import get_last_paths, save_last_paths

# Initialize FastAPI app
app = FastAPI(title="File Organizer API", version="1.0.0")

# Create API router for all API endpoints
api_router = APIRouter()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static file serving for production build
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
if os.path.exists(frontend_dist):
    # Mount static assets
    assets_dir = os.path.join(frontend_dist, 'assets')
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Global state
db = Database()
classifier = None
image_inference = None
text_inference = None
webview_window = None  # Store webview window reference
current_session = {
    'input_path': None,
    'output_path': None,
    'is_classifying': False,
    'classification_progress': 0
}

def set_webview_window(window):
    """Set the webview window reference for folder dialogs."""
    global webview_window
    webview_window = window


# Pydantic models
class ScanRequest(BaseModel):
    input_path: str
    output_path: Optional[str] = None


class ClassifyRequest(BaseModel):
    mode: str = "content"  # content, date, type


class ItemUpdateRequest(BaseModel):
    proposed_workspace: Optional[str] = None
    proposed_subpath: Optional[str] = None
    proposed_filename: Optional[str] = None
    status: Optional[str] = None


class BulkActionRequest(BaseModel):
    item_ids: List[str]
    action: str  # approve, ignore, reject
    workspace: Optional[str] = None  # for bulk workspace change


class MigrateRequest(BaseModel):
    output_path: Optional[str] = None


# Helper functions
def initialize_models():
    """Initialize AI models if not already initialized."""
    global image_inference, text_inference, classifier
    
    if image_inference is None or text_inference is None:
        model_path = "llava-v1.6-vicuna-7b:q4_0"
        model_path_text = "Llama3.2-3B-Instruct:q3_K_M"
        
        with filter_specific_output():
            # Initialize VLM for images (using adapter)
            image_inference = NexaVLMInference(
                model_path=model_path,
                temperature=0.3,
                max_new_tokens=3000,
                top_k=3,
                top_p=0.2
            )
            
            # Initialize LLM for text (using adapter)
            text_inference = NexaTextInference(
                model_path=model_path_text,
                temperature=0.5,
                max_new_tokens=3000,
                top_k=3,
                top_p=0.3
            )
    
    if classifier is None:
        taxonomy_path = os.path.join(os.path.dirname(__file__), 'taxonomy.yaml')
        classifier = TaxonomyClassifier(taxonomy_path)


# API Endpoints

@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {"message": "File Organizer API", "version": "1.0.0"}


@app.get("/")
async def serve_spa():
    """Serve the React SPA."""
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
    index_path = os.path.join(frontend_dist, 'index.html')
    
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    else:
        return {"message": "File Organizer API", "version": "1.0.0", "note": "Frontend not built. Run 'npm run build' in frontend/"}


@api_router.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_loaded": image_inference is not None and text_inference is not None,
        "database_connected": db.conn is not None
    }


@api_router.post("/scan")
async def scan_directory(request: ScanRequest):
    """Scan a directory and return file list."""
    if not os.path.exists(request.input_path):
        raise HTTPException(status_code=404, detail="Input path does not exist")
    
    if not os.path.isdir(request.input_path):
        raise HTTPException(status_code=400, detail="Input path must be a directory")
    
    # Clear previous session
    db.clear_all()
    
    # Update session
    current_session['input_path'] = request.input_path
    current_session['output_path'] = request.output_path or os.path.join(
        os.path.dirname(request.input_path), 'organized_folder'
    )
    
    # Save paths for persistence
    save_last_paths(
        input_path=request.input_path,
        output_path=current_session['output_path']
    )
    
    # Collect file paths
    file_paths = collect_file_paths(request.input_path)
    
    return {
        "input_path": request.input_path,
        "output_path": current_session['output_path'],
        "file_count": len(file_paths),
        "files": [{"path": fp, "name": os.path.basename(fp)} for fp in file_paths[:100]]  # Limit to first 100
    }


@api_router.post("/classify")
async def classify_files(request: ClassifyRequest, background_tasks: BackgroundTasks):
    """Classify files in the scanned directory."""
    if not current_session['input_path']:
        raise HTTPException(status_code=400, detail="No directory scanned. Call /scan first.")
    
    if current_session['is_classifying']:
        raise HTTPException(status_code=409, detail="Classification already in progress")
    
    # Initialize AI models
    initialize_models()
    
    # Start classification in background
    background_tasks.add_task(run_classification, request.mode)
    
    current_session['is_classifying'] = True
    current_session['classification_progress'] = 0
    
    return {"status": "started", "message": "Classification started (simple mode - keyword-based)"}


def run_classification(mode: str):
    """Run classification (called in background)."""
    try:
        file_paths = collect_file_paths(current_session['input_path'])
        
        if mode == "content":
            # Separate files by type
            image_files, text_files = separate_files_by_type(file_paths)
            
            # Prepare text tuples
            text_tuples = []
            for fp in text_files:
                text_content = read_file_data(fp)
                if text_content:
                    text_tuples.append((fp, text_content))
            
            # Process files
            total_files = len(image_files) + len(text_tuples)
            processed = 0
            
            # Process images
            data_images = process_image_files(image_files, image_inference, text_inference, classifier, silent=True)
            for data in data_images:
                create_item_from_classification(data)
                processed += 1
                current_session['classification_progress'] = int((processed / total_files) * 100)
            
            # Process texts
            data_texts = process_text_files(text_tuples, text_inference, classifier, silent=True)
            for data in data_texts:
                create_item_from_classification(data)
                processed += 1
                current_session['classification_progress'] = int((processed / total_files) * 100)
        
        elif mode == "date":
            # Date-based organization (simplified for now)
            for fp in file_paths[:20]:  # Limit for demo
                item = DocumentItem(
                    id="",
                    source_path=fp,
                    original_filename=os.path.basename(fp),
                    extracted_text="",
                    proposed_workspace="By_Date",
                    proposed_subpath="",
                    proposed_filename=os.path.basename(fp),
                    confidence=5,
                    status=ItemStatus.PENDING,
                    description="Date-based organization"
                )
                db.create_item(item)
        
        elif mode == "type":
            # Type-based organization (simplified for now)
            for fp in file_paths[:20]:  # Limit for demo
                ext = os.path.splitext(fp)[1]
                item = DocumentItem(
                    id="",
                    source_path=fp,
                    original_filename=os.path.basename(fp),
                    extracted_text="",
                    proposed_workspace="By_Type",
                    proposed_subpath=ext,
                    proposed_filename=os.path.basename(fp),
                    confidence=5,
                    status=ItemStatus.PENDING,
                    description="Type-based organization"
                )
                db.create_item(item)
        
        current_session['is_classifying'] = False
        current_session['classification_progress'] = 100
        
    except Exception as e:
        current_session['is_classifying'] = False
        current_session['classification_progress'] = -1
        print(f"Classification error: {e}")


def run_classification_simple(mode: str):
    """Simple classification without AI models (temporary fallback)."""
    try:
        file_paths = collect_file_paths(current_session['input_path'])
        total_files = len(file_paths)
        
        for idx, fp in enumerate(file_paths[:50]):  # Limit to 50 files for demo
            # Simple heuristic-based classification
            filename = os.path.basename(fp).lower()
            full_path_lower = fp.lower()
            ext = os.path.splitext(fp)[1].lower()
            
            # Determine workspace based on keywords
            # Check paystubs FIRST (more specific than generic tax terms)
            workspace = "Personal"
            subpath = "Misc"
            confidence = 3
            matched_keywords = []
            classification_reason = "Default classification"
            
            # Check path AND filename for better matching
            if any(kw in full_path_lower for kw in ['paystub', 'paycheck', 'pay stub', 'salary', 'earnings']):
                workspace = "Finance"
                subpath = "Income/Paystubs"
                confidence = 4
                matched_keywords = [kw for kw in ['paystub', 'paycheck', 'pay stub', 'salary', 'earnings'] if kw in full_path_lower]
                classification_reason = f"Matched paystub keywords: {matched_keywords}"
            elif any(kw in full_path_lower for kw in ['tax', 'w2', 'w-2', '1099', 'return']):
                workspace = "Finance"
                subpath = "Taxes/Federal"
                confidence = 4
                matched_keywords = [kw for kw in ['tax', 'w2', 'w-2', '1099', 'return'] if kw in full_path_lower]
                classification_reason = f"Matched tax keywords: {matched_keywords}"
            elif any(kw in full_path_lower for kw in ['invoice', 'receipt', 'bill']):
                workspace = "Finance"
                subpath = "Receipts"
                confidence = 3
                matched_keywords = [kw for kw in ['invoice', 'receipt', 'bill'] if kw in full_path_lower]
                classification_reason = f"Matched receipt keywords: {matched_keywords}"
            elif any(kw in full_path_lower for kw in ['bank', 'statement', 'account']):
                workspace = "Finance"
                subpath = "Banking"
                confidence = 3
                matched_keywords = [kw for kw in ['bank', 'statement', 'account'] if kw in full_path_lower]
                classification_reason = f"Matched banking keywords: {matched_keywords}"
            elif any(kw in full_path_lower for kw in ['contract', 'agreement']):
                workspace = "Legal"
                subpath = "Contracts"
                confidence = 3
                matched_keywords = [kw for kw in ['contract', 'agreement'] if kw in full_path_lower]
                classification_reason = f"Matched legal keywords: {matched_keywords}"
            elif any(kw in full_path_lower for kw in ['resume', 'cv']):
                workspace = "Career"
                subpath = "Documents"
                confidence = 4
                matched_keywords = [kw for kw in ['resume', 'cv'] if kw in full_path_lower]
                classification_reason = f"Matched career keywords: {matched_keywords}"
            else:
                classification_reason = f"No keywords matched in '{filename}' or path"
            
            # Create item with debug information
            debug_info = f"""Classification Details:
- File: {os.path.basename(fp)}
- Full path: {fp}
- Reason: {classification_reason}
- Matched keywords: {matched_keywords if matched_keywords else 'none'}
- Workspace: {workspace}
- Subpath: {subpath}
- Confidence: {confidence}/5"""
            
            item = DocumentItem(
                id="",
                source_path=fp,
                original_filename=os.path.basename(fp),
                extracted_text="",
                proposed_workspace=workspace,
                proposed_subpath=subpath,
                proposed_filename=os.path.basename(fp),
                confidence=confidence,
                status=ItemStatus.PENDING,
                description=debug_info,
                file_size=os.path.getsize(fp) if os.path.exists(fp) else None,
                file_extension=ext
            )
            db.create_item(item)
            
            print(f"Classified: {os.path.basename(fp)} → {workspace}/{subpath} ({confidence}/5)")
            
            # Update progress
            current_session['classification_progress'] = int(((idx + 1) / min(total_files, 50)) * 100)
        
        current_session['is_classifying'] = False
        current_session['classification_progress'] = 100
        
    except Exception as e:
        current_session['is_classifying'] = False
        current_session['classification_progress'] = -1
        print(f"Classification error: {e}")
        import traceback
        traceback.print_exc()


def create_item_from_classification(data: Dict[str, Any]):
    """Create a DocumentItem from classification data."""
    item = DocumentItem(
        id="",
        source_path=data['file_path'],
        original_filename=os.path.basename(data['file_path']),
        extracted_text=data.get('description', '')[:1000],  # Truncate
        proposed_workspace=data['workspace'],
        proposed_subpath=data.get('subpath', ''),
        proposed_filename=data['filename'],
        confidence=data.get('confidence', 0),
        status=ItemStatus.PENDING,
        description=data.get('description', ''),
        file_size=os.path.getsize(data['file_path']) if os.path.exists(data['file_path']) else None,
        file_extension=os.path.splitext(data['file_path'])[1]
    )
    db.create_item(item)


@api_router.get("/classify/status")
async def classification_status():
    """Get classification progress status."""
    return {
        "is_classifying": current_session['is_classifying'],
        "progress": current_session['classification_progress']
    }


@api_router.get("/items")
async def get_items(
    status: Optional[str] = None,
    workspace: Optional[str] = None,
    min_confidence: Optional[int] = None,
    max_confidence: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get classified items with optional filters."""
    items = db.get_items(
        status=status,
        workspace=workspace,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        limit=limit,
        offset=offset
    )
    
    # Return array of item dicts
    return [item.to_dict() for item in items]


@api_router.get("/items/{item_id}")
async def get_item(item_id: str):
    """Get a single item by ID."""
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_dict()


@api_router.patch("/items/{item_id}")
async def update_item(item_id: str, request: ItemUpdateRequest):
    """Update a document item."""
    updates = {}
    if request.proposed_workspace is not None:
        updates['proposed_workspace'] = request.proposed_workspace
    if request.proposed_subpath is not None:
        updates['proposed_subpath'] = request.proposed_subpath
    if request.proposed_filename is not None:
        updates['proposed_filename'] = request.proposed_filename
    if request.status is not None:
        updates['status'] = request.status
    
    item = db.update_item(item_id, updates)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item.to_dict()


@api_router.post("/items/bulk-action")
async def bulk_action(request: BulkActionRequest):
    """Perform bulk action on items."""
    if not request.item_ids:
        raise HTTPException(status_code=400, detail="No items specified")
    
    if request.action == "approve":
        count = db.bulk_update_status(request.item_ids, ItemStatus.APPROVED)
    elif request.action == "ignore":
        count = db.bulk_update_status(request.item_ids, ItemStatus.IGNORED)
    elif request.action == "reject":
        count = db.bulk_update_status(request.item_ids, ItemStatus.REJECTED)
    elif request.action == "set_workspace" and request.workspace:
        count = db.bulk_update_workspace(request.item_ids, request.workspace)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return {"updated": count}


@api_router.post("/migrate")
async def migrate_files(request: MigrateRequest):
    """Migrate approved files to output directory."""
    output_path = request.output_path or current_session.get('output_path')
    if not output_path:
        raise HTTPException(status_code=400, detail="No output path specified")
    
    # Get approved items
    items = db.get_items(status=ItemStatus.APPROVED)
    if not items:
        return {"message": "No approved items to migrate", "migrated": 0}
    
    # Create output directory
    os.makedirs(output_path, exist_ok=True)
    
    # Migrate files
    migrated = 0
    for item in items:
        try:
            # Build target path
            if item.proposed_subpath:
                target_dir = os.path.join(output_path, item.proposed_workspace, item.proposed_subpath)
            else:
                target_dir = os.path.join(output_path, item.proposed_workspace)
            
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy file
            target_file = os.path.join(target_dir, item.proposed_filename + item.file_extension)
            shutil.copy2(item.source_path, target_file)
            
            # Update status
            db.update_item(item.id, {"status": ItemStatus.MIGRATED})
            migrated += 1
            
        except Exception as e:
            print(f"Error migrating {item.source_path}: {e}")
    
    return {"message": f"Migrated {migrated} files", "migrated": migrated}


@api_router.get("/taxonomy")
async def get_taxonomy():
    """Get workspace taxonomy."""
    taxonomy_path = os.path.join(os.path.dirname(__file__), 'taxonomy.yaml')
    with open(taxonomy_path, 'r') as f:
        taxonomy = yaml.safe_load(f)
    return taxonomy


@api_router.get("/statistics")
async def get_statistics():
    """Get classification statistics."""
    return db.get_statistics()


@api_router.get("/preview/{item_id}")
async def get_preview(item_id: str):
    """Get file preview for an item."""
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Return extracted text as preview
    return {
        "id": item_id,
        "type": item.file_extension,
        "preview": item.extracted_text[:1000] if item.extracted_text else "",
        "full_text_available": len(item.extracted_text) > 1000 if item.extracted_text else False
    }


@api_router.post("/browse/folder")
async def browse_folder(request: dict):
    """
    Trigger native folder selection dialog through PyWebView.
    Returns the selected folder path.
    """
    import webview
    
    title = request.get('title', 'Select Folder')
    
    try:
        # Try to use webview if available
        if webview.windows:
            window = webview.windows[0]
            result = window.create_file_dialog(
                webview.FOLDER_DIALOG,
                directory='',
                allow_multiple=False
            )
            if result and len(result) > 0:
                return {"path": result[0], "success": True}
        
        return {"path": None, "success": False, "error": "No webview window available"}
    
    except Exception as e:
        return {"path": None, "success": False, "error": str(e)}


@api_router.delete("/session")
async def clear_session():
    """Clear current session and database."""
    db.clear_all()
    current_session['input_path'] = None
    current_session['output_path'] = None
    current_session['is_classifying'] = False
    current_session['classification_progress'] = 0
    
    return {"message": "Session cleared"}


@api_router.get("/config/paths")
async def get_config_paths():
    """Get the last used input/output paths."""
    paths = get_last_paths()
    print(f"Returning saved paths: {paths}")
    return paths


@api_router.post("/config/paths")
async def save_config_paths(data: dict):
    """Save the last used input/output paths."""
    input_path = data.get('input_path')
    output_path = data.get('output_path')
    mode = data.get('mode')
    
    print(f"Saving paths: input={input_path}, output={output_path}, mode={mode}")
    
    success = save_last_paths(input_path=input_path, output_path=output_path, mode=mode)
    
    return {"success": success, "message": "Paths saved" if success else "Failed to save paths"}


# Include API router with /api prefix
app.include_router(api_router, prefix="/api")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("File Organizer API starting...")
    print(f"Database initialized at: {db.db_path}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    db.close()
    print("File Organizer API shutdown")


# Catch-all route for SPA (must be last)
@app.get("/{full_path:path}")
async def serve_spa_catchall(full_path: str):
    """Serve SPA for all non-API routes."""
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
    
    # Check if it's a file request
    file_path = os.path.join(frontend_dist, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise serve index.html for SPA routing
    index_path = os.path.join(frontend_dist, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback
    raise HTTPException(status_code=404, detail="Not found")

