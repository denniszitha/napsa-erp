"""
Create sample data for testing Phase 2 features
"""
import sys
sys.path.append('.')

from datetime import datetime, timedelta
import random
from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.risk import Risk, RiskCategory, RiskStatus
from app.models.control import Control, ControlType, ControlStatus
from app.models.kri import KeyRiskIndicator, KRIStatus
from app.core.security import get_password_hash

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("Creating sample data for Phase 2 features...")

# Create sample users if they don't exist
users_data = [
    {
        "email": "john.doe@napsa.co.zm",
        "username": "johndoe",
        "full_name": "John Doe",
        "role": UserRole.risk_manager,
        "department": "Risk Management"
    },
    {
        "email": "jane.smith@napsa.co.zm",
        "username": "janesmith",
        "full_name": "Jane Smith",
        "role": UserRole.risk_owner,
        "department": "Operations"
    }
]

created_users = []
for user_data in users_data:
    user = db.query(User).filter(User.username == user_data["username"]).first()
    if not user:
        user = User(
            **user_data,
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    created_users.append(user)

# Create sample risks if they don't exist
risks_data = [
    {
        "title": "Cybersecurity Breach Risk",
        "description": "Risk of unauthorized access to sensitive data",
        "category": RiskCategory.cyber,
        "status": RiskStatus.active,
        "likelihood": 3,
        "impact": 5,
        "department": "IT"
    },
    {
        "title": "Regulatory Compliance Risk",
        "description": "Risk of non-compliance with new regulations",
        "category": RiskCategory.compliance,
        "status": RiskStatus.active,
        "likelihood": 2,
        "impact": 4,
        "department": "Legal"
    },
    {
        "title": "Market Volatility Risk",
        "description": "Risk from market fluctuations affecting investments",
        "category": RiskCategory.financial,
        "status": RiskStatus.active,
        "likelihood": 4,
        "impact": 4,
        "department": "Finance"
    }
]

created_risks = []
for risk_data in risks_data:
    # Check if risk already exists
    existing_risk = db.query(Risk).filter(Risk.title == risk_data["title"]).first()
    if not existing_risk:
        risk = Risk(
            **risk_data,
            risk_owner_id=random.choice(created_users).id,
            inherent_risk_score=risk_data["likelihood"] * risk_data["impact"]
        )
        db.add(risk)
        db.commit()
        db.refresh(risk)
        created_risks.append(risk)
    else:
        created_risks.append(existing_risk)

# Create sample controls
controls_data = [
    {
        "name": "Firewall Configuration",
        "description": "Network firewall to prevent unauthorized access",
        "type": ControlType.preventive,
        "status": ControlStatus.effective,
        "control_owner": "IT Security Team",
        "implementation_status": "Fully Implemented",
        "testing_frequency": "Monthly",
        "effectiveness_rating": 90.0
    },
    {
        "name": "Compliance Monitoring System",
        "description": "Automated system to monitor regulatory compliance",
        "type": ControlType.detective,
        "status": ControlStatus.effective,
        "control_owner": "Compliance Team",
        "implementation_status": "Fully Implemented",
        "testing_frequency": "Weekly",
        "effectiveness_rating": 85.0
    },
    {
        "name": "Investment Diversification Policy",
        "description": "Policy to diversify investment portfolio",
        "type": ControlType.preventive,
        "status": ControlStatus.partially_effective,
        "control_owner": "Investment Team",
        "implementation_status": "In Progress",
        "testing_frequency": "Quarterly",
        "effectiveness_rating": 70.0
    }
]

for control_data in controls_data:
    # Check if control already exists
    existing_control = db.query(Control).filter(Control.name == control_data["name"]).first()
    if not existing_control:
        control = Control(**control_data)
        db.add(control)
        db.commit()

# Create sample KRIs
kris_data = [
    {
        "name": "Failed Login Attempts",
        "description": "Number of failed login attempts per day",
        "metric_type": "count",
        "lower_threshold": 0,
        "upper_threshold": 100,
        "target_value": 20,
        "current_value": 45,
        "status": KRIStatus.warning,
        "measurement_frequency": "Daily",
        "data_source": "Security Logs",
        "responsible_party": "IT Security"
    },
    {
        "name": "Compliance Score",
        "description": "Overall compliance score percentage",
        "metric_type": "percentage",
        "lower_threshold": 80,
        "upper_threshold": 100,
        "target_value": 95,
        "current_value": 92,
        "status": KRIStatus.normal,
        "measurement_frequency": "Weekly",
        "data_source": "Compliance System",
        "responsible_party": "Compliance Officer"
    },
    {
        "name": "Portfolio Volatility",
        "description": "Investment portfolio volatility index",
        "metric_type": "index",
        "lower_threshold": 0,
        "upper_threshold": 30,
        "target_value": 15,
        "current_value": 28,
        "status": KRIStatus.critical,
        "measurement_frequency": "Daily",
        "data_source": "Market Data Feed",
        "responsible_party": "Investment Manager"
    }
]

for i, kri_data in enumerate(kris_data):
    if i < len(created_risks):
        # Check if KRI already exists for this risk
        existing_kri = db.query(KeyRiskIndicator).filter(
            KeyRiskIndicator.name == kri_data["name"],
            KeyRiskIndicator.risk_id == created_risks[i].id
        ).first()
        if not existing_kri:
            kri = KeyRiskIndicator(
                **kri_data,
                risk_id=created_risks[i].id
            )
            db.add(kri)
            db.commit()

print("\n✅ Sample data created successfully!")
print("\n📊 Created:")
print(f"- {len(created_users)} users")
print(f"- {len(created_risks)} risks")
print(f"- {len(controls_data)} controls")
print(f"- {len(kris_data)} KRIs")
print("\n🔐 You can now login with:")
print("- Username: admin, Password: admin123 (Admin)")
print("- Username: johndoe, Password: password123 (Risk Manager)")
print("- Username: janesmith, Password: password123 (Risk Owner)")

db.close()
