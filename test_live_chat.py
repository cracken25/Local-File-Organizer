"""Test live chat with longer timeout to see actual LLM response"""
import requests
import json
import time

base_url = "http://localhost:8888"
api_key = "FVQ0990-9MDM0CW-Q5TR4VV-P3GXGV8"
workspace_slug = "taxonomyclassifierlibrarian"

print(f"Testing live chat with {workspace_slug}...")
print("Sending classification request...\n")

try:
    response = requests.post(
        f"{base_url}/api/v1/workspace/{workspace_slug}/chat",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "message": "What are the main taxonomy categories you know about? List the top 3.",
            "mode": "chat"
        },
        timeout=60  # Longer timeout for LLM processing
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}\n")
    print(f"Response Text:\n{response.text}\n")
    
    if response.status_code == 200:
        try:
            json_response = response.json()
            print("✅ JSON Response:")
            print(json.dumps(json_response, indent=2))
            
            if 'textResponse' in json_response:
                print(f"\n📝 LLM Response:\n{json_response['textResponse']}")
            
            if 'sources' in json_response:
                print(f"\n📚 Sources: {len(json_response['sources'])} citations")
        except json.JSONDecodeError:
            print("⚠️  Response is not JSON")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
