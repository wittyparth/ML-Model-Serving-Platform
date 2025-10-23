import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Login
login_data = {"email": "testuser@example.com", "password": "mypassword123"}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
token = response.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get model ID
model_id = "a6505c93-d2eb-4979-b0ab-2e4b439c9827"

# Make prediction
prediction_data = {
    "input": {
        "feature1": 0.5,
        "feature2": -0.5,
        "feature3": 1.0,
        "feature4": -1.0
    }
}

print(f"\n[PREDICTION TEST]")
print(f"Model ID: {model_id}")
print(f"Input: {prediction_data['input']}")
print("="*60)

response = requests.post(
    f"{BASE_URL}/predict/{model_id}",
    headers=headers,
    json=prediction_data
)

print(f"\nStatus: {response.status_code}")
print(json.dumps(response.json(), indent=2))
