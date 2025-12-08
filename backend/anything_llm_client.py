"""
AnythingLLM Client for LocalFileOrganizer integration.

This module provides a client interface to interact with AnythingLLM's API
for RAG-based document classification and workspace management.
"""
import requests
import json
import os
from typing import Dict, Any, Optional


class AnythingLLMClient:
    """
    Client for interacting with AnythingLLM's Built-in Developer API.
    
    This client handles authentication, request formatting, and response parsing
    for all AnythingLLM API interactions.
    """
    
    def __init__(self, base_url: str = "http://localhost:3001", api_key: Optional[str] = None):
        """
        Initialize the AnythingLLM client.
        
        Args:
            base_url: Base URL of the AnythingLLM instance (default: http://localhost:3001)
            api_key: API key for authentication. If None, reads from ANYTHING_LLM_API_KEY env var
        """
        self.base_url = base_url
        self.api_key = api_key or os.getenv("ANYTHING_LLM_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "AnythingLLM API key is required. Provide via constructor or "
                "ANYTHING_LLM_API_KEY environment variable."
            )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }

    def chat_with_workspace(
        self, 
        workspace_slug: str, 
        message: str, 
        mode: str = "chat"
    ) -> Optional[Dict[str, Any]]:
        """
        Send a prompt to a specific workspace to leverage RAG.
        
        Args:
            workspace_slug: The identifier for the workspace (e.g., 'librarian-core')
            message: The message/prompt to send to the workspace
            mode: Chat mode, typically 'chat' for RAG-enabled responses
        
        Returns:
            Dict containing the API response with textResponse and sources, or None on error
        """
        # Note: Endpoint structure based on standard ALLM API practices. 
        # Check /api/docs on your instance for the exact path.
        endpoint = f"{self.base_url}/api/v1/workspace/{workspace_slug}/chat"
        
        payload = {
            "message": message,
            "mode": mode  # 'chat' usually implies using RAG context
        }

        try:
            response = requests.post(
                endpoint, 
                headers=self.headers, 
                json=payload,
                timeout=30  # 30 second timeout for LLM responses
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"Timeout error chatting with workspace {workspace_slug}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error chatting with workspace {workspace_slug}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            print(f"Unexpected error chatting with workspace {workspace_slug}: {e}")
            return None

    def update_document_in_workspace(
        self, 
        workspace_slug: str, 
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a file to a workspace for embedding and RAG.
        
        This is used for the post-migration knowledge base creation workflow.
        
        Args:
            workspace_slug: The identifier for the target workspace
            file_path: Absolute path to the file to upload
        
        Returns:
            Dict containing upload status, or None on error
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        
        endpoint = f"{self.base_url}/api/v1/document/upload"
        
        # Implementation depends on exact multipart/form-data requirements in Swagger docs
        # This is a placeholder that should be verified against actual API
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f)
                }
                data = {
                    'workspaceSlug': workspace_slug
                }
                
                # Remove Content-Type header for multipart/form-data
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "accept": "application/json"
                }
                
                response = requests.post(
                    endpoint,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60  # Longer timeout for file uploads
                )
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error uploading document to AnythingLLM: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            print(f"Unexpected error updating document: {e}")
            return None
    
    def get_workspace_info(self, workspace_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a workspace.
        
        Args:
            workspace_slug: The identifier for the workspace
        
        Returns:
            Dict containing workspace metadata, or None on error
        """
        endpoint = f"{self.base_url}/api/v1/workspace/{workspace_slug}"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching workspace info: {e}")
            return None
    
    def create_workspace(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Create a new workspace.
        
        Args:
            name: Name of the workspace to create
        
        Returns:
            Dict containing new workspace info, or None on error
        """
        endpoint = f"{self.base_url}/api/v1/workspace/new"
        
        payload = {
            "name": name
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Workspace '{name}' created successfully")
            return result
        except requests.exceptions.RequestException as e:
            print(f"Error creating workspace: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None
    
    def list_workspaces(self) -> Optional[list]:
        """
        List all available workspaces.
        
        Returns:
            List of workspace objects, or None on error
        """
        endpoint = f"{self.base_url}/api/v1/workspaces"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing workspaces: {e}")
            return None
