"""
Oracle ERP Integration API endpoints
Connects NAPSA ERM with Oracle ERP systems
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import cx_Oracle
import os
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.risk import Risk
from app.models.incident import Incident

router = APIRouter(prefix="/oracle-erp", tags=["Oracle ERP Integration"])

# Oracle connection configuration
ORACLE_CONFIG = {
    "host": os.getenv("ORACLE_HOST", "localhost"),
    "port": os.getenv("ORACLE_PORT", "1521"),
    "service_name": os.getenv("ORACLE_SERVICE", "ORCL"),
    "user": os.getenv("ORACLE_USER", "napsa_integration"),
    "password": os.getenv("ORACLE_PASSWORD", ""),
    "encoding": "UTF-8"
}

class OracleConnection:
    """Oracle database connection manager"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish Oracle connection"""
        try:
            dsn = cx_Oracle.makedsn(
                ORACLE_CONFIG["host"],
                ORACLE_CONFIG["port"],
                service_name=ORACLE_CONFIG["service_name"]
            )
            
            self.connection = cx_Oracle.connect(
                user=ORACLE_CONFIG["user"],
                password=ORACLE_CONFIG["password"],
                dsn=dsn,
                encoding=ORACLE_CONFIG["encoding"]
            )
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"Oracle connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close Oracle connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute SELECT query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            columns = [col[0] for col in self.cursor.description]
            rows = self.cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Query execution failed: {e}")
            return []
    
    def execute_update(self, query: str, params: Dict = None) -> bool:
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Update execution failed: {e}")
            self.connection.rollback()
            return False

# Data models for Oracle ERP integration
class FinancialRiskData(BaseModel):
    gl_account: str
    account_name: str
    balance: float
    currency: str
    risk_indicator: Optional[str]
    threshold_breach: bool = False

class VendorRiskData(BaseModel):
    vendor_id: str
    vendor_name: str
    vendor_type: str
    risk_score: float
    payment_terms: str
    total_spend: float
    compliance_status: str

class TransactionAnomalyData(BaseModel):
    transaction_id: str
    transaction_date: datetime
    amount: float
    description: str
    anomaly_type: str
    risk_level: str

class AssetRiskData(BaseModel):
    asset_id: str
    asset_name: str
    asset_value: float
    depreciation: float
    maintenance_due: bool
    risk_factors: List[str]

# API Endpoints
@router.get("/connection-status")
def check_connection_status(
    current_user: User = Depends(get_current_user)
):
    """Check Oracle ERP connection status"""
    oracle = OracleConnection()
    connected = oracle.connect()
    
    if connected:
        oracle.disconnect()
        return {
            "status": "connected",
            "host": ORACLE_CONFIG["host"],
            "service": ORACLE_CONFIG["service_name"],
            "message": "Oracle ERP connection successful"
        }
    else:
        return {
            "status": "disconnected",
            "message": "Failed to connect to Oracle ERP"
        }

