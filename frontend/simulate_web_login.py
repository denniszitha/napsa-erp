#!/usr/bin/env python3
"""
Simulate web browser login and test control creation
"""
import requests
from urllib.parse import urljoin

class NAPSAWebClient:
    def __init__(self, base_url="http://localhost:58000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def login(self, username, password):
        """Login through the web interface"""
        print(f"Logging in as {username}...")
        
        # First, get the login page (might set CSRF token)
        login_page = self.session.get(f"{self.base_url}/auth/login")
        print(f"  Login page status: {login_page.status_code}")
        
        # Submit login form
        login_data = {
            "username": username,
            "password": password,
            "remember": "on"
        }
        
        response = self.session.post(
            f"{self.base_url}/auth/login",
            data=login_data,
            allow_redirects=False
        )
        
        print(f"  Login response: {response.status_code}")
        
        # Check cookies
        cookies = self.session.cookies.get_dict()
        print(f"  Cookies set: {list(cookies.keys())}")
        
        if 'napsa_token' in cookies:
            print(f"  ✓ Authentication token received")
            print(f"    Token preview: {cookies['napsa_token'][:40]}...")
            return True
        elif 'napsa_session' in cookies:
            print(f"  ✓ Session cookie received")
            return True
        else:
            print(f"  ✗ No authentication cookie received")
            # Check if redirected to dashboard (successful login)
            if response.status_code in [302, 303] and 'dashboard' in response.headers.get('Location', ''):
                print(f"  ✓ Redirected to dashboard (login successful)")
                return True
            return False
    
    def test_controls_access(self):
        """Test if we can access controls page"""
        print("\nTesting controls page access...")
        response = self.session.get(f"{self.base_url}/controls/")
        print(f"  Controls page status: {response.status_code}")
        
        if response.status_code == 200:
            if "login" in response.url:
                print(f"  ✗ Redirected to login page")
                return False
            else:
                print(f"  ✓ Controls page accessible")
                return True
        return False
    
    def create_control(self):
        """Create a control through the web API"""
        print("\nCreating control via web API...")
        
        control_data = {
            "name": "Test Control - Web Interface",
            "description": "Created through simulated web login",
            "type": "preventive",
            "control_owner": "Web Admin",
            "implementation_status": "Implemented",
            "testing_frequency": "Monthly",
            "category": "IT Security",
            "department": "IT"
        }
        
        # Add all cookies to the request
        response = self.session.post(
            f"{self.base_url}/controls/api/create",
            json=control_data
        )
        
        print(f"  Create control status: {response.status_code}")
        print(f"  Response Content-Type: {response.headers.get('Content-Type')}")
        
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                result = response.json()
                if result.get('success'):
                    print(f"  ✓ Control created successfully!")
                    if result.get('data'):
                        print(f"    ID: {result['data'].get('id')}")
                else:
                    print(f"  ✗ Creation failed: {result.get('error')}")
            except Exception as e:
                print(f"  ✗ Failed to parse JSON: {e}")
        else:
            print(f"  ✗ Received HTML instead of JSON (likely redirected to login)")
            print(f"    First 200 chars: {response.text[:200]}")
        
        return response

def main():
    print("=" * 60)
    print("NAPSA ERM - Web Login Simulation")
    print("=" * 60)
    
    client = NAPSAWebClient()
    
    # Step 1: Login
    if not client.login("admin", "Admin@123"):
        print("\n❌ Login failed. Please check credentials.")
        print("\nNOTE: You need to login manually through the web browser:")
        print("1. Open http://102.23.120.243:58000/auth/login")
        print("2. Username: admin")
        print("3. Password: Admin@123")
        return
    
    # Step 2: Test access
    if client.test_controls_access():
        # Step 3: Create control
        client.create_control()
    
    print("\n" + "=" * 60)
    print("Simulation completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()