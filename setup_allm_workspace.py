"""
Automated setup script for AnythingLLM workspace.

This script:
1. Creates the 'librarian-core' workspace
2. Uploads taxonomy.yaml and TaxonomyRequirements.MD
3. Triggers document embedding
"""
import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from anything_llm_client import AnythingLLMClient


def setup_librarian_workspace():
    """Set up the librarian-core workspace with taxonomy documents."""
    
    print("=" * 70)
    print("AnythingLLM Workspace Setup - librarian-core")
    print("=" * 70)
    
    # Configuration
    base_url = "http://localhost:8888"
    api_key = "FVQ0990-9MDM0CW-Q5TR4VV-P3GXGV8"
    workspace_name = "Librarian Core"
    workspace_slug = "librarian-core"
    
    # Files to upload
    taxonomy_file = os.path.join(os.path.dirname(__file__), "backend", "taxonomy.yaml")
    requirements_file = os.path.join(os.path.dirname(__file__), "TaxonomyRequirements.MD")
    
    # Initialize client
    print(f"\n📡 Connecting to AnythingLLM at {base_url}...")
    client = AnythingLLMClient(base_url=base_url, api_key=api_key)
    print("✅ Client initialized\n")
    
    # Step 1: Check if workspace already exists
    print("-" * 70)
    print("Step 1: Checking for existing workspace")
    print("-" * 70)
    
    existing = client.get_workspace_info(workspace_slug)
    
    if existing and 'workspace' in existing:
        print(f"✅ Workspace '{workspace_slug}' already exists")
        print(f"   Name: {existing['workspace'].get('name', 'N/A')}")
        print(f"   Documents: {existing['workspace'].get('documentCount', 0)}")
    else:
        # Step 2: Create workspace
        print(f"📝 Creating new workspace '{workspace_name}'...")
        
        result = client.create_workspace(workspace_name)
        
        if result and 'workspace' in result:
            print(f"✅ Workspace created successfully!")
            print(f"   Slug: {result['workspace'].get('slug', 'N/A')}")
            time.sleep(2)  # Give AnythingLLM time to initialize workspace
        else:
            print("❌ Failed to create workspace")
            return False
    
    # Step 3: Upload taxonomy.yaml
    print("\n" + "-" * 70)
    print("Step 2: Uploading taxonomy.yaml")
    print("-" * 70)
    
    if os.path.exists(taxonomy_file):
        print(f"📤 Uploading {taxonomy_file}...")
        
        upload_result = client.update_document_in_workspace(
            workspace_slug=workspace_slug,
            file_path=taxonomy_file
        )
        
        if upload_result:
            print("✅ taxonomy.yaml uploaded successfully")
        else:
            print("⚠️  Failed to upload taxonomy.yaml")
    else:
        print(f"❌ File not found: {taxonomy_file}")
    
    # Step 4: Upload TaxonomyRequirements.MD (if it exists)
    print("\n" + "-" * 70)
    print("Step 3: Uploading TaxonomyRequirements.MD")
    print("-" * 70)
    
    if os.path.exists(requirements_file):
        print(f"📤 Uploading {requirements_file}...")
        
        upload_result = client.update_document_in_workspace(
            workspace_slug=workspace_slug,
            file_path=requirements_file
        )
        
        if upload_result:
            print("✅ TaxonomyRequirements.MD uploaded successfully")
        else:
            print("⚠️  Failed to upload TaxonomyRequirements.MD")
    else:
        print(f"ℹ️  File not found: {requirements_file} (optional)")
    
    # Step 5: Verify workspace state
    print("\n" + "-" * 70)
    print("Step 4: Verifying workspace setup")
    print("-" * 70)
    
    time.sleep(3)  # Give time for embedding to start
    
    workspace_info = client.get_workspace_info(workspace_slug)
    
    if workspace_info and 'workspace' in workspace_info:
        ws = workspace_info['workspace']
        print(f"✅ Workspace verification:")
        print(f"   Name: {ws.get('name', 'N/A')}")
        print(f"   Slug: {ws.get('slug', 'N/A')}")
        print(f"   Documents: {ws.get('documentCount', 0)}")
        print(f"   Vectors: {ws.get('vectorCount', 0)}")
        
        if ws.get('documentCount', 0) > 0:
            print("\n🎉 Setup complete!")
            print("\nThe workspace is ready for RAG-based classification.")
            print("Documents are being embedded in the background.")
        else:
            print("\n⚠️  Workspace created but no documents uploaded")
            print("You may need to manually upload files via the AnythingLLM UI")
    else:
        print("⚠️  Could not verify workspace state")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("1. Wait a few minutes for document embedding to complete")
    print("2. Run test_allm_connection.py to verify RAG functionality")
    print("3. Start using the workspace for classification")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        setup_librarian_workspace()
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
