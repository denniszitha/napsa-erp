#!/usr/bin/env python3
"""
NAPSA ERM Database Seeder
Seeds the database with NAPSA-specific risk management data
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import json
from uuid import uuid4
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from passlib.context import CryptContext

# Import models from their respective files
from app.models.user import User
from app.models.risk import Risk
from app.models.control import Control, RiskControl
from app.models.assessment import RiskAssessment
from app.models.kri import KeyRiskIndicator, KRIMeasurement
from app.models.workflow import RiskTreatment
from app.models.audit import AuditLog
from app.models.incident import Incident, IncidentTimelineEvent
from app.models.compliance import ComplianceRequirement, ComplianceMapping

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Database connection - using the correct credentials
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/napsa_erm")
if not DATABASE_URL.startswith('postgresql+asyncpg://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# NAPSA-specific departments
NAPSA_DEPARTMENTS = [
    "Benefits Administration",
    "Contributions and Compliance", 
    "Investments",
    "Information Technology",
    "Finance",
    "Human Resources",
    "Legal and Corporate Affairs",
    "Internal Audit",
    "Risk and Compliance",
    "Operations",
    "Corporate Planning",
    "Public Relations"
]

# NAPSA-specific users
NAPSA_USERS = [
    {
        "username": "director.general",
        "email": "dg@napsa.co.zm",
        "full_name": "Director General",
        "role": "admin",
        "department": "Executive",
        "password": "napsa2025"
    },
    {
        "username": "chief.risk",
        "email": "cro@napsa.co.zm", 
        "full_name": "Chief Risk Officer",
        "role": "risk_manager",
        "department": "Risk and Compliance",
        "password": "napsa2025"
    },
    {
        "username": "head.investments",
        "email": "investments@napsa.co.zm",
        "full_name": "Head of Investments",
        "role": "risk_owner",
        "department": "Investments",
        "password": "napsa2025"
    },
    {
        "username": "head.benefits",
        "email": "benefits@napsa.co.zm",
        "full_name": "Head of Benefits",
        "role": "risk_owner", 
        "department": "Benefits Administration",
        "password": "napsa2025"
    },
    {
        "username": "head.it",
        "email": "it@napsa.co.zm",
        "full_name": "Head of IT",
        "role": "risk_owner",
        "department": "Information Technology",
        "password": "napsa2025"
    },
    {
        "username": "internal.auditor",
        "email": "audit@napsa.co.zm",
        "full_name": "Chief Internal Auditor",
        "role": "auditor",
        "department": "Internal Audit",
        "password": "napsa2025"
    },
    {
        "username": "compliance.officer",
        "email": "compliance@napsa.co.zm",
        "full_name": "Compliance Officer",
        "role": "risk_manager",
        "department": "Risk and Compliance",
        "password": "napsa2025"
    }
]

# NAPSA-specific risks
NAPSA_RISKS = [
    # Strategic Risks
    {
        "title": "Investment Portfolio Underperformance",
        "description": "Risk of pension fund investments not meeting target returns, affecting ability to pay future benefits",
        "category": "strategic",
        "likelihood": 3,
        "impact": 5,
        "risk_source": "Market volatility, poor investment decisions",
        "department": "Investments",
        "owner": "head.investments"
    },
    {
        "title": "Regulatory Changes to Pension Act",
        "description": "Risk of adverse changes to pension legislation affecting operations and benefit structures",
        "category": "strategic", 
        "likelihood": 2,
        "impact": 4,
        "risk_source": "Government policy changes",
        "department": "Legal and Corporate Affairs",
        "owner": "chief.risk"
    },
    
    # Operational Risks
    {
        "title": "Benefits Payment Processing Delays",
        "description": "Risk of delays in processing pension benefits causing member dissatisfaction and reputational damage",
        "category": "operational",
        "likelihood": 3,
        "impact": 4,
        "risk_source": "System failures, process inefficiencies",
        "department": "Benefits Administration",
        "owner": "head.benefits"
    },
    {
        "title": "Contribution Collection Failures",
        "description": "Risk of employers not remitting pension contributions on time affecting fund liquidity",
        "category": "operational",
        "likelihood": 4,
        "impact": 4,
        "risk_source": "Employer non-compliance, economic conditions",
        "department": "Contributions and Compliance",
        "owner": "compliance.officer"
    },
    {
        "title": "Member Data Integrity Issues",
        "description": "Risk of inaccurate member records affecting benefit calculations and payments",
        "category": "operational",
        "likelihood": 3,
        "impact": 3,
        "risk_source": "Data entry errors, system integration issues",
        "department": "Operations",
        "owner": "head.it"
    },
    
    # Financial Risks
    {
        "title": "Actuarial Deficit",
        "description": "Risk of pension liabilities exceeding assets leading to funding shortfalls",
        "category": "financial",
        "likelihood": 2,
        "impact": 5,
        "risk_source": "Demographic changes, investment losses",
        "department": "Finance",
        "owner": "chief.risk"
    },
    {
        "title": "Foreign Exchange Losses",
        "description": "Risk of losses from currency fluctuations on international investments",
        "category": "financial",
        "likelihood": 3,
        "impact": 3,
        "risk_source": "Currency volatility",
        "department": "Investments",
        "owner": "head.investments"
    },
    {
        "title": "Liquidity Crisis",
        "description": "Risk of insufficient liquid assets to meet benefit payment obligations",
        "category": "financial",
        "likelihood": 2,
        "impact": 5,
        "risk_source": "Asset-liability mismatch, contribution delays",
        "department": "Finance",
        "owner": "chief.risk"
    },
    
    # Compliance Risks
    {
        "title": "Non-compliance with PIA Regulations",
        "description": "Risk of violating Pensions and Insurance Authority regulations leading to penalties",
        "category": "compliance",
        "likelihood": 2,
        "impact": 4,
        "risk_source": "Regulatory oversight, process gaps",
        "department": "Risk and Compliance",
        "owner": "compliance.officer"
    },
    {
        "title": "Anti-Money Laundering Violations",
        "description": "Risk of pension scheme being used for money laundering activities",
        "category": "compliance",
        "likelihood": 1,
        "impact": 5,
        "risk_source": "Inadequate KYC procedures",
        "department": "Risk and Compliance",
        "owner": "compliance.officer"
    },
    
    # Cyber Risks
    {
        "title": "Ransomware Attack on Core Systems",
        "description": "Risk of ransomware encrypting critical pension administration systems",
        "category": "cyber",
        "likelihood": 3,
        "impact": 5,
        "risk_source": "Cyber criminals, system vulnerabilities",
        "department": "Information Technology",
        "owner": "head.it"
    },
    {
        "title": "Member Data Breach",
        "description": "Risk of unauthorized access to sensitive member personal and financial data",
        "category": "cyber",
        "likelihood": 3,
        "impact": 4,
        "risk_source": "Hacking, insider threats",
        "department": "Information Technology",
        "owner": "head.it"
    },
    {
        "title": "Online Portal Service Disruption",
        "description": "Risk of member self-service portal being unavailable affecting service delivery",
        "category": "cyber",
        "likelihood": 3,
        "impact": 3,
        "risk_source": "DDoS attacks, infrastructure failures",
        "department": "Information Technology",
        "owner": "head.it"
    },
    
    # Reputational Risks
    {
        "title": "Negative Media Coverage",
        "description": "Risk of adverse publicity affecting public trust in NAPSA",
        "category": "reputational",
        "likelihood": 3,
        "impact": 3,
        "risk_source": "Service failures, scandals",
        "department": "Public Relations",
        "owner": "chief.risk"
    },
    {
        "title": "Member Complaints Escalation",
        "description": "Risk of unresolved complaints escalating to regulators or media",
        "category": "reputational",
        "likelihood": 3,
        "impact": 3,
        "risk_source": "Poor service delivery",
        "department": "Operations",
        "owner": "head.benefits"
    }
]

# NAPSA-specific controls
NAPSA_CONTROLS = [
    # Investment Controls
    {
        "name": "Investment Policy Statement",
        "description": "Comprehensive policy governing investment decisions and asset allocation",
        "type": "preventive",
        "status": "effective",
        "implementation_cost": 50000,
        "testing_frequency": "quarterly"
    },
    {
        "name": "Investment Performance Monitoring",
        "description": "Monthly monitoring of investment returns against benchmarks",
        "type": "detective",
        "status": "effective",
        "implementation_cost": 30000,
        "testing_frequency": "monthly"
    },
    
    # Operational Controls
    {
        "name": "Automated Benefits Calculation System",
        "description": "System to automatically calculate pension benefits based on contributions",
        "type": "preventive",
        "status": "effective",
        "implementation_cost": 500000,
        "testing_frequency": "quarterly"
    },
    {
        "name": "Contribution Reconciliation Process",
        "description": "Monthly reconciliation of employer contributions",
        "type": "detective",
        "status": "partially_effective",
        "implementation_cost": 80000,
        "testing_frequency": "monthly"
    },
    {
        "name": "Member Data Validation Rules",
        "description": "Automated validation of member data inputs",
        "type": "preventive",
        "status": "effective",
        "implementation_cost": 100000,
        "testing_frequency": "quarterly"
    },
    
    # Cyber Controls
    {
        "name": "Multi-Factor Authentication",
        "description": "MFA for all system access",
        "type": "preventive",
        "status": "effective",
        "implementation_cost": 50000,
        "testing_frequency": "annually"
    },
    {
        "name": "Data Encryption at Rest and Transit",
        "description": "Encryption of all sensitive member data",
        "type": "preventive",
        "status": "effective",
        "implementation_cost": 150000,
        "testing_frequency": "annually"
    },
    {
        "name": "Security Information Event Management (SIEM)",
        "description": "Real-time monitoring of security events",
        "type": "detective",
        "status": "effective",
        "implementation_cost": 200000,
        "testing_frequency": "monthly"
    },
    {
        "name": "Backup and Disaster Recovery",
        "description": "Regular backups with tested recovery procedures",
        "type": "corrective",
        "status": "effective",
        "implementation_cost": 300000,
        "testing_frequency": "quarterly"
    },
    
    # Compliance Controls
    {
        "name": "Regulatory Compliance Monitoring",
        "description": "Tracking of regulatory requirements and compliance status",
        "type": "detective",
        "status": "effective",
        "implementation_cost": 60000,
        "testing_frequency": "quarterly"
    },
    {
        "name": "Know Your Customer (KYC) Procedures",
        "description": "Member verification and AML screening",
        "type": "preventive",
        "status": "effective",
        "implementation_cost": 80000,
        "testing_frequency": "annually"
    },
    
    # Financial Controls
    {
        "name": "Asset-Liability Matching Study",
        "description": "Annual ALM study to ensure funding adequacy",
        "type": "preventive",
        "status": "effective",
        "implementation_cost": 100000,
        "testing_frequency": "annually"
    },
    {
        "name": "Liquidity Risk Monitoring",
        "description": "Daily monitoring of cash positions and liquidity needs",
        "type": "detective",
        "status": "effective",
        "implementation_cost": 40000,
        "testing_frequency": "monthly"
    }
]

# NAPSA-specific KRIs
NAPSA_KRIS = [
    {
        "name": "Investment Return vs Benchmark",
        "description": "Percentage deviation of actual returns from benchmark",
        "metric_type": "percentage",
        "threshold_green": 2,
        "threshold_amber": -2,
        "threshold_red": -5,
        "frequency": "monthly",
        "unit": "%"
    },
    {
        "name": "Contribution Collection Rate",
        "description": "Percentage of expected contributions collected on time",
        "metric_type": "percentage", 
        "threshold_green": 95,
        "threshold_amber": 90,
        "threshold_red": 85,
        "frequency": "monthly",
        "unit": "%"
    },
    {
        "name": "Benefits Processing Time",
        "description": "Average days to process benefit payments",
        "metric_type": "number",
        "threshold_green": 5,
        "threshold_amber": 10,
        "threshold_red": 15,
        "frequency": "weekly",
        "unit": "days"
    },
    {
        "name": "System Availability",
        "description": "Percentage uptime of critical systems",
        "metric_type": "percentage",
        "threshold_green": 99.5,
        "threshold_amber": 99,
        "threshold_red": 98,
        "frequency": "daily",
        "unit": "%"
    },
    {
        "name": "Member Complaints",
        "description": "Number of unresolved member complaints",
        "metric_type": "number",
        "threshold_green": 10,
        "threshold_amber": 20,
        "threshold_red": 30,
        "frequency": "weekly",
        "unit": "complaints"
    },
    {
        "name": "Funding Ratio",
        "description": "Ratio of assets to liabilities",
        "metric_type": "percentage",
        "threshold_green": 110,
        "threshold_amber": 100,
        "threshold_red": 90,
        "frequency": "quarterly",
        "unit": "%"
    },
    {
        "name": "Cyber Security Incidents",
        "description": "Number of security incidents detected",
        "metric_type": "number",
        "threshold_green": 5,
        "threshold_amber": 10,
        "threshold_red": 20,
        "frequency": "monthly",
        "unit": "incidents"
    },
    {
        "name": "Regulatory Compliance Score",
        "description": "Percentage compliance with regulatory requirements",
        "metric_type": "percentage",
        "threshold_green": 98,
        "threshold_amber": 95,
        "threshold_red": 90,
        "frequency": "quarterly",
        "unit": "%"
    }
]

async def clear_existing_data(session: AsyncSession):
    """Clear existing data from all tables"""
    print("🧹 Clearing existing data...")
    
    # Delete in reverse order of dependencies
    tables = [
        KRIMeasurement,
        KeyRiskIndicator,
        RiskControl,
        Control,
        RiskAssessment,
        IncidentTimelineEvent,
        Incident,
        RiskTreatment,
        ComplianceMapping,
        ComplianceRequirement,
        Risk,
        AuditLog,
        User
    ]
    
    for table in tables:
        await session.execute(delete(table))
    
    await session.commit()
    print("✅ Existing data cleared")

async def create_users(session: AsyncSession) -> Dict[str, User]:
    """Create NAPSA users"""
    print("👤 Creating NAPSA users...")
    users = {}
    
    for user_data in NAPSA_USERS:
        user = User(
            id=str(uuid4()),
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            hashed_password=get_password_hash(user_data["password"]),
            role=user_data["role"],
            department=user_data["department"],
            is_active=True
        )
        session.add(user)
        users[user.username] = user
    
    await session.commit()
    print(f"✅ Created {len(users)} users")
    return users

async def create_risks(session: AsyncSession, users: Dict[str, User]) -> List[Risk]:
    """Create NAPSA-specific risks"""
    print("⚠️ Creating NAPSA risks...")
    risks = []
    
    for risk_data in NAPSA_RISKS:
        owner = users.get(risk_data["owner"])
        if not owner:
            owner = users["chief.risk"]
        
        risk = Risk(
            id=str(uuid4()),
            title=risk_data["title"],
            description=risk_data["description"],
            category=risk_data["category"],
            status="active",
            likelihood=risk_data["likelihood"],
            impact=risk_data["impact"],
            inherent_risk_score=risk_data["likelihood"] * risk_data["impact"],
            risk_source=risk_data["risk_source"],
            risk_owner_id=owner.id,
            department=risk_data["department"]
        )
        session.add(risk)
        risks.append(risk)
    
    await session.commit()
    print(f"✅ Created {len(risks)} risks")
    return risks

async def create_controls(session: AsyncSession) -> List[Control]:
    """Create NAPSA-specific controls"""
    print("🛡️ Creating NAPSA controls...")
    controls = []
    
    for control_data in NAPSA_CONTROLS:
        control = Control(
            id=str(uuid4()),
            name=control_data["name"],
            description=control_data["description"],
            type=control_data["type"],
            status=control_data["status"],
            cost_of_control=control_data["implementation_cost"],
            testing_frequency=control_data["testing_frequency"],
            last_test_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90)),
            next_test_date=datetime.now(timezone.utc) + timedelta(days=random.randint(30, 180))
        )
        session.add(control)
        controls.append(control)
    
    await session.commit()
    print(f"✅ Created {len(controls)} controls")
    return controls

async def map_risks_to_controls(session: AsyncSession, risks: List[Risk], controls: List[Control]):
    """Map risks to relevant controls"""
    print("🔗 Mapping risks to controls...")
    mappings = 0
    
    # Investment risks to investment controls
    investment_risks = [r for r in risks if "investment" in r.title.lower() or "portfolio" in r.title.lower()]
    investment_controls = [c for c in controls if "investment" in c.name.lower()]
    
    for risk in investment_risks:
        for control in investment_controls:
            risk_control = RiskControl(
                id=str(uuid4()),
                risk_id=risk.id,
                control_id=control.id,
                coverage_percentage=random.randint(70, 95)
            )
            session.add(risk_control)
            mappings += 1
    
    # Cyber risks to cyber controls
    cyber_risks = [r for r in risks if r.category == "cyber"]
    cyber_controls = [c for c in controls if any(term in c.name.lower() for term in ["security", "encryption", "authentication", "backup"])]
    
    for risk in cyber_risks:
        for control in cyber_controls:
            risk_control = RiskControl(
                id=str(uuid4()),
                risk_id=risk.id,
                control_id=control.id,
                coverage_percentage=random.randint(80, 95)
            )
            session.add(risk_control)
            mappings += 1
    
    # Operational risks to operational controls
    operational_risks = [r for r in risks if r.category == "operational"]
    operational_controls = [c for c in controls if any(term in c.name.lower() for term in ["benefits", "contribution", "data validation", "reconciliation"])]
    
    for risk in operational_risks:
        for control in operational_controls[:2]:  # Map to first 2 relevant controls
            risk_control = RiskControl(
                id=str(uuid4()),
                risk_id=risk.id,
                control_id=control.id,
                coverage_percentage=random.randint(75, 90)
            )
            session.add(risk_control)
            mappings += 1
    
    await session.commit()
    print(f"✅ Created {mappings} risk-control mappings")

async def create_risk_assessments(session: AsyncSession, risks: List[Risk], users: Dict[str, User]):
    """Create historical risk assessments"""
    print("📊 Creating risk assessments...")
    assessments = []
    
    for risk in risks:
        # Create 3-5 historical assessments for each risk
        num_assessments = random.randint(3, 5)
        for i in range(num_assessments):
            assessment_date = datetime.now(timezone.utc) - timedelta(days=90*i)
            
            # Simulate risk scores changing over time
            likelihood_change = random.randint(-1, 1)
            impact_change = random.randint(-1, 1)
            
            likelihood = max(1, min(5, risk.likelihood + likelihood_change))
            impact = max(1, min(5, risk.impact + impact_change))
            
            assessment = RiskAssessment(
                id=str(uuid4()),
                risk_id=risk.id,
                assessor_id=users["chief.risk"].id,
                likelihood_score=likelihood,
                impact_score=impact,
                inherent_risk=likelihood * impact,
                control_effectiveness=random.randint(60, 95),
                residual_risk=int((likelihood * impact) * (1 - random.randint(60, 95)/100)),
                assessment_date=assessment_date,
                notes=f"Quarterly assessment - Q{(i+1)}",
                next_review_date=assessment_date + timedelta(days=90)
            )
            session.add(assessment)
            assessments.append(assessment)
    
    await session.commit()
    print(f"✅ Created {len(assessments)} risk assessments")

async def create_kris(session: AsyncSession, risks: List[Risk]) -> List[KeyRiskIndicator]:
    """Create NAPSA KRIs"""
    print("📈 Creating Key Risk Indicators...")
    kris = []
    
    # Map KRIs to relevant risks
    kri_risk_mapping = {
        "Investment Return vs Benchmark": "Investment Portfolio Underperformance",
        "Contribution Collection Rate": "Contribution Collection Failures",
        "Benefits Processing Time": "Benefits Payment Processing Delays",
        "System Availability": "Online Portal Service Disruption",
        "Member Complaints": "Member Complaints Escalation",
        "Funding Ratio": "Actuarial Deficit",
        "Cyber Security Incidents": "Ransomware Attack on Core Systems",
        "Regulatory Compliance Score": "Non-compliance with PIA Regulations"
    }
    
    for kri_data in NAPSA_KRIS:
        # Find matching risk
        risk_title = kri_risk_mapping.get(kri_data["name"])
        matching_risk = next((r for r in risks if r.title == risk_title), risks[0])
        
        # Map thresholds to KRI model fields
        if kri_data["metric_type"] == "percentage":
            if "Investment Return" in kri_data["name"]:
                # For investment returns, negative is bad
                lower_threshold = kri_data["threshold_red"]
                upper_threshold = kri_data["threshold_green"]
            else:
                # For most percentages, higher is better
                lower_threshold = kri_data["threshold_red"]
                upper_threshold = 100
        else:
            # For numbers like days or incidents, lower is better
            lower_threshold = 0
            upper_threshold = kri_data["threshold_red"]
        
        kri = KeyRiskIndicator(
            id=str(uuid4()),
            risk_id=matching_risk.id,
            name=kri_data["name"],
            description=kri_data["description"],
            metric_type=kri_data["metric_type"],
            lower_threshold=lower_threshold,
            upper_threshold=upper_threshold,
            target_value=kri_data["threshold_green"],
            measurement_frequency=kri_data["frequency"],
            current_value=0,
            status="normal"
        )
        session.add(kri)
        kris.append(kri)
    
    await session.commit()
    print(f"✅ Created {len(kris)} KRIs")
    return kris

async def create_kri_measurements(session: AsyncSession, kris: List[KeyRiskIndicator]):
    """Create historical KRI measurements"""
    print("📏 Creating KRI measurements...")
    measurements = []
    
    for kri in kris:
        # Create measurements for the last 12 months
        for month in range(12):
            measurement_date = datetime.now(timezone.utc) - timedelta(days=30*month)
            
            # Generate realistic values based on KRI type
            if kri.metric_type == "percentage":
                if "Investment Return" in kri.name:
                    value = random.uniform(-5, 5)
                elif "Collection Rate" in kri.name:
                    value = random.uniform(85, 98)
                elif "System Availability" in kri.name:
                    value = random.uniform(98, 99.9)
                elif "Funding Ratio" in kri.name:
                    value = random.uniform(95, 115)
                elif "Compliance Score" in kri.name:
                    value = random.uniform(92, 100)
                else:
                    value = random.uniform(80, 100)
            else:  # number type
                if "Processing Time" in kri.name:
                    value = random.randint(3, 15)
                elif "Complaints" in kri.name:
                    value = random.randint(5, 35)
                elif "Security Incidents" in kri.name:
                    value = random.randint(0, 25)
                else:
                    value = random.randint(1, 50)
            
            # Determine status based on KRI type and thresholds
            if "Investment Return" in kri.name:
                if value >= 2:
                    status = "normal"
                elif value >= -2:
                    status = "warning"
                else:
                    status = "critical"
            elif kri.metric_type == "percentage":
                if value >= kri.target_value:
                    status = "normal"
                elif value >= kri.lower_threshold:
                    status = "warning"
                else:
                    status = "critical"
            else:  # number type - lower is better
                if value <= kri.target_value:
                    status = "normal"
                elif value <= kri.upper_threshold * 0.66:
                    status = "warning"
                else:
                    status = "critical"
            
            measurement = KRIMeasurement(
                id=str(uuid4()),
                kri_id=kri.id,
                value=value,
                status=status,
                measurement_date=measurement_date,
                notes=f"Monthly measurement - {measurement_date.strftime('%B %Y')}"
            )
            session.add(measurement)
            measurements.append(measurement)
        
        # Update KRI current value with latest measurement
        if measurements:
            latest = sorted([m for m in measurements if m.kri_id == kri.id], 
                          key=lambda x: x.measurement_date, reverse=True)[0]
            kri.current_value = latest.value
            kri.status = latest.status
            kri.last_updated = datetime.now(timezone.utc)
    
    await session.commit()
    print(f"✅ Created {len(measurements)} KRI measurements")

async def create_compliance_data(session: AsyncSession):
    """Create compliance requirements and mappings"""
    print("📋 Creating compliance data...")
    
    NAPSA_COMPLIANCE_REQUIREMENTS = [
        {
            "framework": "ISO 27001",
            "requirement_id": "A.12.1",
            "title": "Operational procedures and responsibilities",
            "description": "Ensure correct and secure operations of information processing facilities",
            "category": "Information Security"
        },
        {
            "framework": "SOX",
            "requirement_id": "404",
            "title": "Internal Control Assessment",
            "description": "Management assessment of internal controls over financial reporting",
            "category": "Financial Reporting"
        },
        {
            "framework": "GDPR",
            "requirement_id": "Art.32",
            "title": "Security of processing",
            "description": "Implement appropriate technical and organizational measures",
            "category": "Data Protection"
        }
    ]
    
    for req_data in NAPSA_COMPLIANCE_REQUIREMENTS:
        requirement = ComplianceRequirement(
            id=str(uuid4()),
            framework=req_data["framework"],
            requirement_id=req_data["requirement_id"],
            title=req_data["title"],
            description=req_data["description"],
            category=req_data["category"]
        )
        session.add(requirement)
    
    await session.commit()
    print(f"✅ Created {len(NAPSA_COMPLIANCE_REQUIREMENTS)} compliance requirements")

async def create_incidents(session: AsyncSession, users: Dict[str, User]):
    """Create sample incidents"""
    print("🚨 Creating sample incidents...")
    
    incidents_data = [
        {
            "title": "Benefits Payment System Outage",
            "description": "Core benefits payment system was down for 4 hours affecting member payments",
            "severity": "high",
            "status": "resolved",
            "type": "system_failure",
            "department": "Information Technology"
        },
        {
            "title": "Delayed Employer Contributions",
            "description": "Major employer delayed contribution remittance by 30 days",
            "severity": "medium",
            "status": "investigating",
            "type": "operational_error",
            "department": "Contributions and Compliance"
        },
        {
            "title": "Phishing Attack Attempt",
            "description": "Sophisticated phishing email targeting finance department staff",
            "severity": "high",
            "status": "contained",
            "type": "security_breach",
            "department": "Information Technology"
        }
    ]
    
    for i, inc_data in enumerate(incidents_data):
        incident = Incident(
            id=str(uuid4()),
            incident_number=f"INC-2025-{i+1:04d}",
            title=inc_data["title"],
            description=inc_data["description"],
            type=inc_data["type"],
            severity=inc_data["severity"],
            status=inc_data["status"],
            reported_by_id=users["chief.risk"].id,
            detected_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
            assigned_to_id=users["head.it"].id if "Technology" in inc_data["department"] else users["compliance.officer"].id
        )
        session.add(incident)
    
    await session.commit()
    print("✅ Created sample incidents")

async def create_audit_logs(session: AsyncSession, users: Dict[str, User], risks: List[Risk]):
    """Create sample audit logs"""
    print("📝 Creating audit logs...")
    
    actions = ["CREATE", "UPDATE", "DELETE", "VIEW"]
    entities = ["risk", "control", "assessment", "kri"]
    
    for _ in range(50):
        user = random.choice(list(users.values()))
        log = AuditLog(
            id=str(uuid4()),
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            action=random.choice(actions),
            entity_type=random.choice(entities),
            entity_id=random.choice(risks).id if random.random() > 0.5 else str(uuid4()),
            timestamp=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90)),
            ip_address=f"192.168.1.{random.randint(1, 255)}",
            user_agent="Mozilla/5.0"
        )
        session.add(log)
    
    await session.commit()
    print("✅ Created 50 audit log entries")

async def seed_database():
    """Main seeding function"""
    print("🌱 Starting NAPSA ERM database seeding...")
    print(f"📊 Database: {DATABASE_URL.replace('+asyncpg', '')}")
    
    async with AsyncSessionLocal() as session:
        try:
            # Clear existing data
            await clear_existing_data(session)
            
            # Create data in order
            users = await create_users(session)
            risks = await create_risks(session, users)
            controls = await create_controls(session)
            await map_risks_to_controls(session, risks, controls)
            await create_risk_assessments(session, risks, users)
            kris = await create_kris(session, risks)
            await create_kri_measurements(session, kris)
            await create_compliance_data(session)
            await create_incidents(session, users)
            await create_audit_logs(session, users, risks)
            
            print("\n✅ NAPSA ERM database seeding completed successfully!")
            print("\n📊 Summary:")
            print(f"- Users: {len(users)}")
            print(f"- Risks: {len(risks)}")
            print(f"- Controls: {len(controls)}")
            print(f"- KRIs: {len(kris)}")
            print(f"- Departments: {len(NAPSA_DEPARTMENTS)}")
            
            print("\n🔐 Login Credentials:")
            for user in NAPSA_USERS[:3]:
                print(f"- {user['full_name']}: {user['username']} / {user['password']}")
            
        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_database())
