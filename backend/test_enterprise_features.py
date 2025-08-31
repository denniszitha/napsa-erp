"""
Test script for enterprise ERM features
"""
import requests
import json
from datetime import datetime, timezone

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def get_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    return response.json()["access_token"]

def test_analytics(token):
    """Test analytics endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Analytics ===")
    
    # Risk Heatmap
    response = requests.get(f"{BASE_URL}/analytics/risk-heatmap", headers=headers)
    print(f"Risk Heatmap: {response.status_code}")
    
    # Risk Trends
    response = requests.get(f"{BASE_URL}/analytics/risk-trends?days=30", headers=headers)
    print(f"Risk Trends: {response.status_code}")
    
    # Control Effectiveness
    response = requests.get(f"{BASE_URL}/analytics/control-effectiveness", headers=headers)
    print(f"Control Effectiveness: {response.status_code}")
    
    # Executive Summary
    response = requests.get(f"{BASE_URL}/analytics/executive-summary", headers=headers)
    print(f"Executive Summary: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))

def test_compliance(token):
    """Test compliance endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Compliance ===")
    
    # Compliance Dashboard
    response = requests.get(f"{BASE_URL}/compliance/dashboard", headers=headers)
    print(f"Compliance Dashboard: {response.status_code}")

def test_incidents(token):
    """Test incident management"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Incidents ===")
    
    # Create incident
    incident_data = {
        "title": "Test Security Incident",
        "description": "Suspicious login attempts detected",
        "type": "security_breach",
        "severity": "high",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "affected_systems": ["Authentication System"],
        "affected_users_count": 50
    }
    
    response = requests.post(
        f"{BASE_URL}/incidents/",
        headers=headers,
        json=incident_data
    )
    print(f"Create Incident: {response.status_code}")
    if response.status_code == 200:
        print(f"Incident Number: {response.json()['incident_number']}")

def test_simulation(token, risk_id):
    """Test risk simulation"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Simulations ===")
    
    # What-if analysis
    response = requests.get(
        f"{BASE_URL}/simulation/what-if/{risk_id}?new_likelihood=4&new_impact=4&control_improvement=30",
        headers=headers
    )
    print(f"What-if Analysis: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))

def main():
    """Run all tests"""
    print("Testing Enterprise ERM Features...")
    
    # Get token
    token = get_token()
    print(f"Authentication successful")
    
    # Run tests
    test_analytics(token)
    test_compliance(token)
    test_incidents(token)
    
    # Get a risk ID for simulation
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/risks/?limit=1", headers=headers)
    if response.status_code == 200 and response.json()["data"]:
        risk_id = response.json()["data"][0]["id"]
        test_simulation(token, risk_id)

if __name__ == "__main__":
    main()
