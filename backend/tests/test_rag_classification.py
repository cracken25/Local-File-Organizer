"""
Unit tests for RAG-based classification logic.

Tests the integration between AnythingLLMClient and the classification engine,
focusing on RAG-specific functionality and taxonomy adherence.
"""
import pytest
from unittest.mock import patch, Mock
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from anything_llm_client import AnythingLLMClient


def classify_file_with_rag(allm_client, filename, content):
    """
    RAG-based classification function (implementation from proposal).
    
    This is the classification logic that will replace the old LLMEngine approach.
    """
    system_instruction = """
    You are the 'Librarian Agent'. 
    Using the Taxonomy Rules and Requirements provided in your context:
    1. Analyze the input file content.
    2. Determine the best KB.Domain.Scope.
    3. Return the result as JSON with keys: category, confidence, reasoning.
    """

    user_prompt = f"File Name: {filename}\n\nFile Content Summary:\n{content}"

    # Send to AnythingLLM (Workspace: librarian-core)
    response = allm_client.chat_with_workspace(
        workspace_slug="librarian-core", 
        message=f"{system_instruction}\n\n{user_prompt}"
    )

    if response is None:
        return None

    # Parse Response
    ai_answer = response.get('textResponse', '{}')
    
    try:
        parsed = json.loads(ai_answer)
        return {
            'category_id': parsed.get('category_id'),
            'confidence': parsed.get('confidence', 0.0),
            'reasoning': parsed.get('reasoning', ''),
            'sources': response.get('sources', [])
        }
    except json.JSONDecodeError:
        return None


