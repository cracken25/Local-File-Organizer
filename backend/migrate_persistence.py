"""
Database migration script to add file persistence columns.

Adds columns needed for file-level tracking and re-classification detection.
"""
import sqlite3
import os
from datetime import datetime


def run_migration(db_path: str = "file_organizer.db"):
    """
    Run database migration to add persistence columns.
    
    Args:
        db_path: Path to SQLite database file
    """
    # Backup database first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(document_items)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add file_hash column
        if 'file_hash' not in columns:
            print("Adding column: file_hash...")
            cursor.execute("ALTER TABLE document_items ADD COLUMN file_hash TEXT")
            print("✓ file_hash column added")
        else:
            print("✓ file_hash column already exists")
        
        # Add source_folder column
        if 'source_folder' not in columns:
            print("Adding column: source_folder...")
            cursor.execute("ALTER TABLE document_items ADD COLUMN source_folder TEXT")
            print("✓ source_folder column added")
        else:
            print("✓ source_folder column already exists")
        
        # Add processed_at column
        if 'processed_at' not in columns:
            print("Adding column: processed_at...")
            cursor.execute("ALTER TABLE document_items ADD COLUMN processed_at TEXT")
            print("✓ processed_at column added")
        else:
            print("✓ processed_at column already exists")
        
        # Add file_modified_time column
        if 'file_modified_time' not in columns:
            print("Adding column: file_modified_time...")
            cursor.execute("ALTER TABLE document_items ADD COLUMN file_modified_time TEXT")
            print("✓ file_modified_time column added")
        else:
            print("✓ file_modified_time column already exists")
        
        # Create indexes for performance
        print("\nCreating indexes...")
        
        # Index on file_hash for quick lookup
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON document_items(file_hash)")
            print("✓ Created index: idx_file_hash")
        except sqlite3.OperationalError as e:
            print(f"  Index idx_file_hash may already exist: {e}")
        
        # Index on source_folder for folder-based queries
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_folder ON document_items(source_folder)")
            print("✓ Created index: idx_source_folder")
        except sqlite3.OperationalError as e:
            print(f"  Index idx_source_folder may already exist: {e}")
        
        # Index on source_path for path-based lookups
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_path ON document_items(source_path)")
            print("✓ Created index: idx_source_path")
        except sqlite3.OperationalError as e:
            print(f"  Index idx_source_path may already exist: {e}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"Database backup available at: {backup_path}")
        raise
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Persistence Columns")
    print("=" * 60)
    print()
    
    run_migration()
    
    print()
    print("=" * 60)
    print("Migration Complete")
    print("=" * 60)
