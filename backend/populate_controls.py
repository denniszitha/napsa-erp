#!/usr/bin/env python3
"""
Populate controls table with sample data for NAPSA
"""

from app.core.database import SessionLocal
from app.models.control import Control, ControlType, ControlStatus
from datetime import datetime, timedelta
import uuid

def populate_controls():
    db = SessionLocal()
    
    # Sample controls data aligned with NAPSA's risk management framework
    controls_data = [
        # Preventive Controls
        {
            "name": "Access Control Policy",
            "description": "Comprehensive access control policy to prevent unauthorized access to sensitive pension data and systems",
            "type": ControlType.preventive,
            "status": ControlStatus.effective,
            "control_owner": "IT Security Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Quarterly",
            "effectiveness_rating": 85.0,
            "cost_of_control": 50000.00
        },
        {
            "name": "Investment Limit Controls",
            "description": "Automated controls to prevent investment exposures exceeding regulatory and internal limits",
            "type": ControlType.preventive,
            "status": ControlStatus.effective,
            "control_owner": "Investment Risk Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Monthly",
            "effectiveness_rating": 90.0,
            "cost_of_control": 75000.00
        },
        {
            "name": "Segregation of Duties",
            "description": "Clear separation of duties in critical financial processes to prevent fraud and errors",
            "type": ControlType.preventive,
            "status": ControlStatus.effective,
            "control_owner": "Chief Finance Officer",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Annual",
            "effectiveness_rating": 88.0,
            "cost_of_control": 30000.00
        },
        
        # Detective Controls
        {
            "name": "Transaction Monitoring System",
            "description": "Real-time monitoring of all financial transactions for anomalies and suspicious patterns",
            "type": ControlType.detective,
            "status": ControlStatus.effective,
            "control_owner": "Compliance Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Continuous",
            "effectiveness_rating": 92.0,
            "cost_of_control": 120000.00
        },
        {
            "name": "Compliance Audit Program",
            "description": "Regular internal audits to detect compliance violations and control weaknesses",
            "type": ControlType.detective,
            "status": ControlStatus.effective,
            "control_owner": "Chief Audit Executive",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Quarterly",
            "effectiveness_rating": 87.0,
            "cost_of_control": 80000.00
        },
        {
            "name": "Cybersecurity Monitoring",
            "description": "24/7 security monitoring to detect and alert on potential cyber threats",
            "type": ControlType.detective,
            "status": ControlStatus.effective,
            "control_owner": "CISO",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Continuous",
            "effectiveness_rating": 89.0,
            "cost_of_control": 150000.00
        },
        
        # Corrective Controls
        {
            "name": "Incident Response Plan",
            "description": "Comprehensive incident response procedures to address and remediate security incidents",
            "type": ControlType.corrective,
            "status": ControlStatus.effective,
            "control_owner": "Risk Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Semi-Annual",
            "effectiveness_rating": 83.0,
            "cost_of_control": 45000.00
        },
        {
            "name": "Business Continuity Plan",
            "description": "Detailed BCP to ensure critical operations can continue during disruptions",
            "type": ControlType.corrective,
            "status": ControlStatus.partially_effective,
            "control_owner": "Operations Manager",
            "implementation_status": "Under Review",
            "testing_frequency": "Annual",
            "effectiveness_rating": 78.0,
            "cost_of_control": 100000.00
        },
        {
            "name": "Data Backup and Recovery",
            "description": "Automated backup systems with tested recovery procedures for critical data",
            "type": ControlType.corrective,
            "status": ControlStatus.effective,
            "control_owner": "IT Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Monthly",
            "effectiveness_rating": 95.0,
            "cost_of_control": 60000.00
        },
        
        # Compensating Controls
        {
            "name": "Manual Review Process",
            "description": "Manual review of high-value transactions when automated controls are unavailable",
            "type": ControlType.compensating,
            "status": ControlStatus.effective,
            "control_owner": "Finance Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Weekly",
            "effectiveness_rating": 75.0,
            "cost_of_control": 25000.00
        },
        {
            "name": "Enhanced Monitoring",
            "description": "Enhanced monitoring procedures for legacy systems with limited control capabilities",
            "type": ControlType.compensating,
            "status": ControlStatus.partially_effective,
            "control_owner": "IT Security Manager",
            "implementation_status": "Partially Implemented",
            "testing_frequency": "Monthly",
            "effectiveness_rating": 70.0,
            "cost_of_control": 35000.00
        },
        
        # Additional Controls
        {
            "name": "Regulatory Compliance Framework",
            "description": "Comprehensive framework ensuring adherence to all pension regulatory requirements",
            "type": ControlType.preventive,
            "status": ControlStatus.effective,
            "control_owner": "Chief Compliance Officer",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Quarterly",
            "effectiveness_rating": 91.0,
            "cost_of_control": 85000.00
        },
        {
            "name": "Vendor Risk Management",
            "description": "Due diligence and ongoing monitoring of third-party service providers",
            "type": ControlType.preventive,
            "status": ControlStatus.effective,
            "control_owner": "Procurement Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Annual",
            "effectiveness_rating": 82.0,
            "cost_of_control": 40000.00
        },
        {
            "name": "Employee Training Program",
            "description": "Regular training on risk management, compliance, and security awareness",
            "type": ControlType.preventive,
            "status": ControlStatus.effective,
            "control_owner": "HR Manager",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Semi-Annual",
            "effectiveness_rating": 77.0,
            "cost_of_control": 55000.00
        },
        {
            "name": "Investment Risk Analytics",
            "description": "Advanced analytics platform for monitoring investment risk metrics and exposures",
            "type": ControlType.detective,
            "status": ControlStatus.effective,
            "control_owner": "Chief Investment Officer",
            "implementation_status": "Fully Implemented",
            "testing_frequency": "Daily",
            "effectiveness_rating": 93.0,
            "cost_of_control": 200000.00
        }
    ]
    
    print("Populating controls table...")
    controls_created = 0
    
    for control_data in controls_data:
        try:
            # Add timestamps
            control_data["last_test_date"] = datetime.now() - timedelta(days=30)
            control_data["next_test_date"] = datetime.now() + timedelta(days=60)
            control_data["created_at"] = datetime.now()
            control_data["updated_at"] = datetime.now()
            
            control = Control(**control_data)
            db.add(control)
            controls_created += 1
            print(f"  ✓ Created control: {control_data['name']}")
        except Exception as e:
            print(f"  ✗ Error creating control {control_data['name']}: {e}")
    
    try:
        db.commit()
        print(f"\n✓ Successfully created {controls_created} controls")
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error committing controls: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate_controls()