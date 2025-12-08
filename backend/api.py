"""
FastAPI backend for File Organizer Desktop GUI.
Provides REST API endpoints for classification, review, and migration.
"""
import os
import yaml
import shutil
import datetime
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
from file_utils import collect_file_paths, separate_files_by_type, read_file_data, normalize_filename
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
# Import LLM Engine
from llm_engine import LLMEngine

# ... (keep other imports)

# Global state
db = Database()
llm_engine = None  # Initialize lazily or on startup
# classifier = None # Removed old classifier
# image_inference = None # Removed old inference
# text_inference = None # Removed old inference
current_session = {
    'input_path': None,
    'output_path': None,
    'is_classifying': False,
    'classification_progress': 0
}

# Pydantic models
class ScanRequest(BaseModel):
    input_path: str
    output_path: Optional[str] = None
    normalize: bool = False


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


def initialize_models():
    """Initialize AI models if not already initialized."""
    global llm_engine
    if llm_engine is None:
        print("Initializing LLM Engine...")
        llm_engine = LLMEngine()
        print("LLM Engine initialized.")

@api_router.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_loaded": llm_engine is not None,
        "database_connected": os.path.exists(db.db_path)
    }


@api_router.post("/scan")
async def scan_directory(request: ScanRequest):
    """Scan a directory for files."""
    if not os.path.exists(request.input_path):
        raise HTTPException(status_code=400, detail="Directory not found")
    
    current_session['input_path'] = request.input_path
    current_session['output_path'] = request.output_path or os.path.join(request.input_path, "Organized")
    
    # Count files
    file_paths = collect_file_paths(request.input_path)
    
    return {
        "status": "scanned", 
        "count": len(file_paths), 
        "path": request.input_path,
        "message": f"Found {len(file_paths)} files"
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
    
    return {"status": "started", "message": "Classification started (Ollama/Llama3)"}

def run_classification(mode: str):
    """Run classification using LLM Engine."""
    global llm_engine
    try:
        if llm_engine is None:
            initialize_models()

        file_paths = collect_file_paths(current_session['input_path'])
        total_files = len(file_paths)
        
        for idx, fp in enumerate(file_paths):
            try:
                # Extract text (using existing helpers or simple read)
                text_content = ""
                try:
                    text_content = read_file_data(fp)
                except Exception as e:
                    print(f"Error reading {fp}: {e}")
                
                # Calculate SHA256
                import hashlib
                sha256_hash = ""
                try:
                    with open(fp, "rb") as f:
                        bytes = f.read() 
                        sha256_hash = hashlib.sha256(bytes).hexdigest()
                except Exception:
                    pass

                # Classify using LLM Engine
                original_filename = os.path.basename(fp)
                print(f"Classifying: {original_filename}")
                classification = llm_engine.classify_document(original_filename, text_content or "")
                
                # Create item
                item = DocumentItem(
                    id="",
                    source_path=fp,
                    original_filename=original_filename,
                    extracted_text=text_content[:1000] if text_content else "",
                    proposed_workspace=classification['workspace'],
                    proposed_subpath=classification['scope'], # Mapping scope to subpath
                    proposed_filename=os.path.splitext(original_filename)[0], # Keep original stem
                    confidence=int(classification['confidence'] * 100) if classification['confidence'] <= 1 else int(classification['confidence']), # Handle 0-1 vs 0-100
                    status=ItemStatus.PENDING,
                    description=classification['reasoning'],
                    file_size=os.path.getsize(fp) if os.path.exists(fp) else None,
                    file_extension=os.path.splitext(fp)[1],
                    sha256=sha256_hash,
                    ai_prompt=classification['prompt'],
                    ai_response=classification['raw_response']
                )
                db.create_item(item)
                
                print(f"Classified: {original_filename} -> {classification['workspace']}/{classification['scope']}")

            except Exception as e:
                print(f"Error processing file {fp}: {e}")
            
            # Update progress
            current_session['classification_progress'] = int(((idx + 1) / total_files) * 100)
        
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


def generate_migration_report(items: List[DocumentItem], output_path: str) -> str:
    """Generate a migration report."""
    report_path = os.path.join(output_path, f"migration_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    with open(report_path, "w") as f:
        f.write(f"# Migration Report - {datetime.datetime.now().isoformat()}\n\n")
        f.write(f"Total items: {len(items)}\n\n")
        f.write("| Original Filename | Destination | Status |\n")
        f.write("| ----------------- | ----------- | ------ |\n")
        
        for item in items:
            dest = os.path.join(item.proposed_workspace, item.proposed_subpath or "", item.proposed_filename + item.file_extension)
            f.write(f"| {item.original_filename} | {dest} | {item.status} |\n")
            
    return report_path


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
    elif request.action == "reject_and_move":
        # First mark as rejected
        count = db.bulk_update_status(request.item_ids, ItemStatus.REJECTED)
        # Then move files
        items = db.get_items_by_ids(request.item_ids)
        rejected_dir = os.path.join(os.path.dirname(current_session['input_path']), '_Rejected')
        os.makedirs(rejected_dir, exist_ok=True)
        for item in items:
            try:
                dest = os.path.join(rejected_dir, os.path.basename(item.source_path))
                shutil.move(item.source_path, dest)
                # Update path in DB or just leave as is (since it's rejected)
                # Ideally we update the source_path, but for now just moving is enough
            except Exception as e:
                print(f"Error moving {item.source_path}: {e}")
    elif request.action == "delete":
        # Delete files
        items = db.get_items_by_ids(request.item_ids)
        deleted_count = 0
        for item in items:
            try:
                if os.path.exists(item.source_path):
                    os.remove(item.source_path)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {item.source_path}: {e}")
        # Mark as rejected/deleted in DB (or remove?)
        # For now, let's mark as REJECTED and add note
        db.bulk_update_status(request.item_ids, ItemStatus.REJECTED)
        count = deleted_count
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
            db.update_item(item.id, {"status": ItemStatus.MIGRATED, "migrated_at": datetime.datetime.now().isoformat()})
            migrated += 1
            
        except Exception as e:
            print(f"Error migrating {item.source_path}: {e}")
    
    # Generate report
    report_path = generate_migration_report(items, output_path)
    
    return {"message": f"Migrated {migrated} files", "migrated": migrated, "report_path": report_path}


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


# Include all API routes
app.include_router(api_router, prefix="/api")

# Serve admin.html and taxonomy-editor.html
@app.get("/admin")
async def serve_admin():
    """Serve the admin tools page."""
    admin_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'admin.html')
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="Admin page not found")

@app.get("/taxonomy-editor")
async def serve_taxonomy_editor():
    """Serve the taxonomy editor page."""
    editor_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'taxonomy-editor.html')
    if os.path.exists(editor_path):
        return FileResponse(editor_path)
    raise HTTPException(status_code=404, detail="Taxonomy editor not found")

# Serve static files for taxonomy editor
@app.get("/taxonomy-editor.css")
async def serve_taxonomy_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'taxonomy-editor.css')
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404)

@app.get("/taxonomy-editor.js")
async def serve_taxonomy_js():
    js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'taxonomy-editor.js')
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404)

# Serve backend/taxonomy.yaml for taxonomy editor
@app.get("/backend/taxonomy.yaml")
async def serve_taxonomy_yaml():
    """Serve the taxonomy YAML file."""
    yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'taxonomy.yaml')
    if os.path.exists(yaml_path):
        return FileResponse(yaml_path, media_type="application/x-yaml")
    raise HTTPException(status_code=404, detail="Taxonomy YAML not found")


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
async def serve_react_app(full_path: str):
    """Serve the React app for all other routes."""
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
    index_path = os.path.join(frontend_dist, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not built. Run 'npm run build' in the frontend directory."}
