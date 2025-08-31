from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.api.v1 import (
    auth, users, risks, assessments, assessment_periods, controls, kris,
    treatments, reports, audit, dashboard, analytics,
    compliance, incidents, data_exchange, simulation, blockchain_audit, streaming, dashboards, federated_learning, regulatory_reporting, network_analysis, notifications, rcsa, departments, bi_tools, risk_matrices,
    file_management, system_config, ad_integration, template_management, rcsa_new, risk_categories,
    heatmap, report_generation, sms_notifications, oracle_erp_connector,
    branches, executive_dashboard
)
# from app.api.v1.aml import router as aml_router  # Temporarily disabled due to schema issues
from app.api.v1 import unified_dashboard
from app.api.v1 import analytics_clickhouse
from app.core.clickhouse import init_clickhouse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting NAPSA ERM & AML System with ClickHouse Analytics...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize ClickHouse - disabled for startup
    # try:
    #     init_clickhouse()
    #     logger.info("ClickHouse initialized successfully")
    # except Exception as e:
    #     logger.warning(f"ClickHouse initialization failed: {e}")
    
    # Start data pipeline - disabled for startup
    # try:
    #     from app.services.data_pipeline import get_data_pipeline
    #     pipeline = get_data_pipeline()
    #     pipeline.start_pipeline()
    #     logger.info("Data pipeline started")
    # except Exception as e:
    #     logger.warning(f"Data pipeline start failed: {e}")
    
    # Start streaming service - disabled for startup
    # try:
    #     from app.services.streaming import get_streaming_service
    #     streaming_service = get_streaming_service()
    #     # Start streaming service in background
    #     import asyncio
    #     asyncio.create_task(streaming_service.start())
    #     logger.info("Streaming service started")
    # except Exception as e:
    #     logger.warning(f"Streaming service start failed: {e}")
    
    yield
    # Shutdown
    logger.info("Shutting down NAPSA ERM & AML System...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(risks.router, prefix=f"{settings.API_V1_STR}/risks", tags=["risks"])
app.include_router(assessments.router, prefix=f"{settings.API_V1_STR}/assessments", tags=["assessments"])
app.include_router(assessment_periods.router, prefix=f"{settings.API_V1_STR}/assessment-periods", tags=["assessment-periods"])
app.include_router(controls.router, prefix=f"{settings.API_V1_STR}/controls", tags=["controls"])
app.include_router(kris.router, prefix=f"{settings.API_V1_STR}/kris", tags=["kris"])
app.include_router(treatments.router, prefix=f"{settings.API_V1_STR}/treatments", tags=["treatments"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])
app.include_router(audit.router, prefix=f"{settings.API_V1_STR}/audit", tags=["audit"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(compliance.router, prefix=f"{settings.API_V1_STR}/compliance", tags=["compliance"])
app.include_router(incidents.router, prefix=f"{settings.API_V1_STR}/incidents", tags=["incidents"])
app.include_router(data_exchange.router, prefix=f"{settings.API_V1_STR}/data", tags=["data-exchange"])
app.include_router(simulation.router, prefix=f"{settings.API_V1_STR}/simulation", tags=["simulation"])

# AML Module Routes
# app.include_router(aml_router, prefix=f"{settings.API_V1_STR}/aml", tags=["AML"])  # Temporarily disabled

# Unified Dashboard
app.include_router(unified_dashboard.router, prefix=f"{settings.API_V1_STR}/unified", tags=["Unified Dashboard"])

# ClickHouse Analytics
app.include_router(analytics_clickhouse.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["ClickHouse Analytics"])

# Blockchain Audit
app.include_router(blockchain_audit.router, prefix=f"{settings.API_V1_STR}/blockchain", tags=["Blockchain Audit"])

# Real-time Streaming
app.include_router(streaming.router, prefix=f"{settings.API_V1_STR}/streaming", tags=["Real-time Streaming"])

# Advanced Dashboards
app.include_router(dashboards.router, prefix=f"{settings.API_V1_STR}/dashboards", tags=["Advanced Dashboards"])

# Federated Learning
app.include_router(federated_learning.router, prefix=f"{settings.API_V1_STR}/federated-learning", tags=["Federated Learning"])

# Regulatory Reporting
app.include_router(regulatory_reporting.router, prefix=f"{settings.API_V1_STR}/regulatory", tags=["Regulatory Reporting"])

# Network Analysis
app.include_router(network_analysis.router, prefix=f"{settings.API_V1_STR}/network", tags=["Network Analysis"])
# Notifications
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notifications"])
# RCSA
app.include_router(rcsa.router, prefix=f"{settings.API_V1_STR}/rcsa", tags=["RCSA"])
# RCSA New (Comprehensive)
app.include_router(rcsa_new.router, prefix=f"{settings.API_V1_STR}/rcsa-new", tags=["RCSA Comprehensive"])
# Departments
app.include_router(departments.router, prefix=f"{settings.API_V1_STR}/departments", tags=["Departments"])

# BI Tools
app.include_router(bi_tools.router, prefix=f"{settings.API_V1_STR}/bi-tools", tags=["Business Intelligence"])
# Risk Matrices
app.include_router(risk_matrices.router, prefix=f"{settings.API_V1_STR}/risk-matrices", tags=["Risk Matrices"])

# File Management
app.include_router(file_management.router, prefix=f"{settings.API_V1_STR}/files", tags=["File Management"])

# System Configuration
app.include_router(system_config.router, prefix=f"{settings.API_V1_STR}/system-config", tags=["System Configuration"])

# Active Directory Integration
app.include_router(ad_integration.router, prefix=f"{settings.API_V1_STR}/ad", tags=["Active Directory"])

# Template Management (Assessment Templates and Scales)
app.include_router(template_management.router, prefix=f"{settings.API_V1_STR}", tags=["Template Management"])

# Risk Categories Management
app.include_router(risk_categories.router, prefix=f"{settings.API_V1_STR}/risk-categories", tags=["Risk Categories"])

# Heat Map Visualization
app.include_router(heatmap.router, prefix=f"{settings.API_V1_STR}/heatmap", tags=["Heat Map"])

# Report Generation (PDF/Excel)
app.include_router(report_generation.router, prefix=f"{settings.API_V1_STR}/reports/generate", tags=["Report Generation"])

# SMS Notifications
app.include_router(sms_notifications.router, prefix=f"{settings.API_V1_STR}/sms", tags=["SMS Notifications"])

# Oracle ERP Connector
app.include_router(oracle_erp_connector.router, prefix=f"{settings.API_V1_STR}/oracle-erp", tags=["Oracle ERP"])

# Import the new modules first
from app.api.v1 import organizational_units, kris_enhanced, rcsa_enhanced

# NAPSA Branch Management
app.include_router(branches.router, prefix=f"{settings.API_V1_STR}/branches", tags=["Branch Management"])

# Executive Dashboard
app.include_router(executive_dashboard.router, prefix=f"{settings.API_V1_STR}/executive", tags=["Executive Dashboard"])

# Organizational Units Management
app.include_router(organizational_units.router, prefix=f"{settings.API_V1_STR}/organizational-units", tags=["Organizational Units"])

# Enhanced KRI Management
app.include_router(kris_enhanced.router, prefix=f"{settings.API_V1_STR}/kris-enhanced", tags=["Enhanced KRIs"])

# Enhanced RCSA Management
app.include_router(rcsa_enhanced.router, prefix=f"{settings.API_V1_STR}/rcsa-enhanced", tags=["Enhanced RCSA"])

@app.get("/")
def read_root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "features": {
            "core": [
                "User Management",
                "Risk Management",
                "Risk Assessments",
                "Controls Management",
                "Key Risk Indicators (KRIs)"
            ],
            "advanced": [
                "Risk Treatment Workflows",
                "Email Notifications",
                "PDF Report Generation",
                "Comprehensive Audit Logging"
            ],
            "analytics": [
                "Risk Heatmaps",
                "Trend Analysis",
                "Risk Correlations",
                "Control Effectiveness Analysis",
                "Executive Dashboards"
            ],
            "compliance": [
                "Multi-framework Support",
                "Compliance Assessments",
                "Gap Analysis",
                "Regulatory Mapping"
            ],
            "operations": [
                "Incident Management",
                "Timeline Tracking",
                "Communication Logs",
                "Response Coordination"
            ],
            "tools": [
                "Data Import/Export",
                "Monte Carlo Simulations",
                "What-if Analysis",
                "Scenario Planning"
            ],
            "aml": [
                "Transaction Monitoring",
                "Customer Due Diligence (KYC)",
                "Risk Scoring Engine",
                "Sanctions & Watchlist Screening",
                "Suspicious Activity Reports (SAR)",
                "Currency Transaction Reports (CTR)",
                "Case Management",
                "Real-time Alerts",
                "Pattern Detection",
                "ML-based Risk Assessment"
            ],
            "advanced_ai_ml": [
                "Predictive Fraud Detection",
                "Anomaly Detection Engine",
                "Risk Forecasting Models",
                "Customer Clustering Analysis",
                "Real-time ML Inference",
                "Model Performance Monitoring",
                "Feature Importance Analysis"
            ],
            "blockchain_audit": [
                "Immutable Audit Trails",
                "Blockchain-based Compliance Logging",
                "Cryptographic Data Integrity",
                "Distributed Ledger Technology",
                "Smart Contract Compliance Rules",
                "Tamper-proof Transaction Records"
            ],
            "real_time_streaming": [
                "Complex Event Processing",
                "Real-time Alert Generation",
                "WebSocket Live Feeds",
                "Stream Processing Engine",
                "Event Pattern Recognition",
                "Live Dashboard Updates",
                "Velocity Analysis"
            ],
            "advanced_dashboards": [
                "Interactive BI Dashboards",
                "Executive Summary Views",
                "Custom Dashboard Builder",
                "Real-time Data Visualization",
                "Drill-down Analytics",
                "Multi-format Chart Support",
                "Mobile-responsive Design"
            ],
            "federated_learning": [
                "Privacy-preserving ML",
                "Multi-party Model Training",
                "Differential Privacy",
                "Secure Model Aggregation",
                "Distributed Learning Networks",
                "GDPR-compliant Analytics"
            ],
            "regulatory_automation": [
                "Automated SAR Generation",
                "CTR Report Creation",
                "Compliance Calendar Management",
                "Multi-format Report Export",
                "Regulatory Deadline Tracking",
                "Cross-jurisdiction Reporting"
            ],
            "network_analysis": [
                "Graph Database Analysis",
                "Relationship Mapping",
                "Community Detection",
                "Suspicious Pattern Recognition",
                "Centrality Analysis",
                "Money Laundering Path Detection",
                "Network Visualization"
            ]
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get overall system statistics"""
    from app.models.risk import Risk
    from app.models.control import Control
    from app.models.kri import KeyRiskIndicator
    from app.models.user import User
    from app.models.incident import Incident
    from app.models.assessment import RiskAssessment
    
    return {
        "entities": {
            "users": db.query(User).count(),
            "risks": db.query(Risk).count(),
            "controls": db.query(Control).count(),
            "kris": db.query(KeyRiskIndicator).count(),
            "assessments": db.query(RiskAssessment).count(),
            "incidents": db.query(Incident).count()
        },
        "system_info": {
            "version": settings.VERSION,
            "environment": getattr(settings, 'ENVIRONMENT', 'production'),
            "api_version": settings.API_V1_STR
        }
    }