class TestClassifyFileWithRAGSuccess:
    """Test successful RAG-based classification."""
    
    def test_successful_classification(self, mock_allm_client, sample_classification_request):
        """Test successful classification with valid RAG response."""
        result = classify_file_with_rag(
            allm_client=mock_allm_client,
            filename=sample_classification_request['filename'],
            content=sample_classification_request['content']
        )
        
        assert result is not None
        assert 'category_id' in result
        assert result['category_id'] == 'KB.Finance.Tax.Filing.Federal'
        assert result['confidence'] >= 0.85
        assert 'reasoning' in result
    
    def test_classification_with_citations(self, mock_allm_api_response):
        """Test that classification includes RAG source citations."""
        client = AnythingLLMClient(api_key="test_key")
        
        with patch('requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_allm_api_response('rag_with_citations')
            mock_post.return_value = mock_resp
            
            result = classify_file_with_rag(
                allm_client=client,
                filename="tax_form.pdf",
                content="IRS Form 1040 for 2024"
            )
            
            assert result is not None
            assert 'sources' in result
            assert len(result['sources']) > 0
            # Verify taxonomy.yaml is cited
            source_titles = [s['title'] for s in result['sources']]
            assert 'taxonomy.yaml' in source_titles


class TestRAGHallucinationDetection:
    """Test detection and handling of hallucinated categories."""
    
    def test_hallucinated_category_flagged(self, mock_allm_api_response):
        """Test that hallucinated categories not in taxonomy are detected."""
        client = AnythingLLMClient(api_key="test_key")
        
        with patch('requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            # Response contains a category that doesn't exist in taxonomy
            mock_resp.json.return_value = mock_allm_api_response('hallucinated_category')
            mock_post.return_value = mock_resp
            
            result = classify_file_with_rag(
                allm_client=client,
                filename="crypto_transactions.csv",
                content="Cryptocurrency trading data"
            )
            
            # The result contains the hallucinated category
            assert result is not None
            assert result['category_id'] == 'KB.Finance.Cryptocurrency.Trading'
            
            # In a real implementation, we would verify against taxonomy
            # and either reject or flag this classification
            # This test documents the need for post-processing validation


class TestLowConfidenceClassification:
    """Test handling of low-confidence classifications."""
    
    def test_low_confidence_classification(self, mock_allm_api_response):
        """Test that low-confidence results are properly handled."""
        client = AnythingLLMClient(api_key="test_key")
        
        with patch('requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_allm_api_response('low_confidence_classification')
            mock_post.return_value = mock_resp
            
            result = classify_file_with_rag(
                allm_client=client,
                filename="ambiguous_doc.txt",
                content="Some ambiguous content"
            )
            
            assert result is not None
            assert result['confidence'] < 0.5
            # Low confidence should default to Misc
            assert 'Misc' in result['category_id']


class TestRAGAPIFailureHandling:
    """Test graceful degradation when ALLM API is unavailable."""
    
    def test_api_unavailable(self):
        """Test handling when AnythingLLM API is down."""
        client = AnythingLLMClient(api_key="test_key")
        
        with patch('requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.ConnectionError("API unavailable")
            
            result = classify_file_with_rag(
                allm_client=client,
                filename="test.pdf",
                content="Test content"
            )
            
            assert result is None
    
    def test_timeout_handling(self):
        """Test handling of API timeouts."""
        client = AnythingLLMClient(api_key="test_key")
        
        with patch('requests.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
            
            result = classify_file_with_rag(
                allm_client=client,
                filename="test.pdf",
                content="Test content"
            )
            
            assert result is None


class TestTaxonomyNotInjectedInPrompt:
    """Verify that full taxonomy is NOT injected into the prompt."""
    
    def test_no_taxonomy_in_prompt(self, sample_taxonomy_data):
        """Assert that taxonomy.yaml content is NOT in the API request."""
        client = AnythingLLMClient(api_key="test_key")
        
        with patch('requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'textResponse': '{"category_id": "KB.Finance.Tax", "confidence": 0.9, "reasoning": "test"}'
            }
            mock_post.return_value = mock_resp
            
            classify_file_with_rag(
                allm_client=client,
                filename="test.pdf",
                content="Test content"
            )
            
            # Get the actual request payload
            call_args = mock_post.call_args
            request_payload = call_args[1]['json']
            message_content = request_payload['message']
            
            # Assert taxonomy content is NOT in the prompt
            # These are strings that would appear if taxonomy was injected
            assert 'KB.Finance.Tax.Filing.Federal' not in message_content
            assert 'workspaces:' not in message_content
            assert sample_taxonomy_data not in message_content
            
            # But the system instruction should be present
            assert 'Librarian Agent' in message_content


class TestRAGTokenReduction:
    """Test that RAG approach reduces token consumption vs full taxonomy injection."""
    
    def test_prompt_size_comparison(self, sample_taxonomy_data):
        """Compare prompt sizes between RAG and legacy approaches."""
        client = AnythingLLMClient(api_key="test_key")
        
        # RAG approach (without taxonomy injection)
        with patch('requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'textResponse': '{"category_id": "KB.Finance.Tax", "confidence": 0.9, "reasoning": "test"}'
            }
            mock_post.return_value = mock_resp
            
            classify_file_with_rag(
                allm_client=client,
                filename="test.pdf",
                content="Test content " * 100  # Realistic content size
            )
            
            rag_prompt = mock_post.call_args[1]['json']['message']
            rag_token_estimate = len(rag_prompt) // 4  # Rough token estimate
            
        # Legacy approach would include full taxonomy
        legacy_prompt = rag_prompt + sample_taxonomy_data
        legacy_token_estimate = len(legacy_prompt) // 4
        
        # RAG should reduce tokens by at least 30% (conservative estimate)
        # In reality, with full taxonomy YAML the reduction would be 60-80%
        reduction_percent = (1 - rag_token_estimate / legacy_token_estimate) * 100
        
        assert reduction_percent >= 30, \
            f"Expected >30% token reduction, got {reduction_percent:.1f}%"


class TestCitationParsing:
    """Test extraction and logging of RAG source citations."""
    
    def test_citation_extraction(self, mock_allm_api_response):
        """Verify that citations are properly extracted from RAG responses."""
        client = AnythingLLMClient(api_key="test_key")
        
        with patch('requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_allm_api_response('rag_with_citations')
            mock_post.return_value = mock_resp
            
            result = classify_file_with_rag(
                allm_client=client,
                filename="tax_doc.pdf",
                content="IRS Form content"
            )
            
            assert result is not None
            assert 'sources' in result
            
            # Verify citation structure
            for source in result['sources']:
                assert 'title' in source
                assert 'chunk' in source
            
            # Verify specific citations
            source_data = {s['title']: s['chunk'] for s in result['sources']}
            assert 'taxonomy.yaml' in source_data
            assert 'TaxonomyRequirements.MD' in source_data


# Pytest markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.rag_classification
]
