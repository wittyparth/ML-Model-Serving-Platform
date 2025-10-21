"""
Manual test script for authentication endpoints
Run this after starting the server with: docker-compose up
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_auth_flow():
    """Test the complete authentication flow"""
    
    print("=" * 50)
    print("Testing Authentication Endpoints")
    print("=" * 50)
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    # 1. Register
    print("\n1. Testing Registration...")
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ Registration successful")
    else:
        print("❌ Registration failed")
        return
    
    # 2. Login
    print("\n2. Testing Login...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful")
        access_token = data["data"]["access_token"]
        refresh_token = data["data"]["refresh_token"]
        print(f"Access Token: {access_token[:50]}...")
        print(f"Refresh Token: {refresh_token[:50]}...")
    else:
        print("❌ Login failed")
        print(f"Response: {response.json()}")
        return
    
    # 3. Get current user info
    print("\n3. Testing Get Current User...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Get current user successful")
    else:
        print("❌ Get current user failed")
    
    # 4. Test invalid token
    print("\n4. Testing Invalid Token...")
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Invalid token correctly rejected")
    else:
        print("❌ Invalid token should have been rejected")
    
    # 5. Test refresh token
    print("\n5. Testing Token Refresh...")
    response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        new_access_token = data["data"]["access_token"]
        print("✅ Token refresh successful")
        print(f"New Access Token: {new_access_token[:50]}...")
    else:
        print("❌ Token refresh failed")
        print(f"Response: {response.json()}")
    
    # 6. Test duplicate registration
    print("\n6. Testing Duplicate Registration...")
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 409:
        print("✅ Duplicate email correctly rejected")
    else:
        print("❌ Duplicate email should have been rejected")
    
    # 7. Test wrong password
    print("\n7. Testing Wrong Password...")
    wrong_login = {
        "email": test_user["email"],
        "password": "wrongpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=wrong_login)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Wrong password correctly rejected")
    else:
        print("❌ Wrong password should have been rejected")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_auth_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server.")
        print("Make sure the server is running with: docker-compose up")
    except Exception as e:
        print(f"❌ Error: {e}")
