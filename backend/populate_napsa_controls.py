"""
Populate NAPSA-specific controls for testing the risk calculation integration
"""
import requests
import json
from datetime import datetime, timedelta
import uuid

# Configuration
API_BASE_URL = "http://localhost:58001/api/v1"
USERNAME = "admin"
PASSWORD = "admin@123"

def login():
    """Login and get access token"""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def create_control(token, control_data):
    """Create a control"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/controls/",
        headers=headers,
        json=control_data
    )
    
    if response.status_code in [200, 201]:
        control = response.json()
        print(f"✓ Created control: {control['name']}")
        return control
    else:
        print(f"✗ Failed to create control: {response.text}")
        return None

def main():
    # Login
    token = login()
    if not token:
        print("Failed to authenticate")
        return
    
    print("\n=== Creating NAPSA Controls ===\n")
    
    # Define NAPSA-specific controls
    controls = [
        # Investment Controls
        {
            "name": "Investment Policy Compliance Review",
            "description": "Quarterly review of investment decisions against approved investment policy and guidelines",
            "type": "preventive",
            "control_owner": "Chief Investment Officer",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Quarterly",
            "effectiveness_rating": 85.0,
            "cost_of_control": 50000.0
        },
        {
            "name": "Investment Risk Monitoring System",
            "description": "Real-time monitoring of portfolio risk metrics including VaR, duration, and concentration limits",
            "type": "detective",
            "control_owner": "Risk Management Department",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Monthly",
            "effectiveness_rating": 90.0,
            "cost_of_control": 120000.0
        },
        {
            "name": "Pre-Investment Due Diligence",
            "description": "Comprehensive due diligence process for all investments above ZMW 10 million",
            "type": "preventive",
            "control_owner": "Investment Committee",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Per Transaction",
            "effectiveness_rating": 88.0,
            "cost_of_control": 75000.0
        },
        
        # Compliance Controls
        {
            "name": "Regulatory Compliance Monitoring",
            "description": "Automated monitoring of compliance with PIA regulations and reporting requirements",
            "type": "detective",
            "control_owner": "Compliance Officer",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Monthly",
            "effectiveness_rating": 92.0,
            "cost_of_control": 60000.0
        },
        {
            "name": "Member Contribution Reconciliation",
            "description": "Monthly reconciliation of member contributions against employer remittances",
            "type": "detective",
            "control_owner": "Finance Department",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Monthly",
            "effectiveness_rating": 95.0,
            "cost_of_control": 40000.0
        },
        
        # IT Security Controls
        {
            "name": "Multi-Factor Authentication",
            "description": "MFA required for all system access to critical pension management systems",
            "type": "preventive",
            "control_owner": "IT Security Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Quarterly",
            "effectiveness_rating": 94.0,
            "cost_of_control": 30000.0
        },
        {
            "name": "Data Encryption at Rest",
            "description": "AES-256 encryption for all member data and financial records at rest",
            "type": "preventive",
            "control_owner": "IT Security Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Annual",
            "effectiveness_rating": 98.0,
            "cost_of_control": 45000.0
        },
        {
            "name": "Security Incident Response Plan",
            "description": "Documented and tested incident response procedures for cybersecurity events",
            "type": "corrective",
            "control_owner": "CISO",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Semi-Annual",
            "effectiveness_rating": 80.0,
            "cost_of_control": 35000.0
        },
        
        # Operational Controls
        {
            "name": "Benefit Payment Verification",
            "description": "Two-level approval for all benefit payments above ZMW 100,000",
            "type": "preventive",
            "control_owner": "Benefits Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Per Transaction",
            "effectiveness_rating": 96.0,
            "cost_of_control": 25000.0
        },
        {
            "name": "Member Data Quality Checks",
            "description": "Automated data quality validation for member records and contribution history",
            "type": "detective",
            "control_owner": "Data Management Team",
            "implementation_status": "Partially Implemented",
            "testing_frequency": "Weekly",
            "effectiveness_rating": 75.0,
            "cost_of_control": 55000.0
        },
        {
            "name": "Business Continuity Testing",
            "description": "Annual testing of BCP and disaster recovery procedures",
            "type": "corrective",
            "control_owner": "Operations Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Annual",
            "effectiveness_rating": 82.0,
            "cost_of_control": 70000.0
        },
        
        # Fraud Prevention Controls
        {
            "name": "Fraud Detection Analytics",
            "description": "Machine learning-based fraud detection for suspicious transactions and claims",
            "type": "detective",
            "control_owner": "Fraud Prevention Unit",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Continuous",
            "effectiveness_rating": 87.0,
            "cost_of_control": 150000.0
        },
        {
            "name": "Segregation of Duties Matrix",
            "description": "Enforced segregation of duties for critical financial processes",
            "type": "preventive",
            "control_owner": "Internal Audit",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Quarterly",
            "effectiveness_rating": 91.0,
            "cost_of_control": 20000.0
        },
        {
            "name": "Vendor Payment Controls",
            "description": "Triple approval and verification for vendor payments above ZMW 500,000",
            "type": "preventive",
            "control_owner": "Procurement Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Per Transaction",
            "effectiveness_rating": 93.0,
            "cost_of_control": 30000.0
        },
        
        # Compensating Controls
        {
            "name": "Manual Investment Review",
            "description": "Manual review process when automated investment monitoring system is unavailable",
            "type": "compensating",
            "control_owner": "Investment Team",
            "implementation_status": "Documented",
            "testing_frequency": "As Needed",
            "effectiveness_rating": 70.0,
            "cost_of_control": 15000.0
        },
        {
            "name": "Alternative Benefit Calculation",
            "description": "Manual benefit calculation procedures when primary system is unavailable",
            "type": "compensating",
            "control_owner": "Benefits Department",
            "implementation_status": "Documented",
            "testing_frequency": "Annual",
            "effectiveness_rating": 65.0,
            "cost_of_control": 10000.0
        }
    ]
    
    created_controls = []
    for control_data in controls:
        control = create_control(token, control_data)
        if control:
            created_controls.append(control)
    
    print(f"\n✅ Successfully created {len(created_controls)} controls")
    
    # Map some controls to risks (if risks exist)
    print("\n=== Mapping Controls to Risks ===\n")
    
    # Get list of risks
    headers = {"Authorization": f"Bearer {token}"}
    risks_response = requests.get(f"{API_BASE_URL}/risks/", headers=headers)
    
    if risks_response.status_code == 200:
        risks_data = risks_response.json()
        risks = risks_data.get("data", [])[:5]  # Get first 5 risks
        
        if risks and created_controls:
            # Map controls to risks based on risk type
            mappings = [
                # Map investment controls to first risk
                {
                    "risk_id": risks[0]["id"] if risks else None,
                    "control_ids": [c["id"] for c in created_controls[:3]],  # Investment controls
                    "coverage": [80, 90, 85]
                },
                # Map compliance controls to second risk
                {
                    "risk_id": risks[1]["id"] if len(risks) > 1 else None,
                    "control_ids": [c["id"] for c in created_controls[3:5]],  # Compliance controls
                    "coverage": [95, 90]
                },
                # Map IT controls to third risk
                {
                    "risk_id": risks[2]["id"] if len(risks) > 2 else None,
                    "control_ids": [c["id"] for c in created_controls[5:8]],  # IT controls
                    "coverage": [100, 95, 80]
                },
                # Map operational controls to fourth risk
                {
                    "risk_id": risks[3]["id"] if len(risks) > 3 else None,
                    "control_ids": [c["id"] for c in created_controls[8:11]],  # Operational controls
                    "coverage": [90, 75, 85]
                },
                # Map fraud controls to fifth risk
                {
                    "risk_id": risks[4]["id"] if len(risks) > 4 else None,
                    "control_ids": [c["id"] for c in created_controls[11:14]],  # Fraud controls
                    "coverage": [95, 100, 90]
                }
            ]
            
            for mapping in mappings:
                if mapping["risk_id"]:
                    risk = next((r for r in risks if r["id"] == mapping["risk_id"]), None)
                    if risk:
                        print(f"\nMapping controls to risk: {risk['title']}")
                        for i, control_id in enumerate(mapping["control_ids"]):
                            map_data = {
                                "risk_id": mapping["risk_id"],
                                "control_id": control_id,
                                "coverage_percentage": mapping["coverage"][i],
                                "criticality": "High" if mapping["coverage"][i] >= 90 else "Medium"
                            }
                            
                            response = requests.post(
                                f"{API_BASE_URL}/controls/map-to-risk",
                                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                json=map_data
                            )
                            
                            if response.status_code in [200, 201]:
                                result = response.json()
                                print(f"  ✓ Mapped control to risk")
                                if "risk_update" in result:
                                    update = result["risk_update"]
                                    print(f"    - New residual risk: {update.get('new_residual_risk', 'N/A')}")
                                    print(f"    - Control effectiveness: {update.get('aggregate_control_effectiveness', 'N/A')}%")
                            else:
                                print(f"  ✗ Failed to map control: {response.text[:100]}")
    
    print("\n=== Control Population Complete ===")

if __name__ == "__main__":
    main()