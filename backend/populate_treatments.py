#!/usr/bin/env python3
"""
Populate risk_treatments table with sample data for NAPSA
"""

from app.core.database import SessionLocal
from app.models.workflow import RiskTreatment, TreatmentStrategy, WorkflowStatus
from app.models.risk import Risk
from datetime import datetime, timedelta
import uuid

def populate_treatments():
    db = SessionLocal()
    
    print("=== POPULATING RISK TREATMENTS ===")
    
    try:
        # Get some risks to create treatments for
        risks = db.query(Risk).limit(10).all()
        
        if not risks:
            print("No risks found in database. Please populate risks first.")
            return
        
        print(f"Found {len(risks)} risks to create treatments for")
        
        # Sample treatments data for different risk types
        treatment_templates = [
            {
                "strategy": TreatmentStrategy.mitigate,
                "title_suffix": "Mitigation Plan",
                "description": "Comprehensive mitigation strategy to reduce risk likelihood and impact",
                "action_plan": """1. Identify and assess current controls
2. Implement additional preventive controls
3. Enhance monitoring and detection capabilities
4. Regular review and testing of controls
5. Continuous improvement based on metrics""",
                "responsible_party": "Risk Management Team",
                "estimated_cost": 75000.00,
                "expected_risk_reduction": 65.0
            },
            {
                "strategy": TreatmentStrategy.transfer,
                "title_suffix": "Risk Transfer Strategy",
                "description": "Transfer risk through insurance, outsourcing, or contractual agreements",
                "action_plan": """1. Evaluate transfer options (insurance, outsourcing)
2. Cost-benefit analysis of transfer mechanisms
3. Negotiate terms and conditions
4. Implement transfer agreements
5. Monitor transferred risk effectiveness""",
                "responsible_party": "Chief Financial Officer",
                "estimated_cost": 50000.00,
                "expected_risk_reduction": 70.0
            },
            {
                "strategy": TreatmentStrategy.accept,
                "title_suffix": "Risk Acceptance Protocol",
                "description": "Formal acceptance of risk within appetite thresholds with monitoring",
                "action_plan": """1. Document risk acceptance rationale
2. Define monitoring triggers and thresholds
3. Establish escalation procedures
4. Regular review of acceptance decision
5. Maintain contingency plans""",
                "responsible_party": "Chief Risk Officer",
                "estimated_cost": 10000.00,
                "expected_risk_reduction": 0.0
            },
            {
                "strategy": TreatmentStrategy.avoid,
                "title_suffix": "Risk Avoidance Strategy",
                "description": "Eliminate risk by avoiding the activity or changing approach",
                "action_plan": """1. Identify alternative approaches
2. Assess feasibility of alternatives
3. Develop implementation roadmap
4. Execute transition plan
5. Verify risk elimination""",
                "responsible_party": "Operations Manager",
                "estimated_cost": 100000.00,
                "expected_risk_reduction": 95.0
            }
        ]
        
        treatments_created = 0
        
        # Create treatments for selected risks
        for i, risk in enumerate(risks[:8]):  # Create treatments for first 8 risks
            template = treatment_templates[i % len(treatment_templates)]
            
            treatment = RiskTreatment(
                risk_id=risk.id,
                strategy=template["strategy"],
                title=f"{template['title_suffix']} for {risk.title}",
                description=template["description"],
                action_plan=template["action_plan"],
                responsible_party=template["responsible_party"],
                target_date=datetime.now() + timedelta(days=90 + (i * 30)),
                estimated_cost=template["estimated_cost"] * (1 + (i * 0.1)),  # Vary cost slightly
                expected_risk_reduction=template["expected_risk_reduction"],
                status=WorkflowStatus.draft if i % 3 == 0 else WorkflowStatus.in_progress if i % 3 == 1 else WorkflowStatus.approved,
                created_at=datetime.now() - timedelta(days=30 - i),
                created_by_id=uuid.UUID("93c69425-0870-4c6d-b78e-d4fa941bc6ae")  # System Administrator
            )
            
            # Set approved details for approved treatments
            if treatment.status == WorkflowStatus.approved:
                treatment.approved_by_id = uuid.UUID("93c69425-0870-4c6d-b78e-d4fa941bc6ae")
                treatment.approved_at = datetime.now() - timedelta(days=5)
            
            db.add(treatment)
            treatments_created += 1
            print(f"  ✓ Created treatment: {treatment.title[:50]}...")
        
        # Add some specific high-priority treatments
        high_priority_treatments = [
            {
                "risk_title": "Data Breach Risk",
                "strategy": TreatmentStrategy.mitigate,
                "title": "Cybersecurity Enhancement Program",
                "description": "Comprehensive cybersecurity improvements to prevent data breaches",
                "action_plan": """1. Implement multi-factor authentication
2. Deploy advanced threat detection systems
3. Conduct security awareness training
4. Regular penetration testing
5. Incident response plan updates""",
                "responsible_party": "Chief Information Security Officer",
                "estimated_cost": 250000.00,
                "expected_risk_reduction": 75.0,
                "status": WorkflowStatus.in_progress
            },
            {
                "risk_title": "Regulatory Non-Compliance",
                "strategy": TreatmentStrategy.mitigate,
                "title": "Regulatory Compliance Framework Enhancement",
                "description": "Strengthen compliance framework to meet all regulatory requirements",
                "action_plan": """1. Gap analysis against regulations
2. Update policies and procedures
3. Implement compliance monitoring tools
4. Staff training on regulations
5. Regular compliance audits""",
                "responsible_party": "Chief Compliance Officer",
                "estimated_cost": 150000.00,
                "expected_risk_reduction": 80.0,
                "status": WorkflowStatus.approved
            }
        ]
        
        for hp_treatment in high_priority_treatments:
            # Find the risk by title
            risk = db.query(Risk).filter(Risk.title.contains(hp_treatment["risk_title"])).first()
            if risk:
                treatment = RiskTreatment(
                    risk_id=risk.id,
                    strategy=hp_treatment["strategy"],
                    title=hp_treatment["title"],
                    description=hp_treatment["description"],
                    action_plan=hp_treatment["action_plan"],
                    responsible_party=hp_treatment["responsible_party"],
                    target_date=datetime.now() + timedelta(days=60),
                    estimated_cost=hp_treatment["estimated_cost"],
                    expected_risk_reduction=hp_treatment["expected_risk_reduction"],
                    status=hp_treatment["status"],
                    created_at=datetime.now() - timedelta(days=15),
                    created_by_id=uuid.UUID("93c69425-0870-4c6d-b78e-d4fa941bc6ae")
                )
                
                if treatment.status == WorkflowStatus.approved:
                    treatment.approved_by_id = uuid.UUID("93c69425-0870-4c6d-b78e-d4fa941bc6ae")
                    treatment.approved_at = datetime.now() - timedelta(days=3)
                
                db.add(treatment)
                treatments_created += 1
                print(f"  ✓ Created high-priority treatment: {treatment.title}")
        
        db.commit()
        print(f"\n✓ Successfully created {treatments_created} risk treatments")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating treatments: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate_treatments()