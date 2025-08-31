#!/usr/bin/env python3
"""Test Report Generation API"""

import requests
import os

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token"""
    login_data = {'username': 'admin', 'password': 'admin123'}
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    
    if resp.status_code == 200:
        return resp.json().get('access_token')
    return None

def test_reports():
    """Test various report endpoints"""
    token = get_auth_token()
    if not token:
        print("❌ Could not authenticate")
        return
    
    print(f"✅ Authenticated successfully")
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test report endpoints
    reports = [
        ("/api/v1/reports/export/risk-register?format=excel", "risk_register.xlsx"),
        ("/api/v1/reports/export/risk-register?format=csv", "risk_register.csv"),
        ("/api/v1/reports/risk-report", "risk_report.pdf"),
    ]
    
    for endpoint, filename in reports:
        print(f"\nTesting {endpoint}...")
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        
        if resp.status_code == 200:
            # Save file
            output_dir = "generated_reports"
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            
            file_size = os.path.getsize(filepath)
            print(f"  ✅ Success! Generated {filename} ({file_size} bytes)")
        else:
            print(f"  ❌ Failed: {resp.status_code} - {resp.text[:100]}")
    
    print("\n" + "="*50)
    print("Report generation test complete!")
    print(f"Check the 'generated_reports' directory for output files")

if __name__ == "__main__":
    test_reports()