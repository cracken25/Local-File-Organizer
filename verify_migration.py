import requests
import time
import os

BASE_URL = "http://127.0.0.1:8765/api"
INPUT_PATH = "/Users/jeffmccracken/LocalFileOrganizer/Local-File-Organizer/sample_data"

def run_verification():
    # 1. Scan
    print("Scanning...")
    resp = requests.post(f"{BASE_URL}/scan", json={"input_path": INPUT_PATH})
    resp.raise_for_status()
    print(resp.json())

    # 2. Classify
    print("Classifying...")
    resp = requests.post(f"{BASE_URL}/classify", json={"mode": "content"})
    resp.raise_for_status()
    
    # 3. Wait for completion
    while True:
        status = requests.get(f"{BASE_URL}/classify/status").json()
        print(f"Status: {status}")
        if not status['is_classifying'] and status['progress'] == 100:
            break
        time.sleep(2)
    
    # 4. Get items
    items = requests.get(f"{BASE_URL}/items").json()
    item_ids = [item['id'] for item in items]
    print(f"Found {len(items)} items")

    # 5. Approve all
    print("Approving all...")
    resp = requests.post(f"{BASE_URL}/items/bulk-action", json={
        "item_ids": item_ids,
        "action": "approve"
    })
    resp.raise_for_status()
    print(resp.json())

    # 6. Migrate
    print("Migrating...")
    resp = requests.post(f"{BASE_URL}/migrate", json={})
    resp.raise_for_status()
    print(resp.json())

    # 7. Verify files
    organized_dir = os.path.join(INPUT_PATH, "Organized")
    if os.path.exists(organized_dir):
        print(f"Organized directory exists: {organized_dir}")
        for root, dirs, files in os.walk(organized_dir):
            for file in files:
                print(f"Found migrated file: {os.path.join(root, file)}")
    else:
        print("Organized directory NOT found!")

if __name__ == "__main__":
    run_verification()
