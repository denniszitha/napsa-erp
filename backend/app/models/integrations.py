"""
Integration models for Zambian government and enterprise systems
ZRA, Government Bus, NAPSA Compliance, PACRA, ERP, ZPPA, CCPC, goAML
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Numeric, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ZRAIntegration(Base):
    """Zambia Revenue Authority Integration"""
    __tablename__ = "zra_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    taxpayer_tpin = Column(String(20), nullable=False, index=True)  # Tax Payer Identification Number
    company_name = Column(String(255), nullable=False)
    registration_status = Column(String(50))  # active, suspended, cancelled
    tax_clearance_status = Column(String(50))  # valid, expired, pending
    vat_registration = Column(Boolean, default=False)
    paye_registration = Column(Boolean, default=False)
    withholding_tax_agent = Column(Boolean, default=False)
    
    # Tax compliance data
    last_tax_return_date = Column(DateTime)
    tax_clearance_expiry = Column(DateTime)
    outstanding_tax_amount = Column(Numeric(15, 2), default=0)
    compliance_rating = Column(String(20))  # excellent, good, fair, poor
    
    # Integration metadata
    last_sync_date = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String(20), default='pending')  # success, failed, pending
    api_response = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GovernmentBusIntegration(Base):
    """Zambian Government Bus Integration for inter-agency communication"""
    __tablename__ = "gov_bus_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    agency_code = Column(String(10), nullable=False)  # ZRA, PACRA, BOZ, etc.
    service_code = Column(String(50), nullable=False)
    transaction_id = Column(String(100), nullable=False, index=True)
    
    # Request/Response data
    request_type = Column(String(50))  # query, update, notification
    request_payload = Column(JSON)
    response_payload = Column(JSON)
    status = Column(String(20))  # pending, completed, failed, timeout
    
    # Timing and audit
    request_timestamp = Column(DateTime, default=datetime.utcnow)
    response_timestamp = Column(DateTime)
    processing_time_ms = Column(Integer)
    
    # Error handling
    error_code = Column(String(10))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class NAPSAComplianceIntegration(Base):
    """NAPSA Compliance Integration for social security compliance"""
    __tablename__ = "napsa_compliance_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    employer_number = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    
    # Registration details
    registration_date = Column(DateTime)
    registration_status = Column(String(50))  # active, suspended, cancelled
    compliance_status = Column(String(50))  # compliant, non_compliant, under_review
    
    # Employee and contribution data
    total_employees = Column(Integer, default=0)
    active_employees = Column(Integer, default=0)
    monthly_contribution = Column(Numeric(15, 2), default=0)
    outstanding_contributions = Column(Numeric(15, 2), default=0)
    
    # Compliance metrics
    last_contribution_date = Column(DateTime)
    contribution_compliance_rate = Column(Numeric(5, 2))  # Percentage
    penalty_amount = Column(Numeric(15, 2), default=0)
    
    # Audit and reporting
    last_audit_date = Column(DateTime)
    next_audit_due = Column(DateTime)
    compliance_certificate_valid = Column(Boolean, default=False)
    certificate_expiry_date = Column(DateTime)
    
    # Integration tracking
    last_sync_date = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String(20), default='pending')
    api_response = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PACRAIntegration(Base):
    """Patents and Companies Registration Agency Integration"""
    __tablename__ = "pacra_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    company_registration_number = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    
    # Company registration details
    incorporation_date = Column(DateTime)
    company_type = Column(String(100))  # Private Limited, Public Limited, etc.
    registration_status = Column(String(50))  # active, dormant, struck_off, liquidation
    
    # Business license information
    business_license_number = Column(String(50))
    license_category = Column(String(100))
    license_status = Column(String(50))  # valid, expired, suspended, cancelled
    license_expiry_date = Column(DateTime)
    
    # Company structure
    authorized_share_capital = Column(Numeric(15, 2))
    paid_up_capital = Column(Numeric(15, 2))
    number_of_directors = Column(Integer)
    number_of_shareholders = Column(Integer)
    
    # Registered office and contact
    registered_address = Column(Text)
    postal_address = Column(String(255))
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    
    # Compliance tracking
    annual_return_due_date = Column(DateTime)
    annual_return_filed = Column(Boolean, default=False)
    compliance_status = Column(String(50))  # compliant, overdue, penalty_imposed
    penalty_amount = Column(Numeric(15, 2), default=0)
    
    # Integration metadata
    last_sync_date = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String(20), default='pending')
    api_response = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ERPIntegration(Base):
    """General ERP System Integration"""
    __tablename__ = "erp_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    erp_system_name = Column(String(100), nullable=False)  # SAP, Oracle, Sage, etc.
    integration_type = Column(String(50))  # api, database, file_transfer, webhook
    
    # Connection details
    endpoint_url = Column(String(500))
    database_connection_string = Column(Text)
    authentication_method = Column(String(50))  # oauth, api_key, basic_auth
    
    # Data synchronization
    sync_frequency = Column(String(20))  # hourly, daily, weekly, real_time
    last_sync_timestamp = Column(DateTime)
    next_sync_timestamp = Column(DateTime)
    sync_status = Column(String(20))  # active, paused, failed, disabled
    
    # Data mapping configuration
    data_mapping_config = Column(JSON)  # Field mappings between systems
    sync_direction = Column(String(20))  # inbound, outbound, bidirectional
    
    # Integration modules
    financial_data_sync = Column(Boolean, default=False)
    hr_data_sync = Column(Boolean, default=False)
    procurement_sync = Column(Boolean, default=False)
    inventory_sync = Column(Boolean, default=False)
    customer_data_sync = Column(Boolean, default=False)
    
    # Performance metrics
    total_records_synced = Column(Integer, default=0)
    sync_success_rate = Column(Numeric(5, 2))  # Percentage
    average_sync_time_minutes = Column(Integer)
    
    # Error tracking
    last_error_message = Column(Text)
    error_count_24h = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class IntegrationAuditLog(Base):
    """Audit log for all integration activities"""
    __tablename__ = "integration_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    integration_type = Column(String(50), nullable=False)  # zra, gov_bus, napsa, pacra, erp
    integration_id = Column(Integer)
    
    # Activity details
    activity_type = Column(String(50))  # sync, query, update, delete
    status = Column(String(20))  # success, failed, warning
    
    # Request/Response tracking
    request_data = Column(JSON)
    response_data = Column(JSON)
    processing_time_ms = Column(Integer)
    
    # Error information
    error_code = Column(String(20))
    error_message = Column(Text)
    
    # User and system context
    initiated_by_user_id = Column(Integer)
    system_component = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class ComplianceDashboard(Base):
    """Unified compliance dashboard aggregating all integration data"""
    __tablename__ = "compliance_dashboard"
    
    id = Column(Integer, primary_key=True, index=True)
    company_identifier = Column(String(100), nullable=False)  # Could be TPIN, Registration Number, etc.
    
    # Overall compliance status
    overall_compliance_score = Column(Numeric(5, 2))  # 0-100 percentage
    compliance_grade = Column(String(5))  # A+, A, B+, B, C+, C, D
    risk_level = Column(String(20))  # low, medium, high, critical
    
    # Individual system statuses
    zra_compliance_status = Column(String(20))
    napsa_compliance_status = Column(String(20))
    pacra_compliance_status = Column(String(20))
    erp_sync_status = Column(String(20))
    
    # Key metrics aggregation
    total_outstanding_obligations = Column(Numeric(15, 2), default=0)
    upcoming_deadlines_count = Column(Integer, default=0)
    overdue_obligations_count = Column(Integer, default=0)
    
    # Alert and notification status
    active_alerts_count = Column(Integer, default=0)
    critical_alerts_count = Column(Integer, default=0)
    last_notification_sent = Column(DateTime)
    
    # Refresh tracking
    last_updated = Column(DateTime, default=datetime.utcnow)
    auto_refresh_enabled = Column(Boolean, default=True)
    refresh_frequency_hours = Column(Integer, default=24)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ZPPAIntegration(Base):
    """Zambia Public Procurement Authority Integration"""
    __tablename__ = "zppa_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_registration_number = Column(String(50), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    registration_status = Column(String(50))  # active, suspended, debarred, pending
    
    # Supplier classification
    supplier_category = Column(String(100))  # goods, services, works, consultancy
    business_sector = Column(String(100))
    company_size = Column(String(20))  # micro, small, medium, large
    local_content_score = Column(Numeric(5, 2))
    
    # Procurement participation
    total_contracts_awarded = Column(Integer, default=0)
    total_contract_value = Column(Numeric(18, 2), default=0)
    active_contracts_count = Column(Integer, default=0)
    completed_contracts_count = Column(Integer, default=0)
    
    # Compliance tracking
    tax_clearance_valid = Column(Boolean, default=False)
    napsa_certificate_valid = Column(Boolean, default=False)
    pacra_registration_valid = Column(Boolean, default=False)
    compliance_certificate_status = Column(String(50))
    
    # Performance metrics
    performance_rating = Column(Numeric(3, 2))  # 1.00 to 5.00
    delivery_performance_score = Column(Numeric(5, 2))
    quality_performance_score = Column(Numeric(5, 2))
    contract_dispute_count = Column(Integer, default=0)
    
    # Financial standing
    annual_turnover = Column(Numeric(18, 2))
    bank_guarantee_capacity = Column(Numeric(18, 2))
    credit_rating = Column(String(10))
    
    # Registration and renewal
    initial_registration_date = Column(DateTime)
    registration_expiry_date = Column(DateTime)
    last_renewal_date = Column(DateTime)
    next_renewal_due = Column(DateTime)
    
    # Integration metadata
    last_sync_date = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String(20), default='pending')
    api_response = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CCPCIntegration(Base):
    """Competition and Consumer Protection Commission Integration"""
    __tablename__ = "ccpc_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    business_registration_number = Column(String(50), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    
    # Business registration details
    business_type = Column(String(100))  # sole_trader, partnership, company, cooperative
    industry_sector = Column(String(100))
    business_activity_code = Column(String(20))
    registration_status = Column(String(50))  # active, suspended, cancelled
    
    # Consumer protection compliance
    consumer_complaints_count = Column(Integer, default=0)
    resolved_complaints_count = Column(Integer, default=0)
    pending_complaints_count = Column(Integer, default=0)
    consumer_satisfaction_rating = Column(Numeric(3, 2))
    
    # Competition compliance
    market_share_percentage = Column(Numeric(5, 2))
    anti_competitive_practices_reported = Column(Boolean, default=False)
    merger_notification_status = Column(String(50))
    dominance_assessment_required = Column(Boolean, default=False)
    
    # Price monitoring
    price_control_applicable = Column(Boolean, default=False)
    controlled_products_list = Column(JSON)
    price_compliance_score = Column(Numeric(5, 2))
    pricing_violations_count = Column(Integer, default=0)
    
    # Quality and standards
    product_quality_certification = Column(String(100))
    quality_control_measures = Column(JSON)
    product_recall_history = Column(JSON)
    safety_standards_compliance = Column(Boolean, default=True)
    
    # Licensing and permits
    trade_license_number = Column(String(50))
    trade_license_status = Column(String(50))
    trade_license_expiry = Column(DateTime)
    special_permits = Column(JSON)
    
    # Financial and operational data
    annual_revenue = Column(Numeric(18, 2))
    number_of_employees = Column(Integer)
    branches_count = Column(Integer, default=1)
    operational_locations = Column(JSON)
    
    # Integration metadata
    last_sync_date = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String(20), default='pending')
    api_response = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GoAMLIntegration(Base):
    """goAML (Anti-Money Laundering) Integration"""
    __tablename__ = "goaml_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(String(50), nullable=False, index=True)
    institution_name = Column(String(255), nullable=False)
    institution_type = Column(String(100))  # bank, microfinance, insurance, money_transfer, etc.
    
    # AML Compliance Status
    aml_compliance_status = Column(String(50))  # compliant, non_compliant, under_review
    compliance_officer_registered = Column(Boolean, default=False)
    aml_policy_updated = Column(Boolean, default=False)
    last_aml_audit_date = Column(DateTime)
    next_aml_audit_due = Column(DateTime)
    
    # Reporting obligations
    suspicious_transaction_reports_count = Column(Integer, default=0)
    currency_transaction_reports_count = Column(Integer, default=0)
    threshold_transaction_reports_count = Column(Integer, default=0)
    last_report_submission_date = Column(DateTime)
    overdue_reports_count = Column(Integer, default=0)
    
    # Customer Due Diligence (CDD)
    total_customers = Column(Integer, default=0)
    high_risk_customers = Column(Integer, default=0)
    pep_customers = Column(Integer, default=0)  # Politically Exposed Persons
    cdd_reviews_completed = Column(Integer, default=0)
    cdd_reviews_overdue = Column(Integer, default=0)
    
    # Transaction monitoring
    monthly_transaction_volume = Column(Numeric(18, 2), default=0)
    suspicious_transactions_identified = Column(Integer, default=0)
    alerts_generated = Column(Integer, default=0)
    alerts_investigated = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    
    # Training and awareness
    staff_aml_training_completed = Column(Boolean, default=False)
    last_training_date = Column(DateTime)
    training_compliance_percentage = Column(Numeric(5, 2))
    aml_awareness_programs_conducted = Column(Integer, default=0)
    
    # Sanctions screening
    sanctions_screening_enabled = Column(Boolean, default=False)
    sanctions_matches_found = Column(Integer, default=0)
    watchlist_screening_frequency = Column(String(20))  # daily, weekly, monthly
    last_sanctions_update = Column(DateTime)
    
    # Risk assessment
    institutional_risk_rating = Column(String(20))  # low, medium, high, very_high
    country_risk_factors = Column(JSON)
    product_risk_assessment = Column(JSON)
    customer_risk_distribution = Column(JSON)
    
    # Regulatory interactions
    fia_inspection_count = Column(Integer, default=0)  # Financial Intelligence Authority
    last_fia_inspection_date = Column(DateTime)
    regulatory_actions_count = Column(Integer, default=0)
    penalties_imposed = Column(Numeric(15, 2), default=0)
    
    # Technology and systems
    aml_system_type = Column(String(100))
    system_last_updated = Column(DateTime)
    automated_monitoring_enabled = Column(Boolean, default=False)
    case_management_system = Column(String(100))
    
    # Integration metadata
    last_sync_date = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String(20), default='pending')
    api_response = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)