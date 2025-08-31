"""
System monitoring and health check endpoints
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import psutil
import os
from app.core.database import SessionLocal
from app.core.config import settings

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive system health check"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "components": {}
        }
        
        # Database health
        try:
            db = SessionLocal()
            start_time = datetime.utcnow()
            db.execute(text("SELECT 1"))
            db_response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            db.close()
            
            health_status["components"]["database"] = {
                "status": "healthy",
                "response_time_ms": round(db_response_time, 2),
                "connection": "active"
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # System metrics
        try:
            health_status["components"]["system"] = {
                "status": "healthy",
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "load_average": os.getloadavg()[0] if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            health_status["components"]["system"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        # Application metrics
        try:
            db = SessionLocal()
            
            # Count records in main tables
            tables_info = {}
            for table in ["users", "risks", "kris", "controls", "incidents"]:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    tables_info[table] = count
                except:
                    tables_info[table] = "error"
            
            db.close()
            
            health_status["components"]["application"] = {
                "status": "healthy",
                "data_status": tables_info,
                "features_available": [
                    "risk_management",
                    "kri_monitoring", 
                    "incident_tracking",
                    "controls_management",
                    "user_authentication"
                ]
            }
        except Exception as e:
            health_status["components"]["application"] = {
                "status": "degraded",
                "error": str(e)
            }
        
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@router.get("/metrics")
async def system_metrics():
    """Get system performance metrics"""
    try:
        db = SessionLocal()
        
        # Database metrics
        db_metrics = {}
        for table in ["users", "risks", "kris", "controls", "incidents"]:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                db_metrics[f"{table}_count"] = result.scalar()
            except:
                db_metrics[f"{table}_count"] = 0
        
        # Calculate risk metrics
        try:
            high_risk_result = db.execute(text("SELECT COUNT(*) FROM risks WHERE risk_score >= 15"))
            medium_risk_result = db.execute(text("SELECT COUNT(*) FROM risks WHERE risk_score >= 8 AND risk_score < 15"))
            low_risk_result = db.execute(text("SELECT COUNT(*) FROM risks WHERE risk_score < 8"))
            
            db_metrics.update({
                "high_risks": high_risk_result.scalar(),
                "medium_risks": medium_risk_result.scalar(), 
                "low_risks": low_risk_result.scalar()
            })
        except:
            db_metrics.update({"high_risks": 0, "medium_risks": 0, "low_risks": 0})
        
        # KRI metrics
        try:
            kri_red = db.execute(text("SELECT COUNT(*) FROM kris WHERE status = 'red'")).scalar()
            kri_amber = db.execute(text("SELECT COUNT(*) FROM kris WHERE status = 'amber'")).scalar()
            kri_green = db.execute(text("SELECT COUNT(*) FROM kris WHERE status = 'green'")).scalar()
            
            db_metrics.update({
                "kri_red": kri_red,
                "kri_amber": kri_amber,
                "kri_green": kri_green
            })
        except:
            db_metrics.update({"kri_red": 0, "kri_amber": 0, "kri_green": 0})
        
        db.close()
        
        # System metrics
        system_metrics = {
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "uptime_seconds": psutil.boot_time()
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database_metrics": db_metrics,
            "system_metrics": system_metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")

@router.get("/version")
async def system_version():
    """Get system version and build information"""
    return {
        "application": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "build_time": datetime.utcnow().isoformat(),
        "features": {
            "risk_management": True,
            "kri_monitoring": True,
            "incident_management": True,
            "controls_management": True,
            "user_authentication": True,
            "aml_compliance": True,
            "ai_ml_analytics": True,
            "blockchain_audit": True,
            "real_time_streaming": True,
            "network_analysis": True,
            "regulatory_reporting": True
        }
    }