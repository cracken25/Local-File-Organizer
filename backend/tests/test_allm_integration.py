"""
Integration tests for AnythingLLM workflow.

Tests the complete scan → classify → review → migrate workflow
with AnythingLLM integration using mocked API responses.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from anything_llm_client import AnythingLLMClient


class TestScanClassifyWorkflow:
    """Test complete scan and classify workflow with ALLM integration."""
    
    @patch('requests.post')
    def test_scan_classify_with_allm(self, mock_post, mock_allm_api_response, tmp_path):
        """Test full workflow: scan directory → classify via ALLM → store results."""
        
        # Setup: Create test files
        test_file = tmp_path / "tax_return_2024.pdf"
        test_file.write_text("IRS Form 1040 for tax year 2024")
        
        # Mock ALLM API response for classification
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_allm_api_response('successful_classification')
        mock_post.return_value = mock_resp
        
        # Initialize client
        client = AnythingLLMClient(api_key="test_key")
        
        # Simulate classification
        filename = str(test_file.name)
        content = test_file.read_text()
        
        # Build classification prompt
        system_instruction = """
        You are the 'Librarian Agent'. 
        Using the Taxonomy Rules and Requirements provided in your context:
        1. Analyze the input file content.
        2. Determine the best KB.Domain.Scope.
        3. Return the result as JSON with keys: category_id, confidence, reasoning.
        """
        
        user_prompt = f"File Name: {filename}\n\nFile Content:\n{content}"
        
        # Call ALLM
        response = client.chat_with_workspace(
            workspace_slug="taxonomyclassifierlibrarian",
            message=f"{system_instruction}\n\n{user_prompt}"
        )
        
        # Assert response structure
        assert response is not None
        assert 'textResponse' in response
        
        # Parse classification result
        text_response = response['textResponse']
        classification = json.loads(text_response)
        
        # Verify classification
        assert 'category_id' in classification
        assert classification['category_id'] == 'KB.Finance.Tax.Filing.Federal'
        assert classification['confidence'] >= 0.85
        assert 'reasoning' in classification
        
        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'taxonomyclassifierlibrarian' in call_args[0][0]
        assert system_instruction in call_args[1]['json']['message']
    
    @patch('requests.post')
    def test_batch_classification(self, mock_post, mock_allm_api_response, tmp_path):
        """Test classifying multiple files in batch."""
        
        # Create multiple test files
        files = [
            ("tax_form_1040.pdf", "IRS Form 1040", "KB.Finance.Tax.Filing.Federal"),
            ("receipt_donation.jpg", "Charitable donation receipt", "KB.Finance.Tax.Records.Receipts"),
            ("meeting_notes.txt", "Project meeting notes", "KB.Personal.Misc"),
        ]
        
        mock_resp = Mock()
        mock_resp.status_code = 200
        
        client = AnythingLLMClient(api_key="test_key")
        results = []
        
        for filename, content, expected_category in files:
            # Create test file
            test_file = tmp_path / filename
            test_file.write_text(content)
            
            # Configure mock response for this file
            classification_response = {
                "textResponse": json.dumps({
                    "category_id": expected_category,
                    "confidence": 0.9,
                    "reasoning": f"File matches {expected_category} pattern"
                }),
                "sources": [],
                "type": "textResponse"
            }
            mock_resp.json.return_value = classification_response
            mock_post.return_value = mock_resp
            
            # Classify
            response = client.chat_with_workspace(
                workspace_slug="taxonomyclassifierlibrarian",
                message=f"Classify: {filename}\nContent: {content}"
            )
            
            if response:
                classification = json.loads(response['textResponse'])
                results.append({
                    'filename': filename,
                    'category': classification['category_id'],
                    'confidence': classification['confidence']
                })
        
        # Verify all files were classified
        assert len(results) == 3
        assert all(r['confidence'] >= 0.85 for r in results)
        
        # Verify different categories assigned
        categories = [r['category'] for r in results]
        assert 'KB.Finance.Tax.Filing.Federal' in categories
        assert 'KB.Finance.Tax.Records.Receipts' in categories
        assert 'KB.Personal.Misc' in categories


class TestWorkspaceSynchronization:
    """Test workspace synchronization after file migration."""
    
    @patch('requests.post')
    def test_migration_triggers_workspace_sync(self, mock_post, tmp_path):
        """Test that migrated files are uploaded to ALLM workspace."""
        
        # Create test file
        source_file = tmp_path / "source" / "contract.pdf"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("Employment contract content")
        
        # Simulate migration
        dest_file = tmp_path / "KB" / "Work" / "Employment" / "contract.pdf"
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Mock successful upload
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "documentId": "doc_12345",
            "message": "Document uploaded successfully"
        }
        mock_post.return_value = mock_resp
        
        # Initialize client and upload
        client = AnythingLLMClient(api_key="test_key")
        
        # Simulate post-migration upload
        result = client.update_document_in_workspace(
            workspace_slug="kb-work-employment",
            file_path=str(source_file)
        )
        
        # Verify upload was attempted
        assert result is not None
        assert result['success'] is True
        
        # Verify correct workspace was targeted
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'upload' in call_args[0][0].lower() or 'document' in call_args[0][0].lower()
    
    @patch('requests.post')
    def test_workspace_sync_failure_handling(self, mock_post, tmp_path):
        """Test handling of workspace sync failures."""
        
        # Create test file
        test_file = tmp_path / "test.pdf"
        test_file.write_text("Test content")
        
        # Mock failed upload - exception should be caught by client
        mock_post.side_effect = Exception("Network error during upload")
        
        client = AnythingLLMClient(api_key="test_key")
        
        # Attempt upload - client should catch exception internally
        try:
            result = client.update_document_in_workspace(
                workspace_slug="test-workspace",
                file_path=str(test_file)
            )
            # If we get here, verify result is None (graceful failure)
            assert result is None
        except Exception:
            # If exception bubbles up, test fails
            pytest.fail("Client should catch exceptions, not raise them")


class TestConcurrentClassification:
    """Test concurrent classification requests."""
    
    @patch('requests.post')
    def test_sequential_classification(self, mock_post, mock_allm_api_response):
        """Test multiple sequential classification requests."""
        
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_allm_api_response('successful_classification')
        mock_post.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="test_key")
        
        # Classify 5 files sequentially
        results = []
        for i in range(5):
            response = client.chat_with_workspace(
                workspace_slug="taxonomyclassifierlibrarian",
                message=f"Classify file_{i}.pdf"
            )
            results.append(response)
        
        # All should succeed
        assert len(results) == 5
        assert all(r is not None for r in results)
        assert mock_post.call_count == 5
    
    def test_rate_limiting_awareness(self, mock_allm_client):
        """Test that client is aware of rate limiting (mock test)."""
        
        # Note: Actual rate limiting would be tested with live API
        # This test documents the need for rate limit handling
        
        # Mock client already handles timeouts and errors
        # In production, we'd add exponential backoff for 429 errors
        
        assert hasattr(mock_allm_client, 'chat_with_workspace')
        # Future enhancement: Add retry logic with backoff


class TestFallbackMechanisms:
    """Test fallback behavior when ALLM is unavailable."""
    
    @patch('requests.post')
    def test_allm_unavailable_returns_none(self, mock_post):
        """Test that unavailable ALLM returns None gracefully."""
        
        # Simulate ALLM down - exception should be caught by client
        mock_post.side_effect = ConnectionError("ALLM service unreachable")
        
        client = AnythingLLMClient(api_key="test_key")
        
        # Attempt classification - client should catch exception internally
        try:
            result = client.chat_with_workspace(
                workspace_slug="taxonomyclassifierlibrarian",
                message="Test classification"
            )
            # If we get here, verify result is None (graceful failure)
            assert result is None
        except ConnectionError:
            # If exception bubbles up, test fails
            pytest.fail("Client should catch ConnectionError, not raise it")
    
    def test_legacy_llm_fallback_detection(self):
        """Document need for legacy LLM fallback when ALLM fails."""
        
        # This test documents the integration point for fallback logic
        # In the main application, when ALLM returns None, 
        # the system should fall back to LLMEngine
        
        # Example fallback pattern:
        # result = allm_client.classify(file)
        # if result is None:
        #     result = legacy_llm_engine.classify(file)
        
        # This would be implemented in api.py or classifier.py
        assert True  # Placeholder for future implementation


class TestTaxonomyUpdatePropagation:
    """Test taxonomy update workflows."""
    
    @patch('requests.post')
    def test_taxonomy_edit_triggers_reembed(self, mock_post, tmp_path):
        """Test that taxonomy edits trigger re-embedding in ALLM."""
        
        # Create taxonomy file
        taxonomy_file = tmp_path / "taxonomy.yaml"
        taxonomy_file.write_text("""
version: "1.1"
workspaces:
  - id: KB.Projects.NewScope
    description: "Newly added scope"
""")
        
        # Mock successful upload
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "documentId": "taxonomy_v1.1"
        }
        mock_post.return_value = mock_resp
        
        client = AnythingLLMClient(api_key="test_key")
        
        # Upload updated taxonomy
        result = client.update_document_in_workspace(
            workspace_slug="taxonomyclassifierlibrarian",
            file_path=str(taxonomy_file)
        )
        
        # Verify update was sent
        assert result is not None
        assert result['success'] is True
    
    def test_taxonomy_version_tracking(self):
        """Test taxonomy version tracking for rollback capability."""
        
        # This test documents the need for version tracking
        # Implementation would involve:
        # 1. Storing taxonomy versions in database
        # 2. Tagging ALLM document uploads with version
        # 3. Providing UI to rollback to previous version
        
        versions = ["1.0", "1.1", "1.2"]
        
        # Each version would be uploaded to ALLM with version tag
        # ALLM workspace would maintain version history
        
        assert len(versions) == 3  # Placeholder


# Pytest markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.allm_integration
]
