"""
Oracle ERP Integration API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.risk import Risk
from app.integrations.oracle_erp import oracle_erp_connector, sync_with_oracle_erp

router = APIRouter()

@router.get("/status")
async def get_integration_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get Oracle ERP integration status"""
    return {
        "status": "configured" if oracle_erp_connector.use_mock else "connected",
        "mode": "mock" if oracle_erp_connector.use_mock else "live",
        "last_sync": None,  # Would be tracked in database
        "features": {
            "employee_sync": True,
            "financial_sync": True,
            "vendor_sync": True,
            "risk_push": True,
            "procurement_monitoring": True
        }
    }

@router.post("/sync/employees")
async def sync_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Manually trigger employee synchronization from Oracle ERP"""
    
    if current_user.role not in ["admin", "system"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    oracle_erp_connector.connect_database()
    result = oracle_erp_connector.sync_employees(db)
    oracle_erp_connector.disconnect()
    
    return result

@router.post("/sync/financial")
async def sync_financial_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Manually trigger financial data synchronization from Oracle ERP"""
    
    if current_user.role not in ["admin", "risk_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    oracle_erp_connector.connect_database()
    result = oracle_erp_connector.sync_financial_data(db)
    oracle_erp_connector.disconnect()
    
    return result

@router.post("/sync/vendors")
async def sync_vendor_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Manually trigger vendor data synchronization from Oracle ERP"""
    
    if current_user.role not in ["admin", "risk_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    oracle_erp_connector.connect_database()
    result = oracle_erp_connector.sync_vendor_data(db)
    oracle_erp_connector.disconnect()
    
    return result

@router.post("/sync/all")
async def sync_all(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Trigger full synchronization with Oracle ERP in background"""
    
    if current_user.role not in ["admin", "system"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Add to background tasks
    background_tasks.add_task(sync_with_oracle_erp)
    
    return {
        "status": "started",
        "message": "Full synchronization initiated in background",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/push/risk/{risk_id}")
async def push_risk_to_erp(
    risk_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Push a specific risk to Oracle ERP system"""
    
    # Get the risk
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    oracle_erp_connector.connect_database()
    result = oracle_erp_connector.push_risk_to_erp(risk)
    oracle_erp_connector.disconnect()
    
    return result

@router.get("/procurement/risks")
async def get_procurement_risks(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get procurement-related risks from Oracle ERP"""
    
    oracle_erp_connector.connect_database()
    risks = oracle_erp_connector.get_procurement_risks()
    oracle_erp_connector.disconnect()
    
    return {
        "procurement_risks": risks,
        "total_count": len(risks),
        "high_risk_count": len([r for r in risks if r.get('risk_level') == 'High']),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/config")
async def get_oracle_config(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get Oracle ERP configuration (sanitized)"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "database": {
            "user": oracle_erp_connector.db_config.get('user'),
            "dsn": oracle_erp_connector.db_config.get('dsn'),
            "connected": oracle_erp_connector.connection is not None
        },
        "api": {
            "base_url": oracle_erp_connector.rest_api_base,
            "has_key": bool(oracle_erp_connector.api_key)
        },
        "mode": "mock" if oracle_erp_connector.use_mock else "live"
    }

@router.post("/test-connection")
async def test_oracle_connection(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Test Oracle ERP connection"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        success = oracle_erp_connector.connect_database()
        
        if success and not oracle_erp_connector.use_mock:
            # Try a simple query
            cursor = oracle_erp_connector.connection.cursor()
            cursor.execute("SELECT SYSDATE FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
            oracle_erp_connector.disconnect()
            
            return {
                "status": "success",
                "connected": True,
                "server_time": str(result[0]) if result else None,
                "mode": "live"
            }
        else:
            return {
                "status": "success",
                "connected": False,
                "mode": "mock",
                "message": "Using mock data - Oracle connection not configured"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
            "mode": "mock"
        }