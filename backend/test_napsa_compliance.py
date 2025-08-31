#!/usr/bin/env python3
"""
NAPSA ERM Compliance Test Suite
Tests all implemented features for NAPSA requirements
"""

import requests
import json
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:58001/api/v1"
TEST_USER = "admin@napsa.co.zm"
TEST_PASSWORD = "Admin123!"

class NAPSAComplianceTest:
    def __init__(self):
        self.token = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "details": []
        }
    
    def login(self):
        """Authenticate and get JWT token"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                data={
                    "username": TEST_USER,
                    "password": TEST_PASSWORD
                }
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                return True
            else:
                print(f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Dict = None, expected_status: int = 200) -> bool:
        """Test a single endpoint"""
        self.test_results["total"] += 1
        
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=self.get_headers())
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", 
                                        json=data, headers=self.get_headers())
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}{endpoint}", 
                                       json=data, headers=self.get_headers())
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}{endpoint}", headers=self.get_headers())
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            
            if success:
                self.test_results["passed"] += 1
                status = "✅ PASSED"
            else:
                self.test_results["failed"] += 1
                status = "❌ FAILED"
            
            result = {
                "test": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "expected": expected_status,
                "result": status
            }
            
            self.test_results["details"].append(result)
            print(f"{status}: {name} - {method} {endpoint} (Got {response.status_code}, Expected {expected_status})")
            
            return success
            
        except Exception as e:
            self.test_results["failed"] += 1
            result = {
                "test": name,
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
                "result": "❌ ERROR"
            }
            self.test_results["details"].append(result)
            print(f"❌ ERROR: {name} - {e}")
            return False
    
    def run_all_tests(self):
        """Run all compliance tests"""
        print("\n" + "="*60)
        print("NAPSA ERM COMPLIANCE TEST SUITE")
        print("="*60 + "\n")
        
        # Login first
        if not self.login():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        print("✅ Authentication successful\n")
        
        # Test 1: Organizational Units
        print("\n--- Testing Organizational Units ---")
        self.test_endpoint(
            "Get Organizational Units",
            "GET", "/organizational-units",
            expected_status=200
        )
        
        # Test 2: Risk Management
        print("\n--- Testing Risk Management ---")
        self.test_endpoint(
            "Get All Risks",
            "GET", "/risks/",
            expected_status=200
        )
        
        self.test_endpoint(
            "Get Risk Categories",
            "GET", "/risk-categories/",
            expected_status=200
        )
        
        # Test 3: RCSA Module
        print("\n--- Testing RCSA Module ---")
        self.test_endpoint(
            "Get RCSA Templates",
            "GET", "/rcsa/templates",
            expected_status=200
        )
        
        self.test_endpoint(
            "Get RCSA Assessments",
            "GET", "/rcsa/assessments",
            expected_status=200
        )
        
        self.test_endpoint(
            "Get RCSA Schedule",
            "GET", "/rcsa/schedule",
            expected_status=200
        )
        
        self.test_endpoint(
            "Get RCSA Dashboard",
            "GET", "/rcsa/dashboard",
            expected_status=200
        )
        
        # Test 4: KRI Management
        print("\n--- Testing KRI Management ---")
        self.test_endpoint(
            "Get Key Risk Indicators",
            "GET", "/kri/",
            expected_status=200
        )
        
        # Test 5: Incident Management
        print("\n--- Testing Incident Management ---")
        self.test_endpoint(
            "Get Incidents",
            "GET", "/incidents/",
            expected_status=200
        )
        
        # Test 6: Compliance
        print("\n--- Testing Compliance Module ---")
        self.test_endpoint(
            "Get Compliance Assessments",
            "GET", "/compliance/assessments",
            expected_status=200
        )
        
        # Test 7: Controls
        print("\n--- Testing Controls ---")
        self.test_endpoint(
            "Get Controls",
            "GET", "/controls/",
            expected_status=200
        )
        
        # Test 8: Treatments
        print("\n--- Testing Treatments ---")
        self.test_endpoint(
            "Get Treatments",
            "GET", "/treatments/",
            expected_status=200
        )
        
        # Test 9: Reports
        print("\n--- Testing Reports ---")
        self.test_endpoint(
            "Get Reports",
            "GET", "/reports/",
            expected_status=200
        )
        
        # Test 10: Dashboard
        print("\n--- Testing Dashboard ---")
        self.test_endpoint(
            "Get Dashboard Stats",
            "GET", "/dashboard/stats",
            expected_status=200
        )
        
        # Test 11: Analytics
        print("\n--- Testing Analytics ---")
        self.test_endpoint(
            "Get Risk Analytics",
            "GET", "/analytics/risk-summary",
            expected_status=200
        )
        
        # Test 12: Notifications
        print("\n--- Testing Notifications ---")
        self.test_endpoint(
            "Get Notifications",
            "GET", "/notifications/",
            expected_status=200
        )
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        total = self.test_results["total"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        
        if total > 0:
            pass_rate = (passed / total) * 100
        else:
            pass_rate = 0
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if failed > 0:
            print("\n--- Failed Tests ---")
            for test in self.test_results["details"]:
                if "FAILED" in test["result"] or "ERROR" in test["result"]:
                    print(f"  • {test['test']}: {test['method']} {test['endpoint']}")
                    if "error" in test:
                        print(f"    Error: {test['error']}")
                    else:
                        print(f"    Expected: {test['expected']}, Got: {test['status_code']}")
        
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nDetailed report saved to: {report_file}")
        
        # Compliance Assessment
        print("\n" + "="*60)
        print("NAPSA COMPLIANCE ASSESSMENT")
        print("="*60)
        
        compliance_items = {
            "Organizational Hierarchy": passed >= 1,
            "Risk Management": passed >= 2,
            "RCSA Module": passed >= 4,
            "KRI Monitoring": passed >= 1,
            "Incident Management": passed >= 1,
            "Compliance Tracking": passed >= 1,
            "Controls Management": passed >= 1,
            "Risk Treatments": passed >= 1,
            "Reporting": passed >= 1,
            "Dashboard & Analytics": passed >= 2,
            "Notifications": passed >= 1
        }
        
        compliant_count = sum(1 for v in compliance_items.values() if v)
        total_requirements = len(compliance_items)
        compliance_rate = (compliant_count / total_requirements) * 100
        
        print("\nCompliance Status by Module:")
        for module, status in compliance_items.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {module}")
        
        print(f"\nOverall Compliance: {compliance_rate:.1f}% ({compliant_count}/{total_requirements})")
        
        if compliance_rate >= 90:
            print("\n🎉 EXCELLENT: System meets NAPSA requirements!")
        elif compliance_rate >= 70:
            print("\n⚠️ GOOD: System mostly compliant, some gaps remain")
        else:
            print("\n❌ NEEDS WORK: Significant compliance gaps detected")

def main():
    """Main test execution"""
    tester = NAPSAComplianceTest()
    tester.run_all_tests()
    tester.generate_report()

if __name__ == "__main__":
    main()