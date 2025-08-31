"""
NAPSA ERM API - Live Data Version
Using actual database without complex dependencies
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.v1 import auth, users, risks, assessments, assessment_periods, controls, incidents
from app.api.v1.treatments_proper import router as treatments_router
from app.api.v1.kri_proper import router as kri_router
from app.api.v1.reports import router as reports_router

# Import new enhanced APIs
try:
    from app.api.v1.branches import router as branches_router
    has_branches = True
except ImportError:
    has_branches = False

try:
    from app.api.v1.executive_dashboard import router as executive_router
    has_executive = True
except ImportError:
    has_executive = False

try:
    from app.api.v1.organizational_units import router as org_units_router
    has_org_units = True
except ImportError:
    has_org_units = False

try:
    from app.api.v1.kris_enhanced import router as kris_enhanced_router
    has_kris_enhanced = True
except ImportError:
    has_kris_enhanced = False

try:
    from app.api.v1.rcsa_enhanced import router as rcsa_enhanced_router
    has_rcsa_enhanced = True
except ImportError:
    has_rcsa_enhanced = False

# Import additional routers if they exist
try:
    from app.api.v1.oracle_integration import router as oracle_router
    has_oracle = True
except ImportError:
    has_oracle = False

try:
    from app.api.v1.notifications import router as notifications_router
    has_notifications = True
except ImportError:
    has_notifications = False

try:
    from app.api.v1.rcsa import router as rcsa_router
    has_rcsa = True
except ImportError:
    has_rcsa = False

try:
    from app.api.v1.departments import router as departments_router
    has_departments = True
except ImportError:
    has_departments = False

try:
    from app.integrations.routes import router as integrations_router
    has_integrations = True
except ImportError:
    has_integrations = False

try:
    from app.api.v1.bi_tools_simple import router as bi_tools_router
    has_bi_tools = True
except ImportError:
    try:
        from app.api.v1.bi_tools import router as bi_tools_router
        has_bi_tools = True
    except ImportError:
        has_bi_tools = False

try:
    from app.api.v1.aml_simple import router as aml_router
    has_aml = True
except ImportError:
    try:
        from app.api.v1.aml import router as aml_router
        has_aml = True
    except ImportError:
        has_aml = False

try:
    from app.api.v1.regulations_simple import router as regulations_router
    has_regulations = True
except ImportError:
    has_regulations = False

try:
    from app.api.v1.analytics_simple import router as analytics_router
    has_analytics = True
except ImportError:
    try:
        from app.api.v1.analytics import router as analytics_router
        has_analytics = True
    except ImportError:
        has_analytics = False

try:
    from app.api.v1.risk_categories import router as risk_categories_router
    has_risk_categories = True
except ImportError:
    has_risk_categories = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting NAPSA ERM API with Live Data...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NAPSA ERM API...")

# Create FastAPI app
app = FastAPI(
    title="NAPSA ERM API",
    description="Enterprise Risk Management System API with Live Data",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
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

# Include core routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(risks.router, prefix=f"{settings.API_V1_STR}/risks", tags=["risks"])
app.include_router(assessments.router, prefix=f"{settings.API_V1_STR}/assessments", tags=["assessments"])
app.include_router(assessment_periods.router, prefix=f"{settings.API_V1_STR}/assessment-periods", tags=["assessment-periods"])
app.include_router(controls.router, prefix=f"{settings.API_V1_STR}/controls", tags=["controls"])
app.include_router(treatments_router, prefix=f"{settings.API_V1_STR}/treatments", tags=["treatments"])
app.include_router(kri_router, prefix=f"{settings.API_V1_STR}/kri", tags=["kri"])
app.include_router(incidents.router, prefix=f"{settings.API_V1_STR}/incidents", tags=["incidents"])
app.include_router(reports_router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])

# Include optional routers
if has_oracle:
    app.include_router(oracle_router, prefix=f"{settings.API_V1_STR}/oracle", tags=["oracle"])
if has_notifications:
    app.include_router(notifications_router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
if has_rcsa:
    app.include_router(rcsa_router, prefix=f"{settings.API_V1_STR}/rcsa", tags=["rcsa"])
if has_departments:
    app.include_router(departments_router, prefix=f"{settings.API_V1_STR}/departments", tags=["departments"])
if has_integrations:
    app.include_router(integrations_router, prefix=settings.API_V1_STR)
if has_bi_tools:
    app.include_router(bi_tools_router, prefix=f"{settings.API_V1_STR}/bi-tools", tags=["bi-tools"])
if has_aml:
    app.include_router(aml_router, prefix=f"{settings.API_V1_STR}/aml", tags=["aml"])
if has_regulations:
    app.include_router(regulations_router, prefix=f"{settings.API_V1_STR}/regulations", tags=["regulations"])
if has_analytics:
    app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
if has_risk_categories:
    app.include_router(risk_categories_router, prefix=f"{settings.API_V1_STR}/risk-categories", tags=["Risk Categories"])

# Include new enhanced routers
if has_branches:
    app.include_router(branches_router, prefix=f"{settings.API_V1_STR}/branches", tags=["Branch Management"])
if has_executive:
    app.include_router(executive_router, prefix=f"{settings.API_V1_STR}/executive-dashboard", tags=["Executive Dashboard"])
if has_org_units:
    app.include_router(org_units_router, prefix=f"{settings.API_V1_STR}/organizational-units", tags=["Organizational Units"])
if has_kris_enhanced:
    app.include_router(kris_enhanced_router, prefix=f"{settings.API_V1_STR}/kris-enhanced", tags=["Enhanced KRIs"])
if has_rcsa_enhanced:
    app.include_router(rcsa_enhanced_router, prefix=f"{settings.API_V1_STR}/rcsa-enhanced", tags=["Enhanced RCSA"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NAPSA ERM API - Live Data",
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = SessionLocal()
        # Test database connection
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.VERSION
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.get(f"{settings.API_V1_STR}/dashboards/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        db = SessionLocal()
        
        # Count total risks
        result = db.execute(text("SELECT COUNT(*) FROM risks"))
        total_risks = result.scalar() or 0
        
        # Count high risks (using inherent_risk_score)
        result = db.execute(text("SELECT COUNT(*) FROM risks WHERE inherent_risk_score >= 15"))
        high_risk_count = result.scalar() or 0
        
        # Count open incidents  
        result = db.execute(text("SELECT COUNT(*) FROM incidents WHERE status != 'resolved'"))
        open_incidents = result.scalar() or 0
        
        # Count KRI breaches - check if table exists first
        try:
            result = db.execute(text("SELECT COUNT(*) FROM kris WHERE status IN ('amber', 'red')"))
            kri_breaches = result.scalar() or 0
        except:
            kri_breaches = 0
        
        db.close()
        
        return {
            "data": {
                "total_risks": total_risks,
                "high_risk_count": high_risk_count, 
                "open_incidents": open_incidents,
                "kri_breaches": kri_breaches,
                "aml_alerts": 23,  # Mock data for now
                "suspicious_transactions": 156  # Mock data for now
            },
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)