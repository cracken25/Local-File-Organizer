"""
Comprehensive diagnostic script for AnythingLLM API.

This script probes various API endpoints to discover the actual API structure.
"""
import requests
import json

base_url = "http://localhost:8888"
api_key = "FVQ0990-9MDM0CW-Q5TR4VV-P3GXGV8"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("AnythingLLM API Diagnostic Tool")
print("=" * 70)

# Test 1: Check API docs
print("\n[1] Checking for API Documentation...")
doc_endpoints = [
    "/api/docs",
    "/api/swagger",
    "/docs",
    "/swagger",
    "/api/v1/docs"
]

for endpoint in doc_endpoints:
    try:
        resp = requests.get(f"{base_url}{endpoint}", timeout=5)
        if resp.status_code == 200 and len(resp.text) > 10:
            print(f"  ✅ Found docs at: {endpoint}")
            print(f"     Content-Type: {resp.headers.get('Content-Type')}")
            print(f"     Length: {len(resp.text)} bytes")
            if 'json' in resp.headers.get('Content-Type', ''):
                print(f"     Preview: {resp.text[:200]}")
        else:
            print(f"  ❌ {endpoint}: {resp.status_code}")
    except Exception as e:
        print(f"  ❌ {endpoint}: {e}")

# Test 2: Try different API versions
print("\n[2] Testing API Version Endpoints...")
version_endpoints = [
    "/api/v1/system",
    "/api/system", 
    "/api/v1/auth",
    "/api/health",
    "/health",
    "/api/v1/workspaces",
    "/workspaces"
]

for endpoint in version_endpoints:
    try:
        resp = requests.get(
            f"{base_url}{endpoint}",
            headers=headers,
            timeout=5
        )
        content_type = resp.headers.get('Content-Type', '')
        print(f"  {endpoint}:")
        print(f"    Status: {resp.status_code}")
        print(f"    Content-Type: {content_type}")
        
        if 'json' in content_type:
            try:
                data = resp.json()
                print(f"    Response: {json.dumps(data, indent=2)[:200]}")
            except:
                print(f"    Response (text): {resp.text[:100]}")
        else:
            print(f"    Response (text): {resp.text[:100]}")
    except Exception as e:
        print(f"    Error: {e}")

# Test 3: Try chat endpoint variations
print("\n[3] Testing Chat Endpoint Variations...")
workspace_slug = "taxonomyclassifierlibrarian"
chat_endpoints = [
    f"/api/v1/workspace/{workspace_slug}/chat",
    f"/api/workspace/{workspace_slug}/chat",
    f"/workspace/{workspace_slug}/chat",
    f"/api/v1/chat/{workspace_slug}",
    f"/chat/{workspace_slug}",
]

message_payload = {
    "message": "Hello, can you respond?",
    "mode": "chat"
}

for endpoint in chat_endpoints:
    try:
        resp = requests.post(
            f"{base_url}{endpoint}",
            headers=headers,
            json=message_payload,
            timeout=30
        )
        content_type = resp.headers.get('Content-Type', '')
        print(f"  {endpoint}:")
        print(f"    Status: {resp.status_code}")
        print(f"    Content-Type: {content_type}")
        
        if resp.status_code == 200:
            if 'json' in content_type:
                try:
                    data = resp.json()
                    print(f"    ✅ JSON Response!")
                    print(f"    Keys: {list(data.keys())}")
                    if 'textResponse' in data:
                        print(f"    textResponse: {data['textResponse'][:100]}...")
                except:
                    print(f"    Response (text): {resp.text}")
            else:
                print(f"    Response (text): {resp.text[:100]}")
        print()
    except Exception as e:
        print(f"    Error: {e}\n")

# Test 4: Check actual HTML page source for clues
print("\n[4] Checking HTML for JavaScript API Clues...")
try:
    resp = requests.get(base_url, timeout=5)
    html = resp.text
    
    # Look for API endpoint patterns in JavaScript
    if 'api/v1' in html:
        print("  ✅ Found 'api/v1' references in HTML")
    if '/workspace/' in html:
        print("  ✅ Found '/workspace/' references")
    if 'chat' in html.lower():
        print("  ✅ Found 'chat' references")
        
    # Try to find actual API calls
    import re
    api_patterns = re.findall(r'[\'"]/(api/[^\'"]+)[\'"]', html)
    if api_patterns:
        print(f"  Found potential API paths:")
        for pattern in set(api_patterns[:10]):
            print(f"    - {pattern}")
except Exception as e:
    print(f"  Error reading HTML: {e}")

print("\n" + "=" * 70)
print("Diagnostic Complete")
print("=" * 70)
print("\n💡 RECOMMENDATION:")
print("1. Check the AnythingLLM UI in browser at http://localhost:8888")
print("2. Open Browser DevTools (F12) → Network tab")
print("3. Send a chat message in the UI")
print("4. Look for the actual API endpoint being called")
print("5. Copy the exact request format and use it in our client")
