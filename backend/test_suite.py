#!/usr/bin/env python3
"""
Comprehensive API Testing Suite for NAPSA ERM System
Tests all critical endpoints and workflows
"""

import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
import string
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

class ERMTestSuite:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.token = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "start_time": datetime.now()
        }
        self.test_data = {}
        
    def print_header(self, text: str):
        """Print formatted section header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{text.center(60)}")
        print(f"{Fore.CYAN}{'='*60}\n")
    
    def print_test(self, test_name: str, status: str, details: str = ""):
        """Print test result with color coding"""
        if status == "PASS":
            symbol = "✅"
            color = Fore.GREEN
        elif status == "FAIL":
            symbol = "❌"
            color = Fore.RED
        elif status == "SKIP":
            symbol = "⏭️"
            color = Fore.YELLOW
        else:
            symbol = "ℹ️"
            color = Fore.BLUE
            
        print(f"{color}{symbol} {test_name}: {status}")
        if details:
            print(f"   {Fore.WHITE}{details}")
    
    def generate_random_string(self, length: int = 10) -> str:
        """Generate random string for test data"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        url = f"{self.api_url}{endpoint}"
        headers = kwargs.get('headers', {})
        
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        
        try:
            response = requests.request(
                method, 
                url, 
                headers=headers,
                **{k: v for k, v in kwargs.items() if k != 'headers'}
            )
            
            if response.status_code >= 400:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "detail": response.text
                }
            
            return response.json() if response.text else {}
            
        except Exception as e:
            return {
                "error": True,
                "exception": str(e)
            }
    
    # ========== Authentication Tests ==========
    
    def test_authentication(self):
        """Test authentication endpoints"""
        self.print_header("Authentication Tests")
        
        # Test login with default admin
        test_user = {
            "username": "admin",
            "password": "Admin@123"
        }
        
        response = self.make_request(
            "POST", 
            "/auth/login",
            data=test_user
        )
        
        if response and not response.get("error"):
            self.token = response.get("access_token")
            self.print_test("Admin Login", "PASS", "Token obtained successfully")
            self.test_results["passed"] += 1
        else:
            self.print_test("Admin Login", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append("Authentication failed - cannot continue")
            return False
        
        # Test current user endpoint
        response = self.make_request("GET", "/users/me")
        if response and not response.get("error"):
            self.print_test("Get Current User", "PASS", f"User: {response.get('username')}")
            self.test_results["passed"] += 1
        else:
            self.print_test("Get Current User", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
        
        return True
    
    # ========== User Management Tests ==========
    
    def test_user_management(self):
        """Test user CRUD operations"""
        self.print_header("User Management Tests")
        
        # Create test user
        test_user = {
            "username": f"testuser_{self.generate_random_string(5)}",
            "email": f"test_{self.generate_random_string(5)}@napsa.co.zm",
            "full_name": "Test User",
            "password": "TestPass123!",
            "role": "viewer",
            "department": "IT"
        }
        
        response = self.make_request("POST", "/users", json=test_user)
        if response and not response.get("error"):
            self.test_data["test_user_id"] = response.get("id")
            self.print_test("Create User", "PASS", f"User ID: {response.get('id')}")
            self.test_results["passed"] += 1
        else:
            self.print_test("Create User", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
        
        # Get users list
        response = self.make_request("GET", "/users?limit=10")
        if response and isinstance(response, list):
            self.print_test("List Users", "PASS", f"Found {len(response)} users")
            self.test_results["passed"] += 1
        else:
            self.print_test("List Users", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
    
    # ========== Risk Management Tests ==========
    
    def test_risk_management(self):
        """Test risk CRUD operations"""
        self.print_header("Risk Management Tests")
        
        # Create test risk
        test_risk = {
            "title": f"Test Risk {self.generate_random_string(5)}",
            "description": "Automated test risk",
            "category": "operational",
            "likelihood": 3,
            "impact": 4,
            "inherent_risk_score": 12,
            "department": "IT",
            "mitigation_plan": "Test mitigation plan",
            "status": "active"
        }
        
        response = self.make_request("POST", "/risks", json=test_risk)
        if response and not response.get("error"):
            self.test_data["test_risk_id"] = response.get("id")
            self.print_test("Create Risk", "PASS", f"Risk ID: {response.get('id')}")
            self.test_results["passed"] += 1
            
            # Get risk details
            risk_id = response.get("id")
            response = self.make_request("GET", f"/risks/{risk_id}")
            if response and not response.get("error"):
                self.print_test("Get Risk Details", "PASS", f"Risk: {response.get('title')}")
                self.test_results["passed"] += 1
            else:
                self.print_test("Get Risk Details", "FAIL", f"Error: {response}")
                self.test_results["failed"] += 1
        else:
            self.print_test("Create Risk", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
        
        # Get risk summary statistics
        response = self.make_request("GET", "/risks/stats/summary")
        if response and not response.get("error"):
            self.print_test("Risk Statistics", "PASS", 
                          f"Total: {response.get('total_risks', 0)}, "
                          f"High: {response.get('high_risks', 0)}")
            self.test_results["passed"] += 1
        else:
            self.print_test("Risk Statistics", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
    
    # ========== System Configuration Tests ==========
    
    def test_system_configuration(self):
        """Test system configuration management"""
        self.print_header("System Configuration Tests")
        
        # Create test configuration
        test_config = {
            "config_key": f"test.config.{self.generate_random_string(5)}",
            "config_value": "test_value",
            "config_type": "string",
            "category": "Testing",
            "display_name": "Test Configuration",
            "description": "Automated test configuration"
        }
        
        response = self.make_request("POST", "/system-config", json=test_config)
        if response and not response.get("error"):
            self.test_data["test_config_key"] = test_config["config_key"]
            self.print_test("Create Config", "PASS", f"Key: {test_config['config_key']}")
            self.test_results["passed"] += 1
            
            # Get configuration
            response = self.make_request("GET", f"/system-config/{test_config['config_key']}")
            if response and not response.get("error"):
                self.print_test("Get Config", "PASS", f"Value: {response.get('config_value')}")
                self.test_results["passed"] += 1
            else:
                self.print_test("Get Config", "FAIL", f"Error: {response}")
                self.test_results["failed"] += 1
        else:
            self.print_test("Create Config", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
        
        # List configurations
        response = self.make_request("GET", "/system-config")
        if response and isinstance(response, list):
            self.print_test("List Configs", "PASS", f"Found {len(response)} configs")
            self.test_results["passed"] += 1
        else:
            self.print_test("List Configs", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
    
    # ========== File Management Tests ==========
    
    def test_file_management(self):
        """Test file upload and management"""
        self.print_header("File Management Tests")
        
        # Create file category first
        category = {
            "name": f"Test Category {self.generate_random_string(5)}",
            "description": "Automated test category",
            "allowed_extensions": ["txt", "pdf", "jpg"],
            "max_file_size": 5242880  # 5MB
        }
        
        response = self.make_request("POST", "/file-management/categories", json=category)
        if response and not response.get("error"):
            category_id = response.get("id")
            self.print_test("Create File Category", "PASS", f"Category ID: {category_id}")
            self.test_results["passed"] += 1
            
            # Create test file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Test file content for NAPSA ERM system")
                test_file_path = f.name
            
            # Upload file (Note: This would need actual file upload in production)
            self.print_test("File Upload", "SKIP", "Requires multipart form data")
            self.test_results["skipped"] += 1
            
            # Clean up
            os.unlink(test_file_path)
        else:
            self.print_test("Create File Category", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
    
    # ========== Active Directory Tests ==========
    
    def test_ad_integration(self):
        """Test AD integration endpoints"""
        self.print_header("Active Directory Integration Tests")
        
        # Check AD status
        response = self.make_request("GET", "/ad/status")
        if response and not response.get("error"):
            ad_enabled = response.get("enabled", False)
            if ad_enabled:
                self.print_test("AD Status", "PASS", "AD integration is enabled")
                self.test_results["passed"] += 1
                
                # Test connection (admin only)
                response = self.make_request("POST", "/ad/test-connection")
                if response and not response.get("error"):
                    self.print_test("AD Connection", "PASS", "Connected successfully")
                    self.test_results["passed"] += 1
                else:
                    self.print_test("AD Connection", "FAIL", f"Error: {response}")
                    self.test_results["failed"] += 1
            else:
                self.print_test("AD Status", "SKIP", "AD integration is disabled")
                self.test_results["skipped"] += 1
        else:
            self.print_test("AD Status", "FAIL", f"Error: {response}")
            self.test_results["failed"] += 1
    
    # ========== Performance Tests ==========
    
    def test_performance(self):
        """Test API performance and response times"""
        self.print_header("Performance Tests")
        
        endpoints = [
            ("/risks", "GET", "List Risks"),
            ("/users", "GET", "List Users"),
            ("/system-config", "GET", "List Configs"),
            ("/risks/stats/summary", "GET", "Risk Statistics"),
        ]
        
        for endpoint, method, name in endpoints:
            start_time = time.time()
            response = self.make_request(method, endpoint)
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response and not response.get("error"):
                if elapsed_time < 500:  # Less than 500ms
                    status = "PASS"
                    self.test_results["passed"] += 1
                else:
                    status = "WARN"
                self.print_test(f"{name} Performance", status, f"Response time: {elapsed_time:.2f}ms")
            else:
                self.print_test(f"{name} Performance", "FAIL", f"Error: {response}")
                self.test_results["failed"] += 1
    
    # ========== Health Check Tests ==========
    
    def test_health_checks(self):
        """Test system health endpoints"""
        self.print_header("Health Check Tests")
        
        # Basic health check
        response = requests.get(f"{self.base_url}/health")
        if response.status_code == 200:
            self.print_test("Basic Health", "PASS", "System is healthy")
            self.test_results["passed"] += 1
        else:
            self.print_test("Basic Health", "FAIL", f"Status: {response.status_code}")
            self.test_results["failed"] += 1
        
        # API docs availability
        response = requests.get(f"{self.base_url}/docs")
        if response.status_code == 200:
            self.print_test("API Documentation", "PASS", "Swagger UI accessible")
            self.test_results["passed"] += 1
        else:
            self.print_test("API Documentation", "FAIL", f"Status: {response.status_code}")
            self.test_results["failed"] += 1
    
    # ========== Cleanup ==========
    
    def cleanup(self):
        """Clean up test data"""
        self.print_header("Cleanup")
        
        # Delete test risk
        if "test_risk_id" in self.test_data:
            response = self.make_request("DELETE", f"/risks/{self.test_data['test_risk_id']}")
            if response and not response.get("error"):
                self.print_test("Delete Test Risk", "PASS", "Cleaned up")
            else:
                self.print_test("Delete Test Risk", "FAIL", f"Error: {response}")
        
        # Delete test config
        if "test_config_key" in self.test_data:
            response = self.make_request("DELETE", f"/system-config/{self.test_data['test_config_key']}")
            if response and not response.get("error"):
                self.print_test("Delete Test Config", "PASS", "Cleaned up")
            else:
                self.print_test("Delete Test Config", "FAIL", f"Error: {response}")
    
    # ========== Main Test Runner ==========
    
    def run_all_tests(self):
        """Run complete test suite"""
        print(f"\n{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}NAPSA ERM System - API Test Suite")
        print(f"{Fore.MAGENTA}Target: {self.base_url}")
        print(f"{Fore.MAGENTA}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.MAGENTA}{'='*60}")
        
        # Run test categories
        if not self.test_authentication():
            print(f"\n{Fore.RED}Authentication failed - stopping tests")
            return self.generate_report()
        
        self.test_user_management()
        self.test_risk_management()
        self.test_system_configuration()
        self.test_file_management()
        self.test_ad_integration()
        self.test_performance()
        self.test_health_checks()
        self.cleanup()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        self.test_results["end_time"] = datetime.now()
        duration = (self.test_results["end_time"] - self.test_results["start_time"]).total_seconds()
        
        total_tests = (self.test_results["passed"] + 
                      self.test_results["failed"] + 
                      self.test_results["skipped"])
        
        pass_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        self.print_header("Test Results Summary")
        
        print(f"{Fore.GREEN}Passed:  {self.test_results['passed']}")
        print(f"{Fore.RED}Failed:  {self.test_results['failed']}")
        print(f"{Fore.YELLOW}Skipped: {self.test_results['skipped']}")
        print(f"{Fore.WHITE}Total:   {total_tests}")
        print(f"{Fore.CYAN}Pass Rate: {pass_rate:.1f}%")
        print(f"{Fore.BLUE}Duration: {duration:.2f} seconds")
        
        if self.test_results["errors"]:
            print(f"\n{Fore.RED}Errors:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        # Save report to file
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print(f"\n{Fore.WHITE}Detailed report saved to: {report_file}")
        
        # Return status code
        return 0 if self.test_results["failed"] == 0 else 1


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NAPSA ERM API Test Suite")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API (default: http://localhost:8000)")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Run tests
    test_suite = ERMTestSuite(base_url=args.url)
    exit_code = test_suite.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()