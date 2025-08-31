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
from colorama import init, Fore, Style

# Initialize colorama for Windows compatibility
init()

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Test with different users
TEST_USERS = {
    "admin": {"username": "admin", "password": "admin123"},
    "director": {"username": "director.general", "password": "napsa2025"},
    "cro": {"username": "chief.risk", "password": "napsa2025"}
}

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
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
        self.test_results["passed"] += 1
    
    def log_error(self, message: str):
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
        self.test_results["failed"] += 1
    
    def log_info(self, message: str):
        print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")
    
    def log_warning(self, message: str):
        print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")
    
    def log_skip(self, message: str):
        print(f"{Fore.CYAN}⏭ {message}{Style.RESET_ALL}")
        self.test_results["skipped"] += 1
    
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
                return response.json() if response.text else None
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
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Authentication Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
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
            self.test_results["passed"] += 1
        else:
            self.log_error(f"POST /auth/login - Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            self.test_results["failed"] += 1
            return False
        
        return True
    
    def test_user_endpoints(self):
        """Test user management endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing User Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # Get current user
        user_data = self.test_endpoint("GET", "/users/me", description="Get current user")
        if user_data:
            self.user_id = user_data.get("id")
            self.log_info(f"Current user: {user_data.get('username')} (ID: {self.user_id})")
        
        # List all users
        users = self.test_endpoint("GET", "/users/", description="List all users")
        if users:
            self.log_info(f"Total users in system: {len(users)}")
        
        # Get specific user (if we have users)
        if users and len(users) > 0:
            test_user_id = users[0]['id']
            self.test_endpoint("GET", f"/users/{test_user_id}", description="Get specific user")
    
    def test_risk_endpoints(self):
        """Test risk management endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Risk Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # List risks
        risks = self.test_endpoint("GET", "/risks/", description="List all risks")
        if risks:
            self.log_info(f"Total risks in system: {len(risks)}")
            
            if len(risks) > 0:
                # Test with existing risk
                risk_id = risks[0]['id']
                self.created_entities['risks'].append(risk_id)
                
                # Get specific risk
                self.test_endpoint("GET", f"/risks/{risk_id}", description="Get specific risk")
                
                # Get risk history
                self.test_endpoint("GET", f"/risks/{risk_id}/history", description="Get risk history")
                
                # Update risk
                update_data = {"likelihood": 4, "impact": 4}
                self.test_endpoint("PATCH", f"/risks/{risk_id}", data=update_data, 
                                 description="Update risk")
        
        # Create new risk
        new_risk = {
            "title": f"Test API Risk {int(time.time())}",
            "description": "Risk created during API testing",
            "category": "operational",
            "likelihood": 3,
            "impact": 3,
            "owner_id": self.user_id,
            "department": "IT"
        }
        created_risk = self.test_endpoint("POST", "/risks/", data=new_risk, 
                                        expected_status=[201, 200], description="Create new risk")
        if created_risk:
            self.created_entities['risks'].append(created_risk['id'])
    
    def test_assessment_endpoints(self):
        """Test assessment endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Assessment Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # List assessments
        assessments = self.test_endpoint("GET", "/assessments/", description="List all assessments")
        if assessments:
            self.log_info(f"Total assessments: {len(assessments)}")
        
        # Create assessment if we have a risk
        if self.created_entities['risks']:
            risk_id = self.created_entities['risks'][0]
            new_assessment = {
                "risk_id": risk_id,
                "likelihood": 3,
                "impact": 4,
                "comments": "Test assessment via API"
            }
            created = self.test_endpoint("POST", "/assessments/", data=new_assessment,
                                       expected_status=[201, 200], description="Create assessment")
            if created:
                self.created_entities['assessments'].append(created['id'])
    
    def test_control_endpoints(self):
        """Test control endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Control Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # List controls
        controls = self.test_endpoint("GET", "/controls/", description="List all controls")
        if controls:
            self.log_info(f"Total controls: {len(controls)}")
        
        # Test control effectiveness
        self.test_endpoint("GET", "/controls/effectiveness", description="Get control effectiveness")
        
        # Create control
        new_control = {
            "name": f"Test Control {int(time.time())}",
            "description": "Control created during API testing",
            "control_type": "preventive",
            "implementation_status": "planned",
            "owner_id": self.user_id,
            "effectiveness": 80
        }
        created = self.test_endpoint("POST", "/controls/", data=new_control,
                                   expected_status=[201, 200], description="Create control")
        if created:
            control_id = created['id']
            self.created_entities['controls'].append(control_id)
            
            # Link control to risk if we have both
            if self.created_entities['risks']:
                risk_id = self.created_entities['risks'][0]
                self.test_endpoint("POST", f"/controls/{control_id}/risks/{risk_id}",
                                 expected_status=[200, 201, 204],
                                 description="Link control to risk")
    
    def test_kri_endpoints(self):
        """Test KRI endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing KRI Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # List KRIs
        kris = self.test_endpoint("GET", "/kris/", description="List all KRIs")
        if kris:
            self.log_info(f"Total KRIs: {len(kris)}")
        
        # Get KRI dashboard
        self.test_endpoint("GET", "/kris/dashboard", description="Get KRI dashboard")
        
        # Get breached KRIs
        self.test_endpoint("GET", "/kris/breached", description="Get breached KRIs")
        
        # Create KRI if we have a risk
        if self.created_entities['risks']:
            risk_id = self.created_entities['risks'][0]
            new_kri = {
                "name": f"Test KRI {int(time.time())}",
                "description": "Test KRI for API testing",
                "risk_id": risk_id,
                "metric_type": "percentage",
                "threshold_lower": 10,
                "threshold_upper": 90,
                "current_value": 50,
                "frequency": "monthly",
                "owner_id": self.user_id
            }
            created = self.test_endpoint("POST", "/kris/", data=new_kri,
                                       expected_status=[201, 200], description="Create KRI")
            if created:
                kri_id = created['id']
                self.created_entities['kris'].append(kri_id)
                
                # Record measurement
                measurement = {
                    "value": 75,
                    "notes": "Test measurement"
                }
                self.test_endpoint("POST", f"/kris/{kri_id}/measurements", 
                                 data=measurement,
                                 expected_status=[201, 200],
                                 description="Record KRI measurement")
    
    def test_treatment_endpoints(self):
        """Test treatment endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Treatment Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # List treatments
        treatments = self.test_endpoint("GET", "/treatments/", description="List all treatments")
        
        # Get treatment plans
        self.test_endpoint("GET", "/treatments/plans", description="Get treatment plans")
        
        # Create treatment if we have a risk
        if self.created_entities['risks']:
            risk_id = self.created_entities['risks'][0]
            new_treatment = {
                "risk_id": risk_id,
                "strategy": "mitigate",
                "description": "Test treatment plan",
                "owner_id": self.user_id,
                "target_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "status": "planned"
            }
            created = self.test_endpoint("POST", "/treatments/", data=new_treatment,
                                       expected_status=[201, 200], description="Create treatment")
            if created:
                treatment_id = created['id']
                self.created_entities['treatments'].append(treatment_id)
    
    def test_incident_endpoints(self):
        """Test incident endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Incident Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # List incidents
        incidents = self.test_endpoint("GET", "/incidents/", description="List all incidents")
        
        # Get incident statistics
        self.test_endpoint("GET", "/incidents/stats", description="Get incident statistics")
        
        # Create incident
        new_incident = {
            "title": f"Test Incident {int(time.time())}",
            "description": "Test incident for API testing",
            "incident_type": "operational_failure",
            "severity": "medium",
            "status": "open",
            "reporter_id": self.user_id,
            "department": "IT"
        }
        created = self.test_endpoint("POST", "/incidents/", data=new_incident,
                                   expected_status=[201, 200], description="Create incident")
        if created:
            incident_id = created['id']
            self.created_entities['incidents'].append(incident_id)
    
    def test_compliance_endpoints(self):
        """Test compliance endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Compliance Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # List frameworks
        self.test_endpoint("GET", "/compliance/frameworks", description="List compliance frameworks")
        
        # Get compliance status
        self.test_endpoint("GET", "/compliance/status", description="Get compliance status")
        
        # List requirements
        self.test_endpoint("GET", "/compliance/requirements", description="List compliance requirements")
    
    def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Analytics Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # Risk analytics
        self.test_endpoint("GET", "/analytics/risk-summary", description="Get risk summary")
        self.test_endpoint("GET", "/analytics/risk-trends", description="Get risk trends")
        self.test_endpoint("GET", "/analytics/risk-heatmap", description="Get risk heatmap")
        self.test_endpoint("GET", "/analytics/department-risks", description="Get department risks")
        
        # KRI analytics
        self.test_endpoint("GET", "/analytics/kri-status", description="Get KRI status")
        
        # Control analytics
        self.test_endpoint("GET", "/analytics/control-effectiveness", description="Get control effectiveness")
        
        # Compliance analytics
        self.test_endpoint("GET", "/analytics/compliance-score", description="Get compliance score")
    
    def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Dashboard Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        self.test_endpoint("GET", "/dashboard/overview", description="Get dashboard overview")
        self.test_endpoint("GET", "/dashboard/stats", description="Get dashboard statistics")
        self.test_endpoint("GET", "/dashboard/recent-activities", description="Get recent activities")
        self.test_endpoint("GET", "/dashboard/my-tasks", description="Get my tasks")
        self.test_endpoint("GET", "/dashboard/risk-metrics", description="Get risk metrics")
    
    def test_report_endpoints(self):
        """Test report endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Report Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # Generate reports
        self.test_endpoint("GET", "/reports/risk-register", description="Generate risk register")
        self.test_endpoint("GET", "/reports/executive-summary", description="Generate executive summary")
        self.test_endpoint("GET", "/reports/compliance", description="Generate compliance report")
        
        # Note: PDF generation might require additional setup
        self.log_info("PDF report generation endpoints skipped (may require additional setup)")
    
    def test_audit_endpoints(self):
        """Test audit endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Audit Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        self.test_endpoint("GET", "/audit/logs", description="Get audit logs")
        self.test_endpoint("GET", "/audit/user-activities", description="Get user activities")
        self.test_endpoint("GET", "/audit/changes", description="Get recent changes")
    
    def test_data_exchange_endpoints(self):
        """Test data import/export endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Data Exchange Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # Export endpoints
        self.test_endpoint("GET", "/data-exchange/export/risks", 
                         description="Export risks to CSV")
        self.test_endpoint("GET", "/data-exchange/export/controls", 
                         description="Export controls to CSV")
        self.test_endpoint("GET", "/data-exchange/export/full", 
                         description="Export full backup")
        
        self.log_info("Import endpoints require file upload - skipping in basic test")
    
    def test_simulation_endpoints(self):
        """Test Monte Carlo simulation endpoints"""
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"Testing Simulation Endpoints")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # Run simulations
        self.test_endpoint("POST", "/simulation/monte-carlo", 
                         data={"iterations": 100},
                         expected_status=[200, 201],
                         description="Run Monte Carlo simulation")
        
        self.test_endpoint("GET", "/simulation/results", 
                         description="Get simulation results")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"Test Summary")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        total = sum(self.test_results.values())
        print(f"{Fore.GREEN}Passed: {self.test_results['passed']}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.test_results['failed']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Skipped: {self.test_results['skipped']}{Style.RESET_ALL}")
        print(f"Total: {total}")
        
        if self.test_results['failed'] == 0:
            print(f"\n{Fore.GREEN}✨ All tests passed! ✨{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠ Some tests failed. Check the output above for details.{Style.RESET_ALL}")
        
        # Print created entities
        print(f"\n{Fore.BLUE}Created Test Data:{Style.RESET_ALL}")
        for entity_type, ids in self.created_entities.items():
            if ids:
                print(f"  {entity_type}: {len(ids)} items")
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"{Fore.BLUE}{'='*60}")
        print(f"NAPSA ERM API Endpoint Tests")
        print(f"{'='*60}{Style.RESET_ALL}")
        print(f"Server: {BASE_URL}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test authentication first
        if not self.test_auth_endpoints():
            print(f"\n{Fore.RED}Authentication failed. Cannot continue with tests.{Style.RESET_ALL}")
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
        self.test_data_exchange_endpoints()
        self.test_simulation_endpoints()
        
        # Print summary
        self.print_summary()


def main():
    """Main function"""
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}Cannot connect to API at {BASE_URL}")
        print(f"Please ensure the server is running:")
        print(f"cd /opt/napsa-erm-simple/backend && uvicorn app.main:app --reload{Style.RESET_ALL}")
        sys.exit(1)
    
    # Install colorama if not available
    try:
        import colorama
    except ImportError:
        print("Installing colorama for colored output...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
        from colorama import init, Fore, Style
        init()
    
    # Run tests
    tester = ERMAPITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
