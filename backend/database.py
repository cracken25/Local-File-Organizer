"""
SQLite database for document items.
"""
import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class ItemStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    IGNORED = "ignored"
    REJECTED = "rejected"
    MIGRATED = "migrated"


class DocumentItem:
    """Document item data model."""
    
    def __init__(
        self,
        id: str,
        source_path: str,
        original_filename: str,
        extracted_text: str,
        proposed_workspace: str,
        proposed_subpath: str,
        proposed_filename: str,
        confidence: int,
        status: ItemStatus,
        description: str = "",
        file_size: Optional[int] = None,
        file_extension: Optional[str] = None,
        migrated_path: Optional[str] = None,
        migrated_at: Optional[str] = None,
        **kwargs
    ):
        self.id = id or str(uuid.uuid4())
        self.source_path = source_path
        self.original_filename = original_filename
        self.extracted_text = extracted_text
        self.proposed_workspace = proposed_workspace
        self.proposed_subpath = proposed_subpath
        self.proposed_filename = proposed_filename
        self.confidence = confidence
        self.status = status.value if isinstance(status, ItemStatus) else status
        self.description = description
        self.file_size = file_size
        self.file_extension = file_extension
        self.migrated_path = migrated_path
        self.migrated_at = migrated_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_path': self.source_path,
            'original_filename': self.original_filename,
            'extracted_text': self.extracted_text,
            'proposed_workspace': self.proposed_workspace,
            'proposed_subpath': self.proposed_subpath,
            'proposed_filename': self.proposed_filename,
            'confidence': self.confidence,
            'status': self.status,
            'description': self.description,
            'file_size': self.file_size,
            'file_extension': self.file_extension,
            'migrated_path': self.migrated_path,
            'migrated_at': self.migrated_at,
        }


class Database:
    """SQLite database for document items."""
    
    def __init__(self, db_path: str = "file_organizer.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_items (
                id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                extracted_text TEXT,
                proposed_workspace TEXT NOT NULL,
                proposed_subpath TEXT,
                proposed_filename TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                status TEXT NOT NULL,
                description TEXT,
                file_size INTEGER,
                file_extension TEXT,
                migrated_path TEXT,
                migrated_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_item(self, item: DocumentItem) -> DocumentItem:
        """Create a new document item."""
        if not item.id:
            item.id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO document_items (
                id, source_path, original_filename, extracted_text,
                proposed_workspace, proposed_subpath, proposed_filename,
                confidence, status, description, file_size, file_extension,
                migrated_path, migrated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.id,
            item.source_path,
            item.original_filename,
            item.extracted_text,
            item.proposed_workspace,
            item.proposed_subpath,
            item.proposed_filename,
            item.confidence,
            item.status,
            item.description,
            item.file_size,
            item.file_extension,
            item.migrated_path,
            item.migrated_at,
        ))
        
        conn.commit()
        conn.close()
        
        return item
    
    def get_items(
        self,
        status: Optional[str] = None,
        workspace: Optional[str] = None,
        min_confidence: Optional[int] = None,
        max_confidence: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[DocumentItem]:
        """Get all document items with optional filters."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM document_items WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if workspace:
            query += " AND proposed_workspace = ?"
            params.append(workspace)
        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(min_confidence)
        if max_confidence is not None:
            query += " AND confidence <= ?"
            params.append(max_confidence)
        
        query += " ORDER BY confidence ASC"
        
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        items = []
        for row in rows:
            item = DocumentItem(
                id=row['id'],
                source_path=row['source_path'],
                original_filename=row['original_filename'],
                extracted_text=row['extracted_text'] or '',
                proposed_workspace=row['proposed_workspace'],
                proposed_subpath=row['proposed_subpath'] or '',
                proposed_filename=row['proposed_filename'],
                confidence=row['confidence'],
                status=row['status'],
                description=row['description'] or '',
                file_size=row['file_size'],
                file_extension=row['file_extension'],
                migrated_path=row['migrated_path'],
                migrated_at=row['migrated_at'],
            )
            items.append(item)
        
        return items
    
    def get_item(self, item_id: str) -> Optional[DocumentItem]:
        """Get a single document item by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM document_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return DocumentItem(
            id=row['id'],
            source_path=row['source_path'],
            original_filename=row['original_filename'],
            extracted_text=row['extracted_text'] or '',
            proposed_workspace=row['proposed_workspace'],
            proposed_subpath=row['proposed_subpath'] or '',
            proposed_filename=row['proposed_filename'],
            confidence=row['confidence'],
            status=row['status'],
            description=row['description'] or '',
            file_size=row['file_size'],
            file_extension=row['file_extension'],
            migrated_path=row['migrated_path'],
            migrated_at=row['migrated_at'],
        )
    
    def update_item(self, item_id: str, updates: Dict[str, Any]) -> Optional[DocumentItem]:
        """Update a document item."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        params.append(item_id)
        
        query = f"UPDATE document_items SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        return self.get_item(item_id)
    
    def count_items(
        self,
        status: Optional[str] = None,
        workspace: Optional[str] = None,
        min_confidence: Optional[int] = None,
        max_confidence: Optional[int] = None
    ) -> int:
        """Count document items with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM document_items WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if workspace:
            query += " AND proposed_workspace = ?"
            params.append(workspace)
        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(min_confidence)
        if max_confidence is not None:
            query += " AND confidence <= ?"
            params.append(max_confidence)
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def clear_all(self):
        """Clear all document items."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM document_items")
        conn.commit()
        conn.close()
    
    def close(self):
        """Close database connection."""
        pass  # SQLite connections are opened per-operation

