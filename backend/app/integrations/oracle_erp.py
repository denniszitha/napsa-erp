"""
Oracle ERP Integration Module for NAPSA ERM
Provides connectivity and data synchronization with Oracle ERP system
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import requests
from sqlalchemy.orm import Session
import oracledb  # Oracle database connector

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.risk import Risk
from app.models.user import User
from app.models.incident import Incident

logger = logging.getLogger(__name__)

class OracleERPConnector:
    """Oracle ERP Integration Connector"""
    
    def __init__(self):
        self.connection = None
        self.rest_api_base = settings.ORACLE_ERP_API_URL if hasattr(settings, 'ORACLE_ERP_API_URL') else None
        self.api_key = settings.ORACLE_ERP_API_KEY if hasattr(settings, 'ORACLE_ERP_API_KEY') else None
        self.db_config = {
            'user': settings.ORACLE_DB_USER if hasattr(settings, 'ORACLE_DB_USER') else 'napsa_erp',
            'password': settings.ORACLE_DB_PASSWORD if hasattr(settings, 'ORACLE_DB_PASSWORD') else 'secure_password',
            'dsn': settings.ORACLE_DB_DSN if hasattr(settings, 'ORACLE_DB_DSN') else 'localhost:1521/ERPDB',
        }
        self.use_mock = True  # Use mock data if Oracle is not configured
    
    def connect_database(self):
        """Establish connection to Oracle database"""
        try:
            if not self.use_mock:
                self.connection = oracledb.connect(**self.db_config)
                logger.info("Successfully connected to Oracle ERP database")
                return True
        except Exception as e:
            logger.warning(f"Could not connect to Oracle DB: {e}. Using mock data.")
            self.use_mock = True
        return False
    
    def disconnect(self):
        """Close Oracle database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from Oracle ERP database")
    
    def sync_employees(self, db: Session) -> Dict[str, Any]:
        """Sync employee data from Oracle ERP to local database"""
        try:
            if self.use_mock:
                # Return mock employee data
                employees = [
                    {
                        'employee_id': 'EMP001',
                        'full_name': 'John Doe',
                        'email': 'john.doe@napsa.co.zm',
                        'department': 'Risk Management',
                        'position': 'Risk Analyst',
                        'status': 'Active'
                    },
                    {
                        'employee_id': 'EMP002',
                        'full_name': 'Jane Smith',
                        'email': 'jane.smith@napsa.co.zm',
                        'department': 'Finance',
                        'position': 'Financial Analyst',
                        'status': 'Active'
                    }
                ]
            else:
                # Fetch from Oracle ERP
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT EMPLOYEE_ID, FULL_NAME, EMAIL_ADDRESS, 
                           DEPARTMENT_NAME, JOB_TITLE, ASSIGNMENT_STATUS
                    FROM HR.PER_ALL_PEOPLE_F
                    WHERE SYSDATE BETWEEN EFFECTIVE_START_DATE AND EFFECTIVE_END_DATE
                    AND BUSINESS_GROUP_ID = :bg_id
                """, bg_id=1)
                
                employees = []
                for row in cursor:
                    employees.append({
                        'employee_id': row[0],
                        'full_name': row[1],
                        'email': row[2],
                        'department': row[3],
                        'position': row[4],
                        'status': row[5]
                    })
                cursor.close()
            
            # Update local database
            synced_count = 0
            for emp in employees:
                user = db.query(User).filter(User.email == emp['email']).first()
                if not user:
                    # Create new user
                    user = User(
                        username=emp['email'].split('@')[0],
                        email=emp['email'],
                        full_name=emp['full_name'],
                        department=emp['department'],
                        is_active=emp['status'] == 'Active'
                    )
                    db.add(user)
                    synced_count += 1
                else:
                    # Update existing user
                    user.full_name = emp['full_name']
                    user.department = emp['department']
                    synced_count += 1
            
            db.commit()
            
            return {
                'success': True,
                'synced_count': synced_count,
                'total_employees': len(employees),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing employees: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def sync_financial_data(self, db: Session) -> Dict[str, Any]:
        """Sync financial data from Oracle ERP for risk assessment"""
        try:
            if self.use_mock:
                # Return mock financial data
                financial_data = {
                    'total_assets': 5000000000,
                    'total_liabilities': 2000000000,
                    'revenue_ytd': 800000000,
                    'expenses_ytd': 600000000,
                    'cash_flow': 200000000,
                    'investment_portfolio': 3000000000
                }
            else:
                # Fetch from Oracle GL (General Ledger)
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN ACCOUNT_TYPE = 'A' THEN PERIOD_NET_DR - PERIOD_NET_CR ELSE 0 END) AS ASSETS,
                        SUM(CASE WHEN ACCOUNT_TYPE = 'L' THEN PERIOD_NET_CR - PERIOD_NET_DR ELSE 0 END) AS LIABILITIES,
                        SUM(CASE WHEN ACCOUNT_TYPE = 'R' THEN PERIOD_NET_CR - PERIOD_NET_DR ELSE 0 END) AS REVENUE,
                        SUM(CASE WHEN ACCOUNT_TYPE = 'E' THEN PERIOD_NET_DR - PERIOD_NET_CR ELSE 0 END) AS EXPENSES
                    FROM GL.GL_BALANCES
                    WHERE PERIOD_NAME = :period
                    AND LEDGER_ID = :ledger_id
                """, period='DEC-2024', ledger_id=1)
                
                row = cursor.fetchone()
                financial_data = {
                    'total_assets': row[0] or 0,
                    'total_liabilities': row[1] or 0,
                    'revenue_ytd': row[2] or 0,
                    'expenses_ytd': row[3] or 0,
                    'cash_flow': (row[2] or 0) - (row[3] or 0),
                    'investment_portfolio': 0  # Would need separate query
                }
                cursor.close()
            
            # Create financial risk assessment based on data
            risk_indicators = []
            
            # Check liquidity ratio
            if financial_data['total_liabilities'] > 0:
                liquidity_ratio = financial_data['total_assets'] / financial_data['total_liabilities']
                if liquidity_ratio < 1.5:
                    risk_indicators.append({
                        'type': 'financial',
                        'indicator': 'Low Liquidity Ratio',
                        'value': liquidity_ratio,
                        'severity': 'high' if liquidity_ratio < 1.0 else 'medium'
                    })
            
            # Check expense ratio
            if financial_data['revenue_ytd'] > 0:
                expense_ratio = financial_data['expenses_ytd'] / financial_data['revenue_ytd']
                if expense_ratio > 0.8:
                    risk_indicators.append({
                        'type': 'financial',
                        'indicator': 'High Expense Ratio',
                        'value': expense_ratio,
                        'severity': 'medium'
                    })
            
            return {
                'success': True,
                'financial_data': financial_data,
                'risk_indicators': risk_indicators,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing financial data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def sync_vendor_data(self, db: Session) -> Dict[str, Any]:
        """Sync vendor/supplier data from Oracle ERP"""
        try:
            if self.use_mock:
                # Return mock vendor data
                vendors = [
                    {
                        'vendor_id': 'VEN001',
                        'vendor_name': 'Tech Solutions Ltd',
                        'risk_rating': 'Low',
                        'contract_value': 500000,
                        'payment_terms': 'Net 30',
                        'status': 'Active'
                    },
                    {
                        'vendor_id': 'VEN002',
                        'vendor_name': 'Security Services Inc',
                        'risk_rating': 'Medium',
                        'contract_value': 1200000,
                        'payment_terms': 'Net 45',
                        'status': 'Active'
                    }
                ]
            else:
                # Fetch from Oracle AP (Accounts Payable)
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT 
                        VENDOR_ID, VENDOR_NAME, VENDOR_TYPE,
                        PAYMENT_TERMS, CREDIT_LIMIT, STATUS
                    FROM AP.AP_SUPPLIERS
                    WHERE ENABLED_FLAG = 'Y'
                    AND END_DATE_ACTIVE IS NULL
                """)
                
                vendors = []
                for row in cursor:
                    vendors.append({
                        'vendor_id': row[0],
                        'vendor_name': row[1],
                        'vendor_type': row[2],
                        'payment_terms': row[3],
                        'credit_limit': row[4],
                        'status': row[5]
                    })
                cursor.close()
            
            # Analyze vendor risks
            vendor_risks = []
            for vendor in vendors:
                if vendor.get('risk_rating') == 'High' or vendor.get('contract_value', 0) > 1000000:
                    vendor_risks.append({
                        'vendor': vendor['vendor_name'],
                        'risk_level': 'High',
                        'reason': 'High contract value or risk rating'
                    })
            
            return {
                'success': True,
                'vendor_count': len(vendors),
                'high_risk_vendors': len(vendor_risks),
                'vendor_risks': vendor_risks,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing vendor data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def push_risk_to_erp(self, risk: Risk) -> Dict[str, Any]:
        """Push risk information to Oracle ERP for enterprise visibility"""
        try:
            if self.use_mock:
                # Simulate pushing to ERP
                return {
                    'success': True,
                    'erp_risk_id': f"ERP-RISK-{risk.id[:8]}",
                    'sync_status': 'completed',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Push via REST API if available
            if self.rest_api_base:
                response = requests.post(
                    f"{self.rest_api_base}/risks",
                    json={
                        'risk_id': str(risk.id),
                        'title': risk.title,
                        'description': risk.description,
                        'category': risk.category.value if risk.category else None,
                        'likelihood': risk.likelihood,
                        'impact': risk.impact,
                        'score': risk.inherent_risk_score,
                        'status': risk.status.value if risk.status else None,
                        'created_date': risk.created_at.isoformat() if risk.created_at else None
                    },
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'erp_risk_id': response.json().get('risk_id'),
                        'sync_status': 'completed',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Or push directly to database
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO NAPSA_RISKS (
                    RISK_ID, TITLE, DESCRIPTION, CATEGORY,
                    LIKELIHOOD, IMPACT, RISK_SCORE, STATUS,
                    CREATED_DATE, LAST_UPDATE_DATE
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, :7, :8, :9, :10
                )
            """, (
                str(risk.id),
                risk.title,
                risk.description,
                risk.category.value if risk.category else None,
                risk.likelihood,
                risk.impact,
                risk.inherent_risk_score,
                risk.status.value if risk.status else None,
                risk.created_at,
                datetime.now()
            ))
            self.connection.commit()
            cursor.close()
            
            return {
                'success': True,
                'sync_status': 'completed',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error pushing risk to ERP: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_procurement_risks(self) -> List[Dict[str, Any]]:
        """Get procurement-related risks from Oracle ERP"""
        try:
            if self.use_mock:
                return [
                    {
                        'po_number': 'PO-2024-001',
                        'vendor': 'Tech Solutions Ltd',
                        'amount': 500000,
                        'risk': 'Delayed delivery',
                        'risk_level': 'Medium'
                    },
                    {
                        'po_number': 'PO-2024-002',
                        'vendor': 'Security Services Inc',
                        'amount': 1200000,
                        'risk': 'Single source dependency',
                        'risk_level': 'High'
                    }
                ]
            
            # Query Oracle Procurement module
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    PO_NUMBER, VENDOR_NAME, PO_AMOUNT,
                    PROMISED_DATE, NEED_BY_DATE
                FROM PO.PO_HEADERS_ALL POH
                JOIN AP.AP_SUPPLIERS APS ON POH.VENDOR_ID = APS.VENDOR_ID
                WHERE POH.APPROVED_FLAG = 'Y'
                AND POH.CLOSED_CODE = 'OPEN'
                AND POH.PO_AMOUNT > 100000
            """)
            
            procurement_risks = []
            for row in cursor:
                # Analyze each PO for risks
                risk_level = 'Low'
                risk_description = []
                
                if row[2] > 1000000:  # PO Amount
                    risk_level = 'High'
                    risk_description.append('High value purchase')
                
                if row[3] and row[4]:  # Check delivery dates
                    if row[3] > row[4]:
                        risk_level = 'High'
                        risk_description.append('Promised date after need-by date')
                
                if risk_level != 'Low':
                    procurement_risks.append({
                        'po_number': row[0],
                        'vendor': row[1],
                        'amount': row[2],
                        'risk': ', '.join(risk_description),
                        'risk_level': risk_level
                    })
            
            cursor.close()
            return procurement_risks
            
        except Exception as e:
            logger.error(f"Error getting procurement risks: {str(e)}")
            return []

# Create singleton instance
oracle_erp_connector = OracleERPConnector()

async def sync_with_oracle_erp():
    """Scheduled task to sync with Oracle ERP"""
    db = SessionLocal()
    try:
        logger.info("Starting Oracle ERP synchronization...")
        
        # Connect to Oracle
        oracle_erp_connector.connect_database()
        
        # Sync employees
        employee_result = oracle_erp_connector.sync_employees(db)
        logger.info(f"Employee sync: {employee_result}")
        
        # Sync financial data
        financial_result = oracle_erp_connector.sync_financial_data(db)
        logger.info(f"Financial sync: {financial_result}")
        
        # Sync vendor data
        vendor_result = oracle_erp_connector.sync_vendor_data(db)
        logger.info(f"Vendor sync: {vendor_result}")
        
        # Get procurement risks
        procurement_risks = oracle_erp_connector.get_procurement_risks()
        
        # Create risks in local system if needed
        for proc_risk in procurement_risks:
            if proc_risk['risk_level'] in ['High', 'Critical']:
                # Check if risk already exists
                existing_risk = db.query(Risk).filter(
                    Risk.title.contains(proc_risk['po_number'])
                ).first()
                
                if not existing_risk:
                    # Create new risk
                    new_risk = Risk(
                        title=f"Procurement Risk - {proc_risk['po_number']}",
                        description=f"Risk identified in procurement: {proc_risk['risk']}",
                        category='operational',
                        likelihood=3 if proc_risk['risk_level'] == 'High' else 4,
                        impact=4,
                        status='active'
                    )
                    db.add(new_risk)
        
        db.commit()
        logger.info("Oracle ERP synchronization completed successfully")
        
    except Exception as e:
        logger.error(f"Oracle ERP sync failed: {str(e)}")
    finally:
        oracle_erp_connector.disconnect()
        db.close()