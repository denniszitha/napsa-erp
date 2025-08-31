#!/usr/bin/env python3
"""Test login functionality"""

import requests
import json

# Test login endpoint
def test_login():
    url = "http://localhost:8000/api/v1/auth/login"
    
    # Test with admin credentials (username, not email)
    data = {
        "username": "admin",
        "password": "Admin@2024!"
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Login successful!")
        print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
        print(f"Token Type: {result.get('token_type', 'N/A')}")
        return result.get('access_token')
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

# Test authenticated endpoint
def test_me_endpoint(token):
    if not token:
        print("No token available")
        return
    
    url = "http://localhost:8000/api/v1/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user = response.json()
        print("\n✅ User info retrieved successfully!")
        print(f"Email: {user.get('email')}")
        print(f"Username: {user.get('username')}")
        print(f"Full Name: {user.get('full_name')}")
        print(f"Role: {user.get('role')}")
        print(f"Department: {user.get('department')}")
        print(f"Is Superuser: {user.get('is_superuser')}")
    else:
        print(f"\n❌ Failed to get user info: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    print("Testing NAPSA ERM Login\n" + "="*40)
    token = test_login()
    if token:
        test_me_endpoint(token)