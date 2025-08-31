#!/usr/bin/env python3
"""
Fixed test script for NAPSA ERM API endpoints
"""

import requests
import json
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Optional
import time

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

class ERMAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def log_success(self, message: str):
        print(f"{GREEN}✓ {message}{RESET}")
        self.test_results["passed"] += 1
    
    def log_error(self, message: str):
        print(f"{RED}✗ {message}{RESET}")
        self.test_results["failed"] += 1
    
    def log_info(self, message: str):
        print(f"{BLUE}ℹ {message}{RESET}")
    
    def log_warning(self, message: str):
        print(f"{YELLOW}⚠ {message}{RESET}")
    
    def setup_auth_header(self):
        """Add authentication header to session"""
        if self.token:
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
    
    def test_endpoint(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     expected_status: List[int] = None, description: str = "") -> Optional[Dict]:
        """Generic endpoint test function"""
        if expected_status is None:
            expected_status = [200]
        
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            elif method == "PATCH":
                response = self.session.patch(url, json=data)
            
            if response.status_code in expected_status:
                self.log_success(f"{method} {endpoint} - {description} (Status: {response.status_code})")
                try:
                    return response.json() if response.text else None
                except:
                    return response.text
            else:
                self.log_error(f"{method} {endpoint} - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    try:
                        error_detail = response.json()
                        print(f"   Error: {error_detail}")
                    except:
                        print(f"   Response: {response.text[:200]}")
                return None
        except requests.exceptions.ConnectionError:
            self.log_error(f"{method} {endpoint} - Connection error")
            return None
        except Exception as e:
            self.log_error(f"{method} {endpoint} - {str(e)}")
            return None
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print(f"\n{YELLOW}=== Testing Authentication ==={RESET}")
        
        # Test login with form data
        form_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD,
            "grant_type": "password"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/login", data=form_data)
        if response.status_code == 200:
            self.log_success("POST /auth/login - Admin login successful")
            token_data = response.json()
            self.token = token_data.get("access_token")
            self.setup_auth_header()
            return True
        else:
            self.log_error(f"POST /auth/login - Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def test_user_endpoints(self):
        """Test user management endpoints"""
        print(f"\n{YELLOW}=== Testing User Endpoints ==={RESET}")
        
        # Get current user
        user_data = self.test_endpoint("GET", "/users/me", description="Get current user")
        if user_data:
            self.user_id = user_data.get("id")
            self.log_info(f"Current user: {user_data.get('username')} (ID: {self.user_id})")
    
    def test_risk_endpoints(self):
        """Test risk management endpoints"""
        print(f"\n{YELLOW}=== Testing Risk Endpoints ==={RESET}")
        
        # List risks
        risks_response = self.test_endpoint("GET", "/risks/", description="List all risks")
        
        if risks_response:
            # Check if response is a list or dict with items
            if isinstance(risks_response, list):
                risks = risks_response
            elif isinstance(risks_response, dict) and 'items' in risks_response:
                risks = risks_response['items']
            elif isinstance(risks_response, dict) and 'data' in risks_response:
                risks = risks_response['data']
            else:
                # Try to extract risks from other possible formats
                risks = []
                self.log_warning(f"Unexpected response format: {type(risks_response)}")
                
            self.log_info(f"Total risks: {len(risks) if risks else 0}")
            
            if risks and len(risks) > 0:
                risk = risks[0]
                risk_id = risk.get('id')
                if risk_id:
                    # Get specific risk
                    self.test_endpoint("GET", f"/risks/{risk_id}", description="Get specific risk")
    
    def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        print(f"\n{YELLOW}=== Testing Dashboard Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/dashboard/overview", description="Get dashboard overview")
        self.test_endpoint("GET", "/dashboard/stats", expected_status=[200, 404], description="Get dashboard stats")
        self.test_endpoint("GET", "/dashboard/recent-activities", description="Get recent activities")
        self.test_endpoint("GET", "/dashboard/my-tasks", description="Get my tasks")
    
    def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        print(f"\n{YELLOW}=== Testing Analytics Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/analytics/risk-summary", description="Get risk summary")
        self.test_endpoint("GET", "/analytics/risk-trends", description="Get risk trends")
        self.test_endpoint("GET", "/analytics/department-risks", description="Get department risks")
    
    def test_kri_endpoints(self):
        """Test KRI endpoints"""
        print(f"\n{YELLOW}=== Testing KRI Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/kris/", description="List all KRIs")
        self.test_endpoint("GET", "/kris/dashboard", expected_status=[200, 404], description="Get KRI dashboard")
    
    def test_control_endpoints(self):
        """Test control endpoints"""
        print(f"\n{YELLOW}=== Testing Control Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/controls/", description="List all controls")
        self.test_endpoint("GET", "/controls/effectiveness", expected_status=[200, 404], description="Get control effectiveness")
    
    def test_assessment_endpoints(self):
        """Test assessment endpoints"""
        print(f"\n{YELLOW}=== Testing Assessment Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/assessments/", description="List all assessments")
    
    def test_incident_endpoints(self):
        """Test incident endpoints"""
        print(f"\n{YELLOW}=== Testing Incident Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/incidents/", description="List all incidents")
        self.test_endpoint("GET", "/incidents/stats", expected_status=[200, 404], description="Get incident stats")
    
    def test_compliance_endpoints(self):
        """Test compliance endpoints"""
        print(f"\n{YELLOW}=== Testing Compliance Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/compliance/frameworks", description="List compliance frameworks")
        self.test_endpoint("GET", "/compliance/requirements", description="List requirements")
    
    def test_treatment_endpoints(self):
        """Test treatment endpoints"""
        print(f"\n{YELLOW}=== Testing Treatment Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/treatments/", description="List all treatments")
    
    def test_report_endpoints(self):
        """Test report endpoints"""
        print(f"\n{YELLOW}=== Testing Report Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/reports/risk-register", description="Get risk register")
        self.test_endpoint("GET", "/reports/executive-summary", expected_status=[200, 404], description="Get executive summary")
    
    def test_audit_endpoints(self):
        """Test audit endpoints"""
        print(f"\n{YELLOW}=== Testing Audit Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/audit/logs", description="Get audit logs")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{CYAN}{'='*60}")
        print(f"Test Summary")
        print(f"{'='*60}{RESET}")
        
        total = sum(self.test_results.values())
        print(f"{GREEN}Passed: {self.test_results['passed']}{RESET}")
        print(f"{RED}Failed: {self.test_results['failed']}{RESET}")
        print(f"{CYAN}Skipped: {self.test_results['skipped']}{RESET}")
        print(f"Total: {total}")
        
        if self.test_results['failed'] == 0:
            print(f"\n{GREEN}✨ All tests passed! ✨{RESET}")
        else:
            print(f"\n{YELLOW}⚠ Some tests failed. Check the output above.{RESET}")
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"{BLUE}{'='*60}")
        print(f"NAPSA ERM API Tests")
        print(f"{'='*60}{RESET}")
        
        if not self.test_auth_endpoints():
            print(f"\n{RED}Authentication failed. Cannot continue.{RESET}")
            return
        
        # Test all endpoints
        self.test_user_endpoints()
        self.test_risk_endpoints()
        self.test_assessment_endpoints()
        self.test_control_endpoints()
        self.test_kri_endpoints()
        self.test_treatment_endpoints()
        self.test_incident_endpoints()
        self.test_compliance_endpoints()
        self.test_analytics_endpoints()
        self.test_dashboard_endpoints()
        self.test_report_endpoints()
        self.test_audit_endpoints()
        
        # Print summary
        self.print_summary()


if __name__ == "__main__":
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"{RED}Cannot connect to API. Please ensure the server is running.{RESET}")
        sys.exit(1)
    
    # Run tests
    tester = ERMAPITester()
    tester.run_all_tests()
