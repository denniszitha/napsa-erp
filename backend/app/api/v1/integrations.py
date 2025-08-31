"""
Integration API endpoints for Zambian government and ERP systems
ZRA, Government Bus, NAPSA Compliance, PACRA, ERP
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.api.deps import get_db
import random
import uuid

router = APIRouter(tags=["integrations"])

# Database dependency already imported from deps

# ZRA Integration Endpoints
@router.post("/zra/validate-tpin")
async def validate_zra_tpin(
    tpin: str,
    db: Session = Depends(get_db)
):
    """Validate TPIN with Zambia Revenue Authority"""
    try:
        # Mock ZRA validation
        result = {
            "tpin": tpin,
            "valid": True,
            "company_name": f"Company {tpin[-4:]}",
            "status": "active",
            "registration_date": "2020-01-15",
            "validated_at": datetime.utcnow().isoformat()
        }
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zra/tax-clearance/{tpin}")
async def get_zra_tax_clearance(
    tpin: str,
    db: Session = Depends(get_db)
):
    """Get tax clearance certificate status from ZRA"""
    try:
        result = await zra_service.get_tax_clearance_status(tpin, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zra/compliance-status/{tpin}")
async def get_zra_compliance_status(
    tpin: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive tax compliance status from ZRA"""
    try:
        result = await zra_service.get_compliance_status(tpin, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zra/tax-obligations/{tpin}")
async def get_zra_tax_obligations(
    tpin: str,
    db: Session = Depends(get_db)
):
    """Get upcoming tax obligations from ZRA"""
    try:
        result = await zra_service.get_tax_obligations(tpin, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/zra/submit-tax-return")
async def submit_zra_tax_return(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit tax return notification to ZRA"""
    try:
        tpin = request_data.get("tpin")
        return_data = request_data.get("return_data", {})
        
        result = await zra_service.submit_tax_return_notification(tpin, return_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NAPSA Compliance Integration Endpoints
@router.post("/napsa/validate-employer")
async def validate_napsa_employer(
    employer_number: str,
    db: Session = Depends(get_db)
):
    """Validate employer number with NAPSA"""
    try:
        result = await napsa_compliance_service.validate_employer_number(employer_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/napsa/contribution-status/{employer_number}")
async def get_napsa_contribution_status(
    employer_number: str,
    db: Session = Depends(get_db)
):
    """Get NAPSA contribution compliance status"""
    try:
        result = await napsa_compliance_service.get_contribution_status(employer_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/napsa/compliance-obligations/{employer_number}")
async def get_napsa_compliance_obligations(
    employer_number: str,
    db: Session = Depends(get_db)
):
    """Get upcoming NAPSA compliance obligations"""
    try:
        result = await napsa_compliance_service.get_compliance_obligations(employer_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/napsa/verify-employee")
async def verify_napsa_employee(
    nrc_number: str,
    db: Session = Depends(get_db)
):
    """Verify employee NAPSA membership"""
    try:
        result = await napsa_compliance_service.verify_employee_membership(nrc_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/napsa/submit-contributions")
async def submit_napsa_contributions(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit employee contribution data to NAPSA"""
    try:
        employer_number = request_data.get("employer_number")
        contribution_data = request_data.get("contribution_data", {})
        
        result = await napsa_compliance_service.submit_contribution_data(employer_number, contribution_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PACRA Integration Endpoints
@router.post("/pacra/verify-company")
async def verify_pacra_company(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Verify company registration with PACRA"""
    try:
        result = await pacra_service.verify_company_registration(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pacra/company-details/{registration_number}")
async def get_pacra_company_details(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive company details from PACRA"""
    try:
        result = await pacra_service.get_company_details(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pacra/directors/{registration_number}")
async def get_pacra_directors(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Get company director information from PACRA"""
    try:
        result = await pacra_service.get_director_information(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pacra/compliance-obligations/{registration_number}")
async def get_pacra_compliance_obligations(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Get upcoming PACRA compliance obligations"""
    try:
        result = await pacra_service.get_compliance_obligations(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pacra/submit-annual-return")
async def submit_pacra_annual_return(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit annual return to PACRA"""
    try:
        registration_number = request_data.get("registration_number")
        return_data = request_data.get("return_data", {})
        
        result = await pacra_service.submit_annual_return(registration_number, return_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pacra/search-companies")
async def search_pacra_companies(
    search_criteria: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Search for companies in PACRA database"""
    try:
        result = await pacra_service.search_companies(search_criteria, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Government Bus Integration Endpoints
@router.post("/government-bus/query-agency")
async def query_government_agency(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Query data from a government agency via Government Bus"""
    try:
        agency_code = request_data.get("agency_code")
        service_code = request_data.get("service_code")
        query_params = request_data.get("query_params", {})
        
        result = await government_bus_service.query_agency_data(agency_code, service_code, query_params, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/government-bus/submit-to-agency")
async def submit_to_government_agency(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit data to a government agency via Government Bus"""
    try:
        agency_code = request_data.get("agency_code")
        service_code = request_data.get("service_code")
        submission_data = request_data.get("submission_data", {})
        
        result = await government_bus_service.submit_data_to_agency(agency_code, service_code, submission_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/government-bus/transaction-status/{transaction_id}")
async def get_government_bus_transaction_status(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a Government Bus transaction"""
    try:
        result = await government_bus_service.get_transaction_status(transaction_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/government-bus/agency-services/{agency_code}")
async def get_government_agency_services(
    agency_code: str,
    db: Session = Depends(get_db)
):
    """Get available services for a government agency"""
    try:
        result = await government_bus_service.get_agency_services(agency_code, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ERP Integration Endpoints
@router.post("/erp/register-system")
async def register_erp_system(
    erp_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Register a new ERP system for integration"""
    try:
        result = await erp_integration_service.register_erp_system(erp_config, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/erp/{erp_id}/sync-financial")
async def sync_erp_financial_data(
    erp_id: int,
    db: Session = Depends(get_db)
):
    """Synchronize financial data from ERP system"""
    try:
        result = await erp_integration_service.sync_financial_data(erp_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/erp/{erp_id}/sync-hr")
async def sync_erp_hr_data(
    erp_id: int,
    db: Session = Depends(get_db)
):
    """Synchronize HR data from ERP system"""
    try:
        result = await erp_integration_service.sync_hr_data(erp_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/erp/{erp_id}/sync-procurement")
async def sync_erp_procurement_data(
    erp_id: int,
    db: Session = Depends(get_db)
):
    """Synchronize procurement data from ERP system"""
    try:
        result = await erp_integration_service.sync_procurement_data(erp_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/erp/{erp_id}/status")
async def get_erp_integration_status(
    erp_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive status of ERP integration"""
    try:
        result = await erp_integration_service.get_erp_status(erp_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/erp/{erp_id}/test-connection")
async def test_erp_connection(
    erp_id: int,
    db: Session = Depends(get_db)
):
    """Test connectivity to ERP system"""
    try:
        result = await erp_integration_service.test_erp_connection(erp_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/erp/systems")
async def get_all_erp_systems(
    db: Session = Depends(get_db)
):
    """Get all registered ERP systems"""
    try:
        result = await erp_integration_service.get_all_erp_systems(db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Unified Dashboard Endpoints
@router.get("/dashboard/compliance-overview")
async def get_compliance_dashboard_overview(
    company_identifier: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get unified compliance dashboard overview"""
    try:
        # Mock unified compliance data - replace with actual aggregation logic
        compliance_overview = {
            "overall_compliance_score": 88.5,
            "compliance_grade": "B+",
            "risk_level": "medium",
            "system_statuses": {
                "zra": {
                    "status": "compliant",
                    "last_sync": datetime.utcnow().isoformat(),
                    "outstanding_issues": 0
                },
                "napsa": {
                    "status": "compliant",
                    "last_sync": datetime.utcnow().isoformat(),
                    "outstanding_issues": 0
                },
                "pacra": {
                    "status": "compliant",
                    "last_sync": datetime.utcnow().isoformat(),
                    "outstanding_issues": 1
                },
                "zppa": {
                    "status": "compliant",
                    "last_sync": datetime.utcnow().isoformat(),
                    "outstanding_issues": 0
                },
                "ccpc": {
                    "status": "compliant",
                    "last_sync": datetime.utcnow().isoformat(),
                    "outstanding_issues": 0
                },
                "goaml": {
                    "status": "compliant",
                    "last_sync": datetime.utcnow().isoformat(),
                    "outstanding_issues": 2
                }
            },
            "upcoming_obligations": [
                {
                    "agency": "ZRA",
                    "obligation": "VAT Return",
                    "due_date": "2024-08-15",
                    "status": "pending"
                },
                {
                    "agency": "PACRA",
                    "obligation": "Annual Return",
                    "due_date": "2024-08-31",
                    "status": "pending"
                },
                {
                    "agency": "ZPPA",
                    "obligation": "Supplier Registration Renewal",
                    "due_date": "2024-09-15",
                    "status": "upcoming"
                },
                {
                    "agency": "goAML",
                    "obligation": "Monthly STR Summary Report",
                    "due_date": "2024-08-15",
                    "status": "pending"
                }
            ],
            "total_outstanding_amount": 0.00,
            "critical_alerts": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return {"data": compliance_overview, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/integration-health")
async def get_integration_health_status(
    db: Session = Depends(get_db)
):
    """Get health status of all integrations"""
    try:
        health_status = {
            "overall_health": "healthy",
            "systems": {
                "zra": {
                    "status": "healthy",
                    "last_successful_sync": datetime.utcnow().isoformat(),
                    "response_time_ms": 150,
                    "error_rate_24h": 0
                },
                "napsa": {
                    "status": "healthy", 
                    "last_successful_sync": datetime.utcnow().isoformat(),
                    "response_time_ms": 180,
                    "error_rate_24h": 0
                },
                "pacra": {
                    "status": "healthy",
                    "last_successful_sync": datetime.utcnow().isoformat(),
                    "response_time_ms": 200,
                    "error_rate_24h": 0
                },
                "government_bus": {
                    "status": "healthy",
                    "active_connections": 3,
                    "transaction_success_rate": 98.5
                },
                "zppa": {
                    "status": "healthy",
                    "last_successful_sync": datetime.utcnow().isoformat(),
                    "response_time_ms": 220,
                    "error_rate_24h": 0
                },
                "ccpc": {
                    "status": "healthy",
                    "last_successful_sync": datetime.utcnow().isoformat(),
                    "response_time_ms": 190,
                    "error_rate_24h": 0
                },
                "goaml": {
                    "status": "healthy",
                    "last_successful_sync": datetime.utcnow().isoformat(),
                    "response_time_ms": 350,
                    "error_rate_24h": 1.2
                }
            },
            "performance_metrics": {
                "total_transactions_24h": 89,
                "successful_transactions": 86,
                "failed_transactions": 3,
                "average_response_time_ms": 235
            }
        }
        
        return {"data": health_status, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance/report")
async def generate_compliance_report(
    report_type: str = Query("full", description="Type of report: full, summary, agency"),
    agency: Optional[str] = Query(None, description="Specific agency: zra, napsa, pacra"),
    period: Optional[str] = Query("current_month", description="Reporting period"),
    db: Session = Depends(get_db)
):
    """Generate comprehensive compliance report"""
    try:
        # Mock comprehensive compliance report
        if report_type == "summary":
            report_data = {
                "report_type": "compliance_summary",
                "period": period,
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "overall_compliance_score": 88.5,
                    "compliant_systems": 3,
                    "non_compliant_systems": 0,
                    "critical_issues": 0,
                    "pending_actions": 2
                }
            }
        elif agency:
            # Agency-specific report
            agency_reports = {
                "zra": {
                    "tax_compliance_score": 95,
                    "outstanding_returns": 0,
                    "clearance_certificates": {"valid": 5, "expired": 0, "pending": 1},
                    "recent_submissions": 12
                },
                "napsa": {
                    "contribution_compliance": 98,
                    "active_employees": 145,
                    "monthly_contributions": 28000.00,
                    "certificate_status": "valid"
                },
                "pacra": {
                    "registration_status": "active",
                    "annual_returns_filed": True,
                    "directors_count": 2,
                    "compliance_score": 92
                }
            }
            
            report_data = {
                "report_type": f"agency_report_{agency}",
                "agency": agency.upper(),
                "period": period,
                "generated_at": datetime.utcnow().isoformat(),
                "data": agency_reports.get(agency.lower(), {})
            }
        else:
            # Full comprehensive report
            report_data = {
                "report_type": "full_compliance",
                "period": period,
                "generated_at": datetime.utcnow().isoformat(),
                "executive_summary": {
                    "overall_score": 88.5,
                    "grade": "B+",
                    "risk_level": "medium",
                    "total_transactions": 1250,
                    "successful_integrations": 4
                },
                "system_details": {
                    "zra": {"score": 95, "status": "compliant", "issues": 0},
                    "napsa": {"score": 98, "status": "compliant", "issues": 0},
                    "pacra": {"score": 92, "status": "compliant", "issues": 1},
                    "government_bus": {"score": 85, "status": "healthy", "uptime": "99.2%"}
                },
                "recommendations": [
                    "Review PACRA annual return submission process",
                    "Implement automated compliance monitoring alerts",
                    "Schedule quarterly integration health assessments"
                ],
                "compliance_timeline": [
                    {
                        "date": "2024-08-01",
                        "event": "ZRA tax clearance renewed",
                        "status": "completed"
                    },
                    {
                        "date": "2024-08-15",
                        "event": "NAPSA contribution submission due",
                        "status": "pending"
                    }
                ]
            }
        
        return {"data": report_data, "success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/all-systems")
async def sync_all_systems(
    force_sync: bool = False,
    db: Session = Depends(get_db)
):
    """Trigger synchronization across all integrated systems"""
    try:
        sync_results = []
        
        # Mock synchronization for all systems
        systems = ["zra", "napsa", "pacra", "government_bus", "zppa", "ccpc", "goaml"]
        
        for system in systems:
            sync_result = {
                "system": system,
                "sync_started": datetime.utcnow().isoformat(),
                "status": "completed",
                "records_synced": 45 if system != "government_bus" else 12,
                "sync_duration_seconds": 30,
                "errors": 0 if system != "pacra" else 1
            }
            sync_results.append(sync_result)
        
        return {
            "data": {
                "sync_id": f"SYNC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "total_systems": len(systems),
                "successful_syncs": len([r for r in sync_results if r["status"] == "completed"]),
                "failed_syncs": 0,
                "sync_results": sync_results,
                "overall_status": "completed"
            },
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ZPPA Integration Endpoints
@router.post("/zppa/verify-supplier")
async def verify_zppa_supplier(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Verify supplier registration with ZPPA"""
    try:
        result = await zppa_service.verify_supplier_registration(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zppa/supplier-profile/{registration_number}")
async def get_zppa_supplier_profile(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive supplier profile from ZPPA"""
    try:
        result = await zppa_service.get_supplier_profile(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zppa/procurement-opportunities")
async def get_zppa_procurement_opportunities(
    supplier_category: str = Query("all", description="Supplier category: goods, services, works, consultancy"),
    db: Session = Depends(get_db)
):
    """Get available procurement opportunities"""
    try:
        result = await zppa_service.get_procurement_opportunities(supplier_category, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zppa/contract-performance/{registration_number}")
async def get_zppa_contract_performance(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Get supplier contract performance history"""
    try:
        result = await zppa_service.get_contract_performance(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/zppa/submit-application")
async def submit_zppa_application(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit procurement application to ZPPA"""
    try:
        registration_number = request_data.get("registration_number")
        tender_id = request_data.get("tender_id")
        application_data = request_data.get("application_data", {})
        
        result = await zppa_service.submit_procurement_application(registration_number, tender_id, application_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CCPC Integration Endpoints
@router.post("/ccpc/verify-business")
async def verify_ccpc_business(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Verify business registration with CCPC"""
    try:
        result = await ccpc_service.verify_business_registration(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ccpc/consumer-protection-status/{registration_number}")
async def get_ccpc_consumer_protection_status(
    registration_number: str,
    db: Session = Depends(get_db)
):
    """Get consumer protection compliance status from CCPC"""
    try:
        result = await ccpc_service.get_consumer_protection_status(registration_number, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ccpc/submit-complaint")
async def submit_ccpc_consumer_complaint(
    complaint_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit consumer complaint to CCPC"""
    try:
        result = await ccpc_service.submit_consumer_complaint(complaint_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ccpc/market-analysis/{industry_sector}")
async def get_ccpc_market_analysis(
    industry_sector: str,
    db: Session = Depends(get_db)
):
    """Get market competition analysis for industry sector"""
    try:
        result = await ccpc_service.get_market_competition_analysis(industry_sector, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ccpc/price-control-check")
async def check_ccpc_price_control(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Check price control compliance for specified products"""
    try:
        registration_number = request_data.get("registration_number")
        product_categories = request_data.get("product_categories", [])
        
        result = await ccpc_service.check_price_control_compliance(registration_number, product_categories, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# goAML Integration Endpoints
@router.post("/goaml/verify-institution")
async def verify_goaml_institution(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """Verify institution registration with goAML"""
    try:
        result = await goaml_service.verify_institution_registration(institution_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/goaml/aml-compliance-status/{institution_id}")
async def get_goaml_compliance_status(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """Get AML compliance status from goAML"""
    try:
        result = await goaml_service.get_aml_compliance_status(institution_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/goaml/submit-str")
async def submit_goaml_str(
    str_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit Suspicious Transaction Report (STR) to goAML"""
    try:
        result = await goaml_service.submit_suspicious_transaction_report(str_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/goaml/submit-ctr")
async def submit_goaml_ctr(
    ctr_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Submit Currency Transaction Report (CTR) to goAML"""
    try:
        result = await goaml_service.submit_currency_transaction_report(ctr_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/goaml/sanctions-screening")
async def perform_goaml_sanctions_screening(
    screening_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Perform sanctions and PEP screening through goAML"""
    try:
        result = await goaml_service.perform_sanctions_screening(screening_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/goaml/reporting-obligations/{institution_id}")
async def get_goaml_reporting_obligations(
    institution_id: str,
    db: Session = Depends(get_db)
):
    """Get upcoming AML reporting obligations"""
    try:
        result = await goaml_service.get_aml_reporting_obligations(institution_id, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/goaml/update-customer-risk")
async def update_goaml_customer_risk(
    customer_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update customer risk profile in goAML"""
    try:
        result = await goaml_service.update_customer_risk_profile(customer_data, db)
        return {"data": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))