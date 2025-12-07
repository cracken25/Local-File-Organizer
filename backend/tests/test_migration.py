import os
import pytest
from database import DocumentItem, ItemStatus

def test_migration_report(client, mock_db, tmp_path):
    # Setup
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create approved items in DB
    item1 = DocumentItem(
        id="1",
        source_path="/tmp/file1.txt",
        original_filename="file1.txt",
        extracted_text="",
        proposed_workspace="Finance",
        proposed_subpath="Invoices",
        proposed_filename="Invoice_001",
        confidence=0.9,
        status=ItemStatus.APPROVED,
        file_extension=".txt"
    )
    mock_db.create_item(item1)
    
    # Create dummy source file
    (tmp_path / "file1.txt").touch()
    # Update item source path to point to real file
    mock_db.update_item("1", {"source_path": str(tmp_path / "file1.txt")})

    # Call migrate endpoint
    response = client.post("/api/migrate", json={"output_path": str(output_dir)})
    assert response.status_code == 200
    data = response.json()
    
    assert data["migrated"] == 1
    assert "report_path" in data
    report_path = data["report_path"]
    assert os.path.exists(report_path)
    
    # Verify report content
    with open(report_path, "r") as f:
        content = f.read()
        assert "# Migration Report" in content
        assert "file1.txt" in content
        assert "Invoice_001" in content
        assert "Finance" in content
