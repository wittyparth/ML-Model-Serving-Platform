"""
Manual test script for Model Management endpoints
Tests model upload, listing, versioning, and updates
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def main():
    print("\n[TEST] Testing Model Management System")
    print("="*60)
    
    # Step 1: Login
    print("\n[1] Logging in...")
    login_data = {
        "email": "testuser@example.com",
        "password": "mypassword123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("[X] Login failed!")
        print_response("Login Error", response)
        return
    
    token = response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Login successful!")
    
    # Step 2: List existing models
    print("\n[2] Listing existing models...")
    response = requests.get(f"{BASE_URL}/models", headers=headers)
    print_response("Model List", response)
    
    # Step 3: Upload a new model
    print("\n[3️⃣]  Uploading a new model...")
    model_file = Path("test_model.pkl")
    
    if not model_file.exists():
        print("[X] test_model.pkl not found! Run create_test_model.py first")
        return
    
    files = {"file": open(model_file, "rb")}
    data = {
        "name": "iris_classifier",
        "description": "Iris flower classification model",
        "model_type": "sklearn"
    }
    
    response = requests.post(
        f"{BASE_URL}/models/upload",
        headers=headers,
        files=files,
        data=data
    )
    print_response("Model Upload", response)
    
    if response.status_code != 201:
        print("[X] Model upload failed!")
        return
    
    model_id = response.json()["data"]["model"]["id"]
    print(f"\n[OK] Model uploaded! ID: {model_id}")
    
    # Step 4: Get model details
    print("\n[4️⃣]  Getting model details...")
    response = requests.get(f"{BASE_URL}/models/{model_id}", headers=headers)
    print_response("Model Details", response)
    
    # Step 5: Update model
    print("\n[5️⃣]  Updating model description...")
    update_data = {
        "description": "Updated: Production-ready iris classifier",
        "status": "active"
    }
    response = requests.patch(
        f"{BASE_URL}/models/{model_id}",
        headers=headers,
        json=update_data
    )
    print_response("Model Update", response)
    
    # Step 6: Upload new version
    print("\n[6️⃣]  Uploading version 2 of the same model...")
    files = {"file": open(model_file, "rb")}
    data = {
        "name": "iris_classifier",
        "description": "Version 2 with better accuracy",
        "model_type": "sklearn"
    }
    
    response = requests.post(
        f"{BASE_URL}/models/upload",
        headers=headers,
        files=files,
        data=data
    )
    print_response("Version 2 Upload", response)
    
    # Step 7: List all models again
    print("\n[7️⃣]  Listing all models (should show multiple versions)...")
    response = requests.get(f"{BASE_URL}/models", headers=headers)
    print_response("Updated Model List", response)
    
    # Step 8: Filter by status
    print("\n[8️⃣]  Filtering models by status...")
    response = requests.get(f"{BASE_URL}/models?status_filter=active", headers=headers)
    print_response("Active Models Only", response)
    
    # Step 9: Archive a model
    print("\n[9️⃣]  Archiving (soft delete) the first version...")
    update_data = {"status": "archived"}
    response = requests.patch(
        f"{BASE_URL}/models/{model_id}",
        headers=headers,
        json=update_data
    )
    print_response("Archive Model", response)
    
    # Step 10: Verify archived model doesn't show in active filter
    print("\n🔟 Checking active models (archived should be excluded)...")
    response = requests.get(f"{BASE_URL}/models?status_filter=active", headers=headers)
    print_response("Active Models After Archive", response)
    
    print("\n" + "="*60)
    print("[OK] All Model Management tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()