@router.get("/financial-risks", response_model=List[FinancialRiskData])
def get_financial_risks(
    account_type: Optional[str] = None,
    threshold_amount: float = Query(default=1000000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch financial risks from Oracle GL (General Ledger)"""
    
    oracle = OracleConnection()
    if not oracle.connect():
        raise HTTPException(status_code=500, detail="Oracle connection failed")
    
    try:
        # Query Oracle GL tables
        query = """
        SELECT 
            gcc.segment1 || '.' || gcc.segment2 || '.' || gcc.segment3 as gl_account,
            ffv.description as account_name,
            gb.period_net_dr - gb.period_net_cr as balance,
            gb.currency_code as currency,
            CASE 
                WHEN ABS(gb.period_net_dr - gb.period_net_cr) > :threshold THEN 'HIGH'
                WHEN ABS(gb.period_net_dr - gb.period_net_cr) > :threshold/2 THEN 'MEDIUM'
                ELSE 'LOW'
            END as risk_indicator,
            CASE 
                WHEN ABS(gb.period_net_dr - gb.period_net_cr) > :threshold THEN 1
                ELSE 0
            END as threshold_breach
        FROM 
            gl_balances gb,
            gl_code_combinations gcc,
            fnd_flex_values_vl ffv
        WHERE 
            gb.code_combination_id = gcc.code_combination_id
            AND gcc.segment2 = ffv.flex_value
            AND gb.actual_flag = 'A'
            AND gb.period_name = :period
        """
        
        params = {
            "threshold": threshold_amount,
            "period": datetime.now().strftime("%b-%y").upper()
        }
        
        if account_type:
            query += " AND ffv.description LIKE :account_type"
            params["account_type"] = f"%{account_type}%"
        
        results = oracle.execute_query(query, params)
        
        # Convert to risk data format
        financial_risks = []
        for row in results:
            financial_risks.append(FinancialRiskData(
                gl_account=row.get("GL_ACCOUNT", ""),
                account_name=row.get("ACCOUNT_NAME", ""),
                balance=float(row.get("BALANCE", 0)),
                currency=row.get("CURRENCY", "ZMW"),
                risk_indicator=row.get("RISK_INDICATOR", "LOW"),
                threshold_breach=bool(row.get("THRESHOLD_BREACH", 0))
            ))
        
        # Create risks in ERM system for high-risk items
        for risk_data in financial_risks:
            if risk_data.threshold_breach:
                risk = Risk(
                    title=f"Financial Risk - {risk_data.account_name}",
                    description=f"GL Account {risk_data.gl_account} has balance of {risk_data.currency} {risk_data.balance:,.2f} exceeding threshold",
                    category="financial",
                    likelihood=3,
                    impact=4,
                    risk_source="Oracle ERP Integration",
                    department="Finance",
                    created_at=datetime.utcnow()
                )
                db.add(risk)
        
        db.commit()
        
        return financial_risks
        
    finally:
        oracle.disconnect()

@router.get("/vendor-risks", response_model=List[VendorRiskData])
def get_vendor_risks(
    min_risk_score: float = Query(default=7.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch vendor risks from Oracle Payables"""
    
    oracle = OracleConnection()
    if not oracle.connect():
        raise HTTPException(status_code=500, detail="Oracle connection failed")
    
    try:
        query = """
        SELECT 
            pv.vendor_id,
            pv.vendor_name,
            pv.vendor_type_lookup_code as vendor_type,
            NVL(pv.credit_rating, 5) * 2 as risk_score,
            apt.name as payment_terms,
            SUM(api.invoice_amount) as total_spend,
            CASE 
                WHEN pv.hold_flag = 'Y' THEN 'ON_HOLD'
                WHEN pv.enabled_flag = 'N' THEN 'DISABLED'
                ELSE 'ACTIVE'
            END as compliance_status
        FROM 
            po_vendors pv,
            ap_terms apt,
            ap_invoices_all api
        WHERE 
            pv.terms_id = apt.term_id(+)
            AND pv.vendor_id = api.vendor_id(+)
            AND pv.creation_date > SYSDATE - 365
        GROUP BY 
            pv.vendor_id, pv.vendor_name, pv.vendor_type_lookup_code,
            pv.credit_rating, apt.name, pv.hold_flag, pv.enabled_flag
        HAVING 
            NVL(pv.credit_rating, 5) * 2 >= :min_risk
        """
        
        params = {"min_risk": min_risk_score}
        results = oracle.execute_query(query, params)
        
        vendor_risks = []
        for row in results:
            vendor_risk = VendorRiskData(
                vendor_id=str(row.get("VENDOR_ID", "")),
                vendor_name=row.get("VENDOR_NAME", ""),
                vendor_type=row.get("VENDOR_TYPE", ""),
                risk_score=float(row.get("RISK_SCORE", 0)),
                payment_terms=row.get("PAYMENT_TERMS", ""),
                total_spend=float(row.get("TOTAL_SPEND", 0)),
                compliance_status=row.get("COMPLIANCE_STATUS", "")
            )
            vendor_risks.append(vendor_risk)
            
            # Create risk if score is high
            if vendor_risk.risk_score >= 8:
                risk = Risk(
                    title=f"Vendor Risk - {vendor_risk.vendor_name}",
                    description=f"High-risk vendor with score {vendor_risk.risk_score}/10. Total spend: ZMW {vendor_risk.total_spend:,.2f}",
                    category="operational",
                    likelihood=4,
                    impact=3,
                    risk_source="Oracle ERP - Vendor Management",
                    department="Procurement",
                    created_at=datetime.utcnow()
                )
                db.add(risk)
        
        db.commit()
        return vendor_risks
        
    finally:
        oracle.disconnect()

@router.get("/transaction-anomalies", response_model=List[TransactionAnomalyData])
def get_transaction_anomalies(
    days_back: int = Query(default=30),
    min_amount: float = Query(default=100000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detect transaction anomalies from Oracle ERP"""
    
    oracle = OracleConnection()
    if not oracle.connect():
        raise HTTPException(status_code=500, detail="Oracle connection failed")
    
    try:
        query = """
        SELECT 
            gjh.je_header_id as transaction_id,
            gjh.default_effective_date as transaction_date,
            ABS(gjl.entered_dr - gjl.entered_cr) as amount,
            gjh.description,
            CASE 
                WHEN gjh.je_source = 'Manual' AND ABS(gjl.entered_dr - gjl.entered_cr) > :threshold THEN 'MANUAL_HIGH_VALUE'
                WHEN gjh.reversed_je_header_id IS NOT NULL THEN 'REVERSAL'
                WHEN gjh.actual_flag != 'A' THEN 'NON_ACTUAL'
                WHEN gjl.entered_dr = gjl.entered_cr THEN 'ZERO_NET'
                ELSE 'NORMAL'
            END as anomaly_type,
            CASE 
                WHEN ABS(gjl.entered_dr - gjl.entered_cr) > :threshold * 2 THEN 'HIGH'
                WHEN ABS(gjl.entered_dr - gjl.entered_cr) > :threshold THEN 'MEDIUM'
                ELSE 'LOW'
            END as risk_level
        FROM 
            gl_je_headers gjh,
            gl_je_lines gjl
        WHERE 
            gjh.je_header_id = gjl.je_header_id
            AND gjh.default_effective_date > SYSDATE - :days
            AND ABS(gjl.entered_dr - gjl.entered_cr) > :min_amount
            AND gjh.je_source = 'Manual'
        ORDER BY 
            gjh.default_effective_date DESC
        """
        
        params = {
            "threshold": min_amount * 2,
            "days": days_back,
            "min_amount": min_amount
        }
        
        results = oracle.execute_query(query, params)
        
        anomalies = []
        for row in results:
            anomaly = TransactionAnomalyData(
                transaction_id=str(row.get("TRANSACTION_ID", "")),
                transaction_date=row.get("TRANSACTION_DATE", datetime.now()),
                amount=float(row.get("AMOUNT", 0)),
                description=row.get("DESCRIPTION", ""),
                anomaly_type=row.get("ANOMALY_TYPE", ""),
                risk_level=row.get("RISK_LEVEL", "LOW")
            )
            anomalies.append(anomaly)
            
            # Create incident for high-risk anomalies
            if anomaly.risk_level == "HIGH":
                incident = Incident(
                    title=f"Transaction Anomaly - {anomaly.anomaly_type}",
                    description=f"Detected anomaly in transaction {anomaly.transaction_id}: {anomaly.description}. Amount: ZMW {anomaly.amount:,.2f}",
                    severity="high",
                    department="Finance",
                    incident_type="financial_anomaly",
                    created_at=datetime.utcnow()
                )
                db.add(incident)
        
        db.commit()
        return anomalies
        
    finally:
        oracle.disconnect()

@router.get("/asset-risks", response_model=List[AssetRiskData])
def get_asset_risks(
    include_depreciated: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch asset risks from Oracle Fixed Assets"""
    
    oracle = OracleConnection()
    if not oracle.connect():
        raise HTTPException(status_code=500, detail="Oracle connection failed")
    
    try:
        query = """
        SELECT 
            fa.asset_id,
            fa.asset_number || ' - ' || fa.description as asset_name,
            fb.cost as asset_value,
            fb.deprn_reserve as depreciation,
            CASE 
                WHEN fa.last_maintenance_date < SYSDATE - 365 THEN 1
                ELSE 0
            END as maintenance_due
        FROM 
            fa_additions fa,
            fa_books fb
        WHERE 
            fa.asset_id = fb.asset_id
            AND fb.date_ineffective IS NULL
        """
        
        if not include_depreciated:
            query += " AND fb.cost > fb.deprn_reserve"
        
        results = oracle.execute_query(query)
        
        asset_risks = []
        for row in results:
            risk_factors = []
            
            # Determine risk factors
            if row.get("MAINTENANCE_DUE", 0):
                risk_factors.append("Overdue maintenance")
            
            depreciation_rate = row.get("DEPRECIATION", 0) / row.get("ASSET_VALUE", 1) if row.get("ASSET_VALUE", 0) > 0 else 0
            if depreciation_rate > 0.8:
                risk_factors.append("High depreciation")
            
            asset_risk = AssetRiskData(
                asset_id=str(row.get("ASSET_ID", "")),
                asset_name=row.get("ASSET_NAME", ""),
                asset_value=float(row.get("ASSET_VALUE", 0)),
                depreciation=float(row.get("DEPRECIATION", 0)),
                maintenance_due=bool(row.get("MAINTENANCE_DUE", 0)),
                risk_factors=risk_factors
            )
            asset_risks.append(asset_risk)
        
        return asset_risks
        
    finally:
        oracle.disconnect()

@router.post("/sync-risks")
def sync_risks_with_oracle(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync risks between NAPSA ERM and Oracle ERP"""
    
    oracle = OracleConnection()
    if not oracle.connect():
        raise HTTPException(status_code=500, detail="Oracle connection failed")
    
    try:
        # Export high-priority risks to Oracle
        high_risks = db.query(Risk).filter(
            Risk.inherent_risk_score >= 15,
            Risk.status == 'active'
        ).all()
        
        exported_count = 0
        for risk in high_risks:
            # Insert into Oracle custom table
            query = """
            INSERT INTO napsa_erm_risks (
                risk_id, risk_title, risk_description, 
                risk_score, risk_category, created_date
            ) VALUES (
                :risk_id, :title, :description,
                :score, :category, :created_date
            )
            """
            
            params = {
                "risk_id": risk.id,
                "title": risk.title[:100],
                "description": risk.description[:500] if risk.description else "",
                "score": risk.inherent_risk_score,
                "category": risk.category,
                "created_date": risk.created_at
            }
            
            if oracle.execute_update(query, params):
                exported_count += 1
        
        # Import Oracle-identified risks
        query = """
        SELECT 
            oracle_risk_id, risk_description, risk_type,
            likelihood, impact, identified_date
        FROM 
            oracle_identified_risks
        WHERE 
            sync_status = 'PENDING'
        """
        
        oracle_risks = oracle.execute_query(query)
        imported_count = 0
        
        for oracle_risk in oracle_risks:
            risk = Risk(
                title=f"Oracle ERP - {oracle_risk.get('RISK_TYPE', 'Unknown')}",
                description=oracle_risk.get("RISK_DESCRIPTION", ""),
                category="financial" if "FIN" in oracle_risk.get("RISK_TYPE", "") else "operational",
                likelihood=int(oracle_risk.get("LIKELIHOOD", 3)),
                impact=int(oracle_risk.get("IMPACT", 3)),
                risk_source="Oracle ERP Auto-Detection",
                department="Finance",
                created_at=datetime.utcnow()
            )
            db.add(risk)
            imported_count += 1
            
            # Mark as synced in Oracle
            update_query = """
            UPDATE oracle_identified_risks 
            SET sync_status = 'SYNCED', sync_date = SYSDATE
            WHERE oracle_risk_id = :risk_id
            """
            oracle.execute_update(update_query, {"risk_id": oracle_risk.get("ORACLE_RISK_ID")})
        
        db.commit()
        
        return {
            "status": "success",
            "exported_to_oracle": exported_count,
            "imported_from_oracle": imported_count,
            "message": f"Successfully synced {exported_count + imported_count} risks"
        }
        
    finally:
        oracle.disconnect()

@router.get("/integration-logs")
def get_integration_logs(
    days: int = Query(default=7),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Oracle ERP integration logs"""
    
    oracle = OracleConnection()
    if not oracle.connect():
        return {
            "status": "error",
            "message": "Cannot retrieve logs - Oracle connection failed"
        }
    
    try:
        query = """
        SELECT 
            log_id, log_date, operation_type, 
            record_count, status, error_message
        FROM 
            napsa_integration_logs
        WHERE 
            log_date > SYSDATE - :days
        ORDER BY 
            log_date DESC
        """
        
        logs = oracle.execute_query(query, {"days": days})
        
        return {
            "total_logs": len(logs),
            "period_days": days,
            "logs": logs
        }
        
    finally:
        oracle.disconnect()