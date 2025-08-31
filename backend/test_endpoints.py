#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for NAPSA ERM API
Tests all endpoints and generates a detailed report
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import time
import traceback

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class EndpointTester:
    def __init__(self):
        self.results = {
            "total": 0,
            "working": 0,
            "failed": 0,
            "errors": [],
            "endpoints": []
        }
        self.token = None
        
    def log_success(self, message: str):
        print(f"{GREEN}✓ {message}{RESET}")
    
    def log_error(self, message: str):
        print(f"{RED}✗ {message}{RESET}")
    
    def log_info(self, message: str):
        print(f"{BLUE}ℹ {message}{RESET}")
    
    def log_warning(self, message: str):
        print(f"{YELLOW}⚠ {message}{RESET}")
    
    def test_server_status(self) -> bool:
        """Test if server is running"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            if response.status_code == 200:
                self.log_success("Server is running")
                return True
            else:
                self.log_error(f"Server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_error("Cannot connect to server at http://localhost:8000")
            return False
        except Exception as e:
            self.log_error(f"Server test failed: {e}")
            return False
    
    def get_openapi_spec(self) -> Dict:
        """Fetch OpenAPI specification"""
        try:
            response = requests.get(f"{API_URL}/openapi.json", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                self.log_error(f"Failed to fetch OpenAPI spec: {response.status_code}")
                return {}
        except Exception as e:
            self.log_error(f"Error fetching OpenAPI spec: {e}")
            return {}
    
    def extract_endpoints(self, openapi_spec: Dict) -> List[Dict]:
        """Extract all endpoints from OpenAPI spec"""
        endpoints = []
        paths = openapi_spec.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "tags": details.get("tags", []),
                        "requires_auth": "security" in details or "Authorization" in str(details.get("parameters", []))
                    })
        
        return endpoints
    
    def test_endpoint(self, endpoint: Dict) -> Tuple[bool, str]:
        """Test a single endpoint"""
        url = f"{API_URL}{endpoint['path']}"
        method = endpoint["method"]
        headers = {}
        
        # Add auth token if required
        if endpoint["requires_auth"] and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            # Handle path parameters
            if "{" in endpoint["path"]:
                # Skip endpoints with path parameters for now
                return None, "Skipped (requires path parameters)"
            
            # Make request based on method
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method == "POST":
                # Skip POST endpoints that require body
                return None, "Skipped (requires request body)"
            elif method in ["PUT", "PATCH", "DELETE"]:
                # Skip update/delete endpoints
                return None, "Skipped (requires existing resource)"
            else:
                return False, f"Unknown method: {method}"
            
            # Check response
            if response.status_code in [200, 201, 204]:
                return True, f"Success ({response.status_code})"
            elif response.status_code == 401:
                return False, "Unauthorized (401)"
            elif response.status_code == 403:
                return False, "Forbidden (403)"
            elif response.status_code == 404:
                return False, "Not Found (404)"
            elif response.status_code == 422:
                return False, "Validation Error (422)"
            elif response.status_code == 500:
                return False, f"Server Error (500)"
            else:
                return False, f"Status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection Error"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
    
    def test_all_endpoints(self):
        """Test all endpoints from OpenAPI spec"""
        # First check if server is running
        if not self.test_server_status():
            self.log_error("Server is not running. Please start the backend server first.")
            self.log_info("Run: cd /opt/napsa-erm-simple/backend && uvicorn app.main:app --reload")
            return
        
        # Get OpenAPI spec
        self.log_info("Fetching API specification...")
        spec = self.get_openapi_spec()
        if not spec:
            self.log_error("Could not fetch API specification")
            return
        
        # Extract endpoints
        endpoints = self.extract_endpoints(spec)
        self.log_info(f"Found {len(endpoints)} endpoints to test")
        
        # Test each endpoint
        print("\n" + "="*60)
        print("TESTING ENDPOINTS")
        print("="*60 + "\n")
        
        by_tag = {}
        for endpoint in endpoints:
            tags = endpoint.get("tags", ["Other"])
            for tag in tags:
                if tag not in by_tag:
                    by_tag[tag] = []
                by_tag[tag].append(endpoint)
        
        # Test endpoints by tag
        for tag in sorted(by_tag.keys()):
            print(f"\n{BLUE}Testing {tag} endpoints:{RESET}")
            print("-" * 40)
            
            for endpoint in by_tag[tag]:
                self.results["total"] += 1
                
                # Test the endpoint
                success, message = self.test_endpoint(endpoint)
                
                # Store result
                result = {
                    "path": endpoint["path"],
                    "method": endpoint["method"],
                    "tag": tag,
                    "summary": endpoint["summary"],
                    "success": success,
                    "message": message
                }
                self.results["endpoints"].append(result)
                
                # Display result
                if success is True:
                    self.results["working"] += 1
                    self.log_success(f"{endpoint['method']:6} {endpoint['path']:40} - {message}")
                elif success is False:
                    self.results["failed"] += 1
                    self.log_error(f"{endpoint['method']:6} {endpoint['path']:40} - {message}")
                else:
                    # Skipped
                    print(f"{YELLOW}⊘{RESET} {endpoint['method']:6} {endpoint['path']:40} - {message}")
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("TEST REPORT")
        print("="*60)
        
        # Summary
        print(f"\n{BLUE}Summary:{RESET}")
        print(f"Total Endpoints: {self.results['total']}")
        print(f"Working: {GREEN}{self.results['working']}{RESET}")
        print(f"Failed: {RED}{self.results['failed']}{RESET}")
        print(f"Skipped: {YELLOW}{self.results['total'] - self.results['working'] - self.results['failed']}{RESET}")
        
        # Success rate
        if self.results['working'] + self.results['failed'] > 0:
            success_rate = (self.results['working'] / (self.results['working'] + self.results['failed'])) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Failed endpoints
        failed = [e for e in self.results["endpoints"] if e["success"] is False]
        if failed:
            print(f"\n{RED}Failed Endpoints:{RESET}")
            for endpoint in failed:
                print(f"  - {endpoint['method']} {endpoint['path']}: {endpoint['message']}")
        
        # Working endpoints by tag
        working = [e for e in self.results["endpoints"] if e["success"] is True]
        if working:
            print(f"\n{GREEN}Working Endpoints by Module:{RESET}")
            by_tag = {}
            for endpoint in working:
                tag = endpoint["tag"]
                if tag not in by_tag:
                    by_tag[tag] = 0
                by_tag[tag] += 1
            
            for tag, count in sorted(by_tag.items()):
                print(f"  - {tag}: {count} endpoints")
        
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n{BLUE}Detailed report saved to: {report_file}{RESET}")
    
    def run(self):
        """Run all tests"""
        print(f"\n{BLUE}╔══════════════════════════════════════════╗{RESET}")
        print(f"{BLUE}║   NAPSA ERM API Endpoint Testing Suite   ║{RESET}")
        print(f"{BLUE}╚══════════════════════════════════════════╝{RESET}")
        print(f"\nStarting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            self.test_all_endpoints()
            self.generate_report()
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Testing interrupted by user{RESET}")
        except Exception as e:
            print(f"\n{RED}Testing failed with error: {e}{RESET}")
            traceback.print_exc()
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    tester = EndpointTester()
    tester.run()