"""
Unit tests for AnythingLLMClient.

Tests the core functionality of the AnythingLLM API client including:
- Initialization and configuration
- RAG-enabled chat with workspaces  
- Document upload and embedding
- Error handling and edge cases
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import requests
import os


# Import the client (will be available after we create it)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from anything_llm_client import AnythingLLMClient


class TestAnythingLLMClientInit:
    """Test client initialization and configuration."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key provided directly."""
        client = AnythingLLMClient(
            base_url="http://localhost:3001",
            api_key="test_key_12345"
        )
        
        assert client.base_url == "http://localhost:3001"
        assert client.api_key == "test_key_12345"
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test_key_12345"
    
    def test_init_with_env_var(self, allm_test_env_vars):
        """Test initialization with API key from environment variable."""
        client = AnythingLLMClient()
        
        assert client.api_key == "test_api_key_12345"
        assert client.base_url == "http://localhost:3001"
    
    def test_init_without_api_key(self, monkeypatch):
        """Test that initialization fails without API key."""
        monkeypatch.delenv("ANYTHING_LLM_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="AnythingLLM API key is required"):
            AnythingLLMClient()
    
    def test_init_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = AnythingLLMClient(
            base_url="http://custom:5000",
            api_key="test_key"
        )
        
        assert client.base_url == "http://custom:5000"


class TestChatWithWorkspace:
    """Test RAG-enabled chat functionality."""
    
    @patch('requests.post')
    def test_successful_chat(self, mock_post, mock_allm_api_response):
        """Test successful chat request with valid response."""
        # Setup mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_allm_api_response('successful_classification')
        mock_post.return_value = mock_resp
        
        # Create client and make request
        client = AnythingLLMClient(api_key="test_key")
        result = client.chat_with_workspace(
            workspace_slug="librarian-core",
            message="Classify this document: test.txt"
        )
        
        # Assertions
        assert result is not None
        assert "textResponse" in result
        mock_post.assert_called_once()
        
        # Verify request structure
        call_args = mock_post.call_args
        assert "librarian-core" in call_args[0][0]
        assert call_args[1]["json"]["message"] == "Classify this document: test.txt"
        assert call_args[1]["json"]["mode"] == "chat"
    
    @patch('requests.post')
    def test_chat_with_custom_mode(self, mock_post):
        """Test chat with custom mode parameter."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"textResponse": "test"}
        mock_post.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="test_key")
        client.chat_with_workspace(
            workspace_slug="test-workspace",
            message="Test message",
            mode="query"
        )
        
        call_args = mock_post.call_args
        assert call_args[1]["json"]["mode"] == "query"
    
    @patch('requests.post')
    def test_chat_network_error(self, mock_post):
        """Test graceful handling of network errors."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")
        
        client = AnythingLLMClient(api_key="test_key")
        result = client.chat_with_workspace(
            workspace_slug="librarian-core",
            message="Test"
        )
        
        assert result is None
    
    @patch('requests.post')
    def test_chat_timeout(self, mock_post):
        """Test timeout handling."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        client = AnythingLLMClient(api_key="test_key")
        result = client.chat_with_workspace(
            workspace_slug="librarian-core",
            message="Test"
        )
        
        assert result is None
    
    @patch('requests.post')
    def test_chat_401_unauthorized(self, mock_post, mock_allm_api_response):
        """Test handling of 401 Unauthorized error."""
        mock_resp = Mock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        mock_post.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="invalid_key")
        result = client.chat_with_workspace(
            workspace_slug="librarian-core",
            message="Test"
        )
        
        assert result is None
    
    @patch('requests.post')
    def test_chat_500_server_error(self, mock_post):
        """Test handling of 500 Internal Server Error."""
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        mock_post.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="test_key")
        result = client.chat_with_workspace(
            workspace_slug="librarian-core",
            message="Test"
        )
        
        assert result is None
    
    @patch('requests.post')
    def test_chat_with_rag_citations(self, mock_post, mock_allm_api_response):
        """Test that RAG responses include source citations."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_allm_api_response('rag_with_citations')
        mock_post.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="test_key")
        result = client.chat_with_workspace(
            workspace_slug="librarian-core",
            message="Classify tax document"
        )
        
        assert result is not None
        assert "sources" in result
        assert len(result["sources"]) > 0
        assert "taxonomy.yaml" in result["sources"][0]["title"]


class TestUpdateDocumentInWorkspace:
    """Test document upload functionality."""
    
    @patch('requests.post')
    def test_successful_upload(self, mock_post, tmp_path, mock_allm_api_response):
        """Test successful document upload."""
        # Create a test file
        test_file = tmp_path / "test_doc.txt"
        test_file.write_text("Test content")
        
        # Setup mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_allm_api_response('document_upload_success')
        mock_post.return_value = mock_resp
        
        # Upload document
        client = AnythingLLMClient(api_key="test_key")
        result = client.update_document_in_workspace(
            workspace_slug="test-workspace",
            file_path=str(test_file)
        )
        
        # Assertions
        assert result is not None
        assert result.get("success") is True
        mock_post.assert_called_once()
        
        # Verify multipart form-data was used
        call_args = mock_post.call_args
        assert "files" in call_args[1]
    
    def test_upload_nonexistent_file(self):
        """Test upload with file that doesn't exist."""
        client = AnythingLLMClient(api_key="test_key")
        result = client.update_document_in_workspace(
            workspace_slug="test-workspace",
            file_path="/nonexistent/file.txt"
        )
        
        assert result is None
    
    @patch('requests.post')
    def test_upload_network_error(self, mock_post, tmp_path):
        """Test upload with network error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        client = AnythingLLMClient(api_key="test_key")
        result = client.update_document_in_workspace(
            workspace_slug="test-workspace",
            file_path=str(test_file)
        )
        
        assert result is None
    
    @patch('requests.post')
    def test_upload_with_longer_timeout(self, mock_post, tmp_path):
        """Test that upload uses longer timeout than chat."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        mock_post.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="test_key")
        client.update_document_in_workspace(
            workspace_slug="test-workspace",
            file_path=str(test_file)
        )
        
        # Verify timeout is set to 60 seconds for uploads
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 60


class TestGetWorkspaceInfo:
    """Test workspace information retrieval."""
    
    @patch('requests.get')
    def test_successful_get_workspace_info(self, mock_get, mock_allm_workspace):
        """Test successful workspace info retrieval."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_allm_workspace
        mock_get.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="test_key")
        result = client.get_workspace_info("librarian-core")
        
        assert result is not None
        assert "workspace" in result
        assert result["workspace"]["slug"] == "librarian-core"
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_workspace_info_not_found(self, mock_get):
        """Test retrieval of non-existent workspace."""
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_resp.text = "Workspace not found"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        mock_get.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="test_key")
        result = client.get_workspace_info("nonexistent-workspace")
        
        assert result is None


class TestHeaderConfiguration:
    """Test HTTP header configuration."""
    
    def test_authorization_header_format(self):
        """Test that Authorization header uses Bearer token format."""
        client = AnythingLLMClient(api_key="test_key_12345")
        
        assert client.headers["Authorization"] == "Bearer test_key_12345"
    
    def test_content_type_header(self):
        """Test that Content-Type header is set correctly."""
        client = AnythingLLMClient(api_key="test_key")
        
        assert client.headers["Content-Type"] == "application/json"
    
    def test_accept_header(self):
        """Test that Accept header is set correctly."""
        client = AnythingLLMClient(api_key="test_key")
        
        assert client.headers["accept"] == "application/json"


# Pytest markers for categorizing tests
pytestmark = [
    pytest.mark.unit,
    pytest.mark.allm_client
]
