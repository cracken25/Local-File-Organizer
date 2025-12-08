"""
Pytest fixtures for AnythingLLM API mocking and test data.
"""
import pytest
import json
import os
from unittest.mock import MagicMock, Mock
from pathlib import Path


@pytest.fixture
def sample_allm_responses():
    """Load sample AnythingLLM API responses from JSON file."""
    fixtures_dir = Path(__file__).parent
    responses_file = fixtures_dir / "sample_allm_responses.json"
    
    with open(responses_file, 'r') as f:
        return json.load(f)


@pytest.fixture
def mock_allm_api_response(sample_allm_responses):
    """
    Factory fixture for creating realistic AnythingLLM API responses.
    
    Usage:
        def test_something(mock_allm_api_response):
            response = mock_allm_api_response('successful_classification')
    """
    def _get_response(response_type='successful_classification'):
        return sample_allm_responses.get(response_type, {})
    
    return _get_response


@pytest.fixture
def mock_allm_workspace():
    """
    Fixture providing a mocked AnythingLLM workspace state.
    """
    return {
        'workspace': {
            'id': 1,
            'name': 'Librarian Core',
            'slug': 'librarian-core',
            'vectorCount': 1250,
            'documentCount': 3,
            'documents': [
                {
                    'id': 'doc_tax_001',
                    'name': 'taxonomy.yaml',
                    'status': 'embedded',
                    'vectorCount': 800
                },
                {
                    'id': 'doc_tax_002',
                    'name': 'TaxonomyRequirements.MD',
                    'status': 'embedded',
                    'vectorCount': 450
                }
            ],
            'createdAt': '2024-01-01T00:00:00Z',
            'lastUpdated': '2024-12-07T00:00:00Z'
        }
    }


@pytest.fixture
def mock_allm_client(mock_allm_api_response):
    """
    Fixture providing a fully mocked AnythingLLMClient instance.
    
    This mock simulates successful API communication without requiring
    a live AnythingLLM instance.
    """
    from unittest.mock import patch
    
    client_mock = MagicMock()
    
    # Mock successful chat response
    def mock_chat_with_workspace(workspace_slug, message, mode="chat"):
        return mock_allm_api_response('successful_classification')
    
    # Mock successful document upload
    def mock_update_document(workspace_slug, file_path):
        return mock_allm_api_response('document_upload_success')
    
    client_mock.chat_with_workspace = Mock(side_effect=mock_chat_with_workspace)
    client_mock.update_document_in_workspace = Mock(side_effect=mock_update_document)
    client_mock.base_url = "http://localhost:3001"
    client_mock.api_key = "test_api_key_12345"
    
    return client_mock


@pytest.fixture
def sample_taxonomy_data():
    """
    Fixture providing sample taxonomy YAML content for testing RAG retrieval.
    """
    return """
workspaces:
  - id: KB.Finance
    description: Financial documents and records
    scopes:
      - id: KB.Finance.Tax
        description: Tax-related documents
        subscopes:
          - id: KB.Finance.Tax.Filing
            description: Tax filing documents
            subscopes:
              - id: KB.Finance.Tax.Filing.Federal
                description: Federal tax returns and IRS forms
                quality_tests:
                  - "Does the document contain IRS forms?"
              - id: KB.Finance.Tax.Filing.State
                description: State tax returns and forms
  - id: KB.Personal
    description: Personal documents
    scopes:
      - id: KB.Personal.Identity
        description: Identity documents (passports, licenses)
      - id: KB.Personal.Misc
        description: Miscellaneous personal files that don't fit other categories
"""


@pytest.fixture
def mock_requests_post(mock_allm_api_response):
    """
    Fixture for mocking requests.post calls to AnythingLLM API.
    
    Usage:
        with mock_requests_post as mock_post:
            # Make API calls
            # Then verify: mock_post.assert_called_with(...)
    """
    from unittest.mock import patch
    
    def create_mock_response(status_code=200, json_data=None):
        mock_resp = Mock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data or mock_allm_api_response('successful_classification')
        mock_resp.raise_for_status = Mock()
        return mock_resp
    
    with patch('requests.post') as mock_post:
        mock_post.return_value = create_mock_response()
        yield mock_post


@pytest.fixture
def allm_test_env_vars(monkeypatch):
    """
    Fixture to set AnythingLLM environment variables for testing.
    """
    monkeypatch.setenv("ANYTHING_LLM_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("ANYTHING_LLM_URL", "http://localhost:3001")
    monkeypatch.setenv("ALLM_SKIP_LIVE_TESTS", "true")
    
    return {
        "api_key": "test_api_key_12345",
        "base_url": "http://localhost:3001"
    }


@pytest.fixture
def sample_classification_request():
    """
    Fixture providing a sample file classification request.
    """
    return {
        "filename": "2024_tax_return_draft.pdf",
        "content": "IRS Form 1040 - U.S. Individual Income Tax Return for fiscal year 2024. "
                  "Taxpayer information, income statements, deductions, and tax calculations. "
                  "Total tax liability: $12,500. Refund due: $1,200.",
        "expected_category": "KB.Finance.Tax.Filing.Federal",
        "expected_confidence_min": 0.85
    }
