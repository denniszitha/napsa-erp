#!/usr/bin/env python3
"""
Script to create a test control by authenticating with the backend directly
and then calling the frontend API with the token
"""
import requests
import json
import sys

# Configuration
BACKEND_URL = "http://localhost:58001/api/v1"
FRONTEND_URL = "http://localhost:58000"

def login():
    """Login to backend and get token"""
    print("1. Logging in to backend...")
    
    response = requests.post(
        f"{BACKEND_URL}/auth/login",
        data={
            "username": "admin",
            "password": "Admin@123"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"   ✓ Login successful")
        print(f"   Token: {token[:40]}...")
        return token
    else:
        print(f"   ✗ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def create_control_via_backend(token):
    """Create control directly via backend"""
    print("\n2. Creating control via backend API...")
    
    control_data = {
        "name": "Test Control - Direct Backend",
        "description": "This control was created directly via backend API",
        "type": "preventive",
        "control_owner": "Admin",
        "implementation_status": "Implemented",
        "testing_frequency": "Monthly"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/controls/",
        json=control_data,
        headers=headers
    )
    
    if response.status_code in [200, 201]:
        control = response.json()
        print(f"   ✓ Control created successfully")
        print(f"   ID: {control['id']}")
        print(f"   Name: {control['name']}")
        return control
    else:
        print(f"   ✗ Failed to create control: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def create_control_via_frontend(token):
    """Create control via frontend API with authentication"""
    print("\n3. Creating control via frontend API...")
    
    control_data = {
        "name": "Test Control - Via Frontend",
        "description": "This control was created via frontend API with backend token",
        "type": "detective",
        "control_owner": "Frontend Admin",
        "implementation_status": "Implemented",
        "testing_frequency": "Quarterly",
        "category": "IT Security",
        "department": "IT"
    }
    
    # Create session and set cookies
    session = requests.Session()
    
    # Set the authentication cookie
    session.cookies.set('napsa_token', token, domain='localhost', path='/')
    
    # Also try with headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = session.post(
        f"{FRONTEND_URL}/controls/api/create",
        json=control_data,
        headers=headers
    )
    
    print(f"   Response status: {response.status_code}")
    print(f"   Response headers: {dict(response.headers)}")
    
    if response.status_code in [200, 201]:
        try:
            result = response.json()
        except:
            print(f"   Response text: {response.text[:500]}")
            return None
            
        if result.get('success'):
            print(f"   ✓ Control created successfully via frontend")
            if result.get('data'):
                print(f"   ID: {result['data'].get('id')}")
                print(f"   Name: {result['data'].get('name')}")
        else:
            print(f"   ✗ Frontend returned error: {result.get('error')}")
        return result
    else:
        print(f"   ✗ Failed to create control: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error}")
        except:
            print(f"   Response: {response.text[:200]}")
        return None

def list_controls():
    """List existing controls"""
    print("\n4. Listing controls...")
    
    response = requests.get(f"{BACKEND_URL}/controls/")
    
    if response.status_code == 200:
        controls = response.json()
        print(f"   ✓ Found {len(controls)} controls")
        for control in controls[-3:]:  # Show last 3
            print(f"   - {control['name']} ({control['type']})")
    else:
        print(f"   ✗ Failed to list controls: {response.status_code}")

def main():
    print("=" * 60)
    print("NAPSA ERM - Control Creation Test")
    print("=" * 60)
    
    # Step 1: Login
    token = login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Step 2: Create via backend
    backend_control = create_control_via_backend(token)
    
    # Step 3: Create via frontend
    frontend_control = create_control_via_frontend(token)
    
    # Step 4: List controls
    list_controls()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("\nNOTE: To use the web interface:")
    print("1. Go to http://102.23.120.243:58000/auth/login")
    print("2. Login with username: admin, password: Admin@123")
    print("3. Navigate to Controls section")
    print("4. You should now be able to create controls")
    print("=" * 60)

if __name__ == "__main__":
    main()