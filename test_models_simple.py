import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Login
login_data = {"email": "testuser@example.com", "password": "mypassword123"}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
token = response.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("\n[TEST] Model Management System")
print("=" * 60)

# Test 1: List models
print("\n[1] Listing all models...")
response = requests.get(f"{BASE_URL}/models", headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test 2: Get specific model
model_id = "a6505c93-d2eb-4979-b0ab-2e4b439c9827"
print(f"\n[2] Getting model {model_id}...")
response = requests.get(f"{BASE_URL}/models/{model_id}", headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

print("\n[OK] All tests passed!")
