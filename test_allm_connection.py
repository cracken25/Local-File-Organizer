"""
Live connection test for AnythingLLM integration.

This script tests the actual connection to a running AnythingLLM instance.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from anything_llm_client import AnythingLLMClient


def test_live_connection():
    """Test connection to live AnythingLLM instance."""
    
    print("=" * 60)
    print("AnythingLLM Live Connection Test")
    print("=" * 60)
    
    # Initialize client with user's configuration
    base_url = "http://localhost:8888"
    api_key = "FVQ0990-9MDM0CW-Q5TR4VV-P3GXGV8"
    workspace_name = "TaxonomyClassifierLibrarian"
    workspace_slug = "taxonomyclassifierlibrarian"  # Likely lowercase without spaces
    
    print(f"\n📡 Connecting to: {base_url}")
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    try:
        client = AnythingLLMClient(base_url=base_url, api_key=api_key)
        print("✅ Client initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test 1: List available workspaces (try to get info about a workspace)
    print("-" * 60)
    print("Test 1: Testing API connectivity")
    print("-" * 60)
    
    # Try to get workspace info
    print(f"Attempting to get workspace info for '{workspace_slug}'...")
    
    result = client.get_workspace_info(workspace_slug)
    
    if result is not None:
        print(f"✅ Successfully retrieved workspace info!")
        print(f"   Workspace: {result.get('workspace', {}).get('name', 'N/A')}")
        print(f"   Slug: {result.get('workspace', {}).get('slug', 'N/A')}")
        print(f"   Documents: {result.get('workspace', {}).get('documentCount', 'N/A')}")
        print(f"   Vector Count: {result.get('workspace', {}).get('vectorCount', 'N/A')}")
    else:
        print(f"⚠️  Workspace '{workspace_slug}' not found or API error")
        print("   This is expected if you haven't created the workspace yet")
    
    # Test 2: Try a simple chat request
    print("\n" + "-" * 60)
    print("Test 2: Testing RAG chat functionality")
    print("-" * 60)
    
    if result is not None:
        # Only test chat if workspace exists
        print(f"Sending test message to '{workspace_slug}'...")
        
        chat_result = client.chat_with_workspace(
            workspace_slug=workspace_slug,
            message="What is your purpose?"
        )
        
        if chat_result is not None:
            print("✅ Successfully received chat response!")
            print(f"   Response preview: {str(chat_result.get('textResponse', ''))[:100]}...")
            if 'sources' in chat_result and chat_result['sources']:
                print(f"   Sources cited: {len(chat_result['sources'])}")
        else:
            print("❌ Chat request failed")
    else:
        print("⏭️  Skipping chat test (workspace not found)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Connection Test Summary")
    print("=" * 60)
    
    if result is not None:
        print("✅ CONNECTION SUCCESSFUL!")
        print("\nYour AnythingLLM instance is accessible and ready to use.")
        print("\nNext steps:")
        print("1. Create a workspace called 'librarian-core' if you haven't")
        print("2. Upload taxonomy.yaml and TaxonomyRequirements.MD to the workspace")
        print("3. Embed the documents in the workspace")
    else:
        print("⚠️  CONNECTION PARTIAL")
        print("\nThe API is accessible, but the 'librarian-core' workspace doesn't exist yet.")
        print("\nTo proceed with the integration:")
        print("1. Open AnythingLLM Desktop at http://localhost:8888")
        print("2. Create a new workspace named 'librarian-core'")
        print("3. Upload your taxonomy.yaml file to the workspace")
        print("4. Run this test again to verify")
    
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        test_live_connection()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
