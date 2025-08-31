#!/usr/bin/env python3
"""
Comprehensive test script for NAPSA ERM API endpoints
Tests all endpoints with proper authentication and data flow
"""

import requests
import json
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Optional
import time

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class ERMAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.created_entities = {
            'users': [],
            'risks': [],
            'assessments': [],
            'controls': [],
            'kris': [],
            'treatments': [],
            'incidents': [],
            'compliance': []
        }
    
    def log_success(self, message: str):
        print(f"{GREEN}✓ {message}{RESET}")
    
    def log_error(self, message: str):
        print(f"{RED}✗ {message}{RESET}")
    
    def log_info(self, message: str):
        print(f"{BLUE}ℹ {message}{RESET}")
    
    def log_warning(self, message: str):
        print(f"{YELLOW}⚠ {message}{RESET}")
    
    def setup_auth_header(self):
        """Add authentication header to session"""
        if self.token:
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
    
    def test_endpoint(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     expected_status: int = 200, description: str = "") -> Optional[Dict]:
        """Generic endpoint test function"""
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
            
            if response.status_code == expected_status:
                self.log_success(f"{method} {endpoint} - {description}")
                return response.json() if response.text else None
            else:
                self.log_error(f"{method} {endpoint} - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            self.log_error(f"{method} {endpoint} - {str(e)}")
            return None
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print(f"\n{YELLOW}=== Testing Authentication Endpoints ==={RESET}")
        
        # Test login
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        # OAuth2 compatible login
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
        else:
            self.log_error(f"POST /auth/login - Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
    
    def test_user_endpoints(self):
        """Test user management endpoints"""
        print(f"\n{YELLOW}=== Testing User Endpoints ==={RESET}")
        
        # Get current user
        user_data = self.test_endpoint("GET", "/users/me", description="Get current user")
        if user_data:
            self.user_id = user_data.get("id")
        
        # List all users
        self.test_endpoint("GET", "/users/", description="List all users")
    
    def test_risk_endpoints(self):
        """Test risk management endpoints"""
        print(f"\n{YELLOW}=== Testing Risk Endpoints ==={RESET}")
        
        # List risks
        risks = self.test_endpoint("GET", "/risks/", description="List all risks")
        if risks and len(risks) > 0:
            risk_id = risks[0]['id']
            self.created_entities['risks'].append(risk_id)
            
            # Get specific risk
            self.test_endpoint("GET", f"/risks/{risk_id}", description="Get specific risk")
    
    def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        print(f"\n{YELLOW}=== Testing Dashboard Endpoints ==={RESET}")
        
        self.test_endpoint("GET", "/dashboard/overview", description="Get dashboard overview")
        self.test_endpoint("GET", "/dashboard/recent-activities", description="Get recent activities")
        self.test_endpoint("GET", "/dashboard/my-tasks", description="Get my tasks")
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Starting NAPSA ERM API Endpoint Tests{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        # Test endpoints in logical order
        self.test_auth_endpoints()
        self.test_user_endpoints()
        self.test_risk_endpoints()
        self.test_dashboard_endpoints()
        
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test Suite Completed{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")


if __name__ == "__main__":
    # Check if API is running - fix the endpoint
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"{RED}Cannot connect to API at {BASE_URL}. Please ensure the server is running.{RESET}")
        print(f"Run: cd /opt/napsa-erm-simple/backend && uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Run tests
    tester = ERMAPITester()
    tester.run_all_tests()
