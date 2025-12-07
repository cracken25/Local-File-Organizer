import pytest
from unittest.mock import patch

@pytest.mark.integration
def test_scan_endpoint(client, sample_file_path):
    """Test the /scan endpoint."""
    response = client.post("/api/scan", json={
        "input_path": sample_file_path,
        "output_path": None
    })
    assert response.status_code == 200
    data = response.json()
    assert "file_count" in data
    assert data["file_count"] > 0

@pytest.mark.integration
def test_items_endpoint(client):
    """Test the /items endpoint."""
    response = client.get("/api/items")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.integration
def test_health_check(client):
    """Test a basic health check (root endpoint if exists, or just ensure app is up)."""
    # Assuming there might not be a root endpoint, but checking if 404 is returned cleanly is also a valid test of the app running
    response = client.get("/")
    assert response.status_code in [200, 404]

def test_scan_normalization(client, tmp_path):
    """Test scanning with filename normalization."""
    # Create dummy files for testing
    (tmp_path / "test_file.txt").touch()
    (tmp_path / "My File.txt").touch()  # File with space
    (tmp_path / "bad@name!.txt").touch() # File with special chars

    # Test without normalization first
    response = client.post("/api/scan", json={"input_path": str(tmp_path), "normalize": False})
    assert response.status_code == 200
    files = response.json()["files"]
    filenames = [f["name"] for f in files]
    assert "My File.txt" in filenames
    assert "bad@name!.txt" in filenames

    # Test with normalization
    response = client.post("/api/scan", json={"input_path": str(tmp_path), "normalize": True})
    assert response.status_code == 200
    files = response.json()["files"]
    filenames = [f["name"] for f in files]
    
    # Check if files were renamed
    assert "My_File.txt" in filenames
    assert "badname.txt" in filenames
    assert "My File.txt" not in filenames
    assert "bad@name!.txt" not in filenames
    
    # Verify files exist on disk with new names
    assert (tmp_path / "My_File.txt").exists()
    assert (tmp_path / "badname.txt").exists()

def test_bulk_actions(client, mock_db):
    from database import DocumentItem, ItemStatus
    from unittest.mock import patch
    
    # Patch the db instance in api module
    with patch("api.db", mock_db):
        # Create items in DB
        item1 = DocumentItem(
            id="1", 
            source_path="/tmp/test1.txt", 
            status="pending",
            original_filename="test1.txt",
            extracted_text="",
            proposed_workspace="KB.Test",
            proposed_subpath="Test",
            proposed_filename="test1.txt",
            confidence=0.9
        )
        item2 = DocumentItem(
            id="2", 
            source_path="/tmp/test2.txt", 
            status="pending",
            original_filename="test2.txt",
            extracted_text="",
            proposed_workspace="KB.Test",
            proposed_subpath="Test",
            proposed_filename="test2.txt",
            confidence=0.9
        )
        mock_db.create_item(item1)
        mock_db.create_item(item2)
        
        # Test reject action
        response = client.post("/api/items/bulk-action", json={
            "action": "reject",
            "item_ids": ["1", "2"]
        })
        assert response.status_code == 200
        assert response.json()["updated"] > 0
        
        # Verify status change in DB
        items = mock_db.get_items_by_ids(["1", "2"])
        for item in items:
            assert item.status == ItemStatus.REJECTED

        # Test reject_and_move (mocking shutil and os)
        with patch("api.shutil") as mock_shutil, \
             patch("api.os") as mock_os:
            mock_os.path.dirname.return_value = "/tmp"
            mock_os.path.join.side_effect = lambda *args: "/".join(map(str, args))
            mock_os.path.basename.side_effect = lambda p: p.split("/")[-1]
            
            response = client.post("/api/items/bulk-action", json={
                "action": "reject_and_move",
                "item_ids": ["1", "2"]
            })
            assert response.status_code == 200
            mock_shutil.move.assert_called()

        # Test delete (mocking os)
        with patch("api.os") as mock_os:
            mock_os.path.exists.return_value = True
            
            response = client.post("/api/items/bulk-action", json={
                "action": "delete",
                "item_ids": ["1", "2"]
            })
            assert response.status_code == 200
            mock_os.remove.assert_called()


