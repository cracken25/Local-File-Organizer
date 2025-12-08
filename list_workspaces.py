"""Quick script to list all workspaces and find the correct slug."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from anything_llm_client import AnythingLLMClient

client = AnythingLLMClient(
    base_url="http://localhost:8888",
    api_key="FVQ0990-9MDM0CW-Q5TR4VV-P3GXGV8"
)

print("Attempting to list all workspaces...")
workspaces = client.list_workspaces()

if workspaces:
    print(f"\n✅ Found {len(workspaces)} workspace(s):\n")
    for ws in workspaces:
        print(f"  Name: {ws.get('name', 'N/A')}")
        print(f"  Slug: {ws.get('slug', 'N/A')}")
        print(f"  ---")
else:
    print("⚠️  No workspaces found or API error")
    print("\nTrying direct API call...")
    
    import requests
    try:
        response = requests.get(
            "http://localhost:8888/api/v1/workspaces",
            headers={
                "Authorization": f"Bearer FVQ0990-9MDM0CW-Q5TR4VV-P3GXGV8",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
