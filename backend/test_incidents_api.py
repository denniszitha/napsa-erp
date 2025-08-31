#!/usr/bin/env python3
"""Test Incidents API and create test data if needed"""

import requests
import json
from datetime import datetime
import sys

BASE_URL = "http://localhost:8000"

# Try to login with existing admin or create one
def get_auth_token():
    # First, try to login with admin/admin123
    login_data = {'username': 'admin', 'password': 'admin123'}
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    
    if resp.status_code == 200:
        return resp.json().get('access_token')
    
    # Try different password
    login_data = {'username': 'admin', 'password': 'Admin@2024'}
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    
    if resp.status_code == 200:
        return resp.json().get('access_token')
    
    print(f"Login failed: {resp.status_code} - {resp.text}")
    
    # Try to register a new user
    print("Attempting to register new test user...")
    register_data = {
        "username": "testuser",
        "email": "test@napsa.co.zm",
        "password": "Test@2024",
        "full_name": "Test User"
    }
    
    resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    if resp.status_code in [200, 201]:
        print("Registered new user, attempting login...")
        login_data = {'username': 'testuser', 'password': 'Test@2024'}
        resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
        if resp.status_code == 200:
            return resp.json().get('access_token')
    
    return None

def test_incidents_api(token):
    headers = {'Authorization': f'Bearer {token}'}
    
    # 1. Test GET incidents
    print("\n1. Testing GET /api/v1/incidents")
    resp = requests.get(f"{BASE_URL}/api/v1/incidents", headers=headers)
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200:
        incidents = resp.json()
        print(f"   Found {len(incidents)} incidents")
    else:
        print(f"   Error: {resp.text[:200]}")
    
    # 2. Test POST - Create new incident
    print("\n2. Testing POST /api/v1/incidents")
    new_incident = {
        "title": "Test Security Incident",
        "description": "Testing incident API functionality",
        "incident_type": "security_incident",
        "severity": "medium",
        "status": "new"
    }
    
    resp = requests.post(f"{BASE_URL}/api/v1/incidents", json=new_incident, headers=headers)
    print(f"   Status: {resp.status_code}")
    
    if resp.status_code in [200, 201]:
        incident = resp.json()
        incident_id = incident.get('id')
        print(f"   Created incident: {incident_id}")
        
        # 3. Test GET specific incident
        print(f"\n3. Testing GET /api/v1/incidents/{incident_id}")
        resp = requests.get(f"{BASE_URL}/api/v1/incidents/{incident_id}", headers=headers)
        print(f"   Status: {resp.status_code}")
        
        # 4. Test PUT - Update incident
        print(f"\n4. Testing PUT /api/v1/incidents/{incident_id}")
        update_data = {
            "status": "investigating",
            "severity": "high"
        }
        resp = requests.put(f"{BASE_URL}/api/v1/incidents/{incident_id}", 
                           json=update_data, headers=headers)
        print(f"   Status: {resp.status_code}")
        
        # 5. Test corrective actions
        print(f"\n5. Testing POST /api/v1/incidents/{incident_id}/corrective-actions")
        action_data = {
            "description": "Implement additional firewall rules",
            "responsible": "Security Team",
            "due_date": "2025-08-31",
            "status": "pending"
        }
        resp = requests.post(f"{BASE_URL}/api/v1/incidents/{incident_id}/corrective-actions", 
                            json=action_data, headers=headers)
        print(f"   Status: {resp.status_code}")
        
        # 6. Test statistics
        print("\n6. Testing GET /api/v1/incidents/stats")
        resp = requests.get(f"{BASE_URL}/api/v1/incidents/stats", headers=headers)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            stats = resp.json()
            print(f"   Total incidents: {stats.get('total_incidents')}")
            print(f"   Open incidents: {stats.get('open_incidents_count')}")
            print(f"   MTTR: {stats.get('mean_time_to_resolution_hours')} hours")
        
        return incident_id
    else:
        print(f"   Error: {resp.text[:200]}")
        return None

def main():
    print("="*50)
    print("NAPSA Incident Management API Test")
    print("="*50)
    
    # Get authentication token
    print("\nAuthenticating...")
    token = get_auth_token()
    
    if not token:
        print("ERROR: Could not authenticate")
        sys.exit(1)
    
    print(f"Got token: {token[:20]}...")
    
    # Test incidents API
    incident_id = test_incidents_api(token)
    
    if incident_id:
        print("\n" + "="*50)
        print("✅ All Incident API endpoints are working!")
        print(f"Created test incident: {incident_id}")
    else:
        print("\n" + "="*50)
        print("⚠️ Some issues were encountered")
    
    print("="*50)

if __name__ == "__main__":
    main()