import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import MagicMock

# Mock dependencies that might not be installed or require heavy setup
sys.modules['nexaai'] = MagicMock()
sys.modules['nexaai.nexa_sdk'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['fitz'] = MagicMock()
sys.modules['docx'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['pptx'] = MagicMock()

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app
from database import Database

# Import AnythingLLM fixtures
from tests.fixtures.allm_fixtures import (
    sample_allm_responses,
    mock_allm_api_response,
    mock_allm_workspace,
    mock_allm_client,
    sample_taxonomy_data,
    mock_requests_post,
    allm_test_env_vars,
    sample_classification_request
)

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    
    # Monkeypatch the global db instance in api module
    import api
    api.db = db
    
    return db

@pytest.fixture
def sample_file_path(tmp_path):
    """Create a temporary directory with sample files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    (test_dir / "test.txt").write_text("Sample text content")
    return str(test_dir)
