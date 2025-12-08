"""Test direct chat endpoint"""
import requests

base_url = "http://localhost:8888"
api_key = "FVQ0990-9MDM0CW-Q5TR4VV-P3GXGV8"

# Try different possible workspace slugs
possible_slugs = [
    "taxonomyclassifierlibrarian",
    "TaxonomyClassifierLibrarian",
    "taxonomy-classifier-librarian",
    "default",
    "my-workspace"
]

for slug in possible_slugs:
    print(f"\nTrying workspace: {slug}")
    try:
        response = requests.post(
            f"{base_url}/api/v1/workspace/{slug}/chat",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "message": "Hello, what taxonomy categories do you know?",
                "mode": "chat"
            },
            timeout=30
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ SUCCESS! Found working slug: {slug}")
            print(f"  Response preview: {response.text[:200]}")
            break
        else:
            print(f"  Response: {response.text[:100]}")
    except Exception as e:
        print(f"  Error: {e}")
