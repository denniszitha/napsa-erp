"""
KRI (Key Risk Indicator) Monitoring Service
Implements real-time KRI threshold monitoring and alerts for NAPSA
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from app.core.database import SessionLocal
from app.models.kri import KeyRiskIndicator, KRIValue, KRIThresholdBreach
from app.models.risk import Risk
from app.models.user import User
from app.services.email import email_service

logger = logging.getLogger(__name__)

class KRIMonitoringService:
    """Service for monitoring KRI thresholds and generating alerts"""
    
    def __init__(self):
        self.check_interval = 300  # Check every 5 minutes
        self.is_running = False
        
    async def start_monitoring(self):
        """Start the KRI monitoring loop"""
        self.is_running = True
        logger.info("KRI Monitoring Service started")
        
        while self.is_running:
            try:
                await self.check_all_kris()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in KRI monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop_monitoring(self):
        """Stop the KRI monitoring loop"""
        self.is_running = False
        logger.info("KRI Monitoring Service stopped")
    
    async def check_all_kris(self):
        """Check all active KRIs against their thresholds"""
        db = SessionLocal()
        try:
            # Get all active KRIs
            kris = db.query(KeyRiskIndicator).filter(
                KeyRiskIndicator.is_active == True
            ).all()
            
            for kri in kris:
                await self.check_kri_threshold(kri, db)
                
        except Exception as e:
            logger.error(f"Error checking KRIs: {str(e)}")
        finally:
            db.close()
    
    async def check_kri_threshold(self, kri: KeyRiskIndicator, db: Session):
        """Check a single KRI against its thresholds"""
        try:
            current_value = kri.current_value
            if current_value is None:
                return
            
            # Determine threshold status
            status = self.get_threshold_status(kri, current_value)
            
            # Check if this is a new breach or status change
            last_breach = db.query(KRIThresholdBreach).filter(
                KRIThresholdBreach.kri_id == kri.id,
                KRIThresholdBreach.resolved_at.is_(None)
            ).first()
            
            if status in ['amber', 'red', 'critical']:
                if not last_breach or last_breach.breach_level != status:
                    # Create new breach record
                    await self.create_breach_record(kri, status, current_value, db)
                    # Send alerts
                    await self.send_kri_alert(kri, status, current_value, db)
            elif last_breach:
                # Threshold returned to normal, resolve the breach
                last_breach.resolved_at = datetime.utcnow()
                last_breach.resolution_value = current_value
                db.commit()
                
        except Exception as e:
            logger.error(f"Error checking KRI {kri.name}: {str(e)}")
    
    def get_threshold_status(self, kri: KeyRiskIndicator, value: float) -> str:
        """Determine the threshold status based on current value"""
        # For ascending thresholds (higher is worse)
        if kri.threshold_direction == 'ascending':
            if value >= kri.threshold_red:
                return 'red' if value < kri.threshold_red * 1.5 else 'critical'
            elif value >= kri.threshold_amber:
                return 'amber'
            elif value <= kri.threshold_green:
                return 'green'
        # For descending thresholds (lower is worse)
        else:
            if value <= kri.threshold_red:
                return 'red' if value > kri.threshold_red * 0.5 else 'critical'
            elif value <= kri.threshold_amber:
                return 'amber'
            elif value >= kri.threshold_green:
                return 'green'
        
        return 'normal'
    
    async def create_breach_record(self, kri: KeyRiskIndicator, status: str, value: float, db: Session):
        """Create a breach record in the database"""
        breach = KRIThresholdBreach(
            kri_id=kri.id,
            breach_level=status,
            breach_value=value,
            threshold_value=self.get_threshold_value(kri, status),
            breached_at=datetime.utcnow(),
            notification_sent=False
        )
        db.add(breach)
        db.commit()
        return breach
    
    def get_threshold_value(self, kri: KeyRiskIndicator, status: str) -> float:
        """Get the threshold value for a given status"""
        if status == 'amber':
            return kri.threshold_amber
        elif status in ['red', 'critical']:
            return kri.threshold_red
        else:
            return kri.threshold_green
    
    async def send_kri_alert(self, kri: KeyRiskIndicator, status: str, value: float, db: Session):
        """Send alert notifications for KRI breaches"""
        try:
            # Get risk associated with this KRI
            risk = None
            if kri.risk_id:
                risk = db.query(Risk).filter(Risk.id == kri.risk_id).first()
            
            # Get recipients
            recipients = await self.get_alert_recipients(kri, risk, db)
            
            if not recipients:
                logger.warning(f"No recipients found for KRI alert: {kri.name}")
                return
            
            # Send email notification
            await email_service.send_kri_breach_notification(
                kri_name=kri.name,
                current_value=value,
                threshold=self.get_threshold_value(kri, status),
                status=status,
                risk_title=risk.title if risk else "N/A",
                recipients=recipients
            )
            
            # Log notification
            logger.info(f"KRI alert sent for {kri.name} - Status: {status}, Value: {value}")
            
            # Update breach record
            breach = db.query(KRIThresholdBreach).filter(
                KRIThresholdBreach.kri_id == kri.id,
                KRIThresholdBreach.resolved_at.is_(None)
            ).first()
            
            if breach:
                breach.notification_sent = True
                breach.notification_sent_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            logger.error(f"Error sending KRI alert: {str(e)}")
    
    async def get_alert_recipients(self, kri: KeyRiskIndicator, risk: Optional[Risk], db: Session) -> List[str]:
        """Get email recipients for KRI alerts"""
        recipients = []
        
        # Add KRI owner
        if kri.owner_id:
            owner = db.query(User).filter(User.id == kri.owner_id).first()
            if owner and owner.email:
                recipients.append(owner.email)
        
        # Add risk owner
        if risk and risk.risk_owner_id:
            risk_owner = db.query(User).filter(User.id == risk.risk_owner_id).first()
            if risk_owner and risk_owner.email and risk_owner.email not in recipients:
                recipients.append(risk_owner.email)
        
        # Add risk management team
        risk_managers = db.query(User).filter(
            User.role.in_(['admin', 'risk_manager'])
        ).all()
        
        for manager in risk_managers:
            if manager.email and manager.email not in recipients:
                recipients.append(manager.email)
        
        return recipients
    
    async def update_kri_value(self, kri_id: str, new_value: float, db: Session) -> Dict[str, Any]:
        """Update KRI value and check thresholds"""
        kri = db.query(KeyRiskIndicator).filter(KeyRiskIndicator.id == kri_id).first()
        
        if not kri:
            raise ValueError(f"KRI not found: {kri_id}")
        
        # Store old value
        old_value = kri.current_value
        
        # Update current value
        kri.current_value = new_value
        kri.last_updated = datetime.utcnow()
        
        # Add to value history
        kri_value = KRIValue(
            kri_id=kri.id,
            value=new_value,
            recorded_at=datetime.utcnow()
        )
        db.add(kri_value)
        
        # Check thresholds
        status = self.get_threshold_status(kri, new_value)
        
        # Commit changes
        db.commit()
        
        # Check for alerts
        await self.check_kri_threshold(kri, db)
        
        return {
            "kri_id": str(kri.id),
            "name": kri.name,
            "old_value": old_value,
            "new_value": new_value,
            "status": status,
            "threshold_green": kri.threshold_green,
            "threshold_amber": kri.threshold_amber,
            "threshold_red": kri.threshold_red
        }
    
    async def get_kri_dashboard_data(self, db: Session) -> Dict[str, Any]:
        """Get KRI dashboard data"""
        kris = db.query(KeyRiskIndicator).filter(
            KeyRiskIndicator.is_active == True
        ).all()
        
        total_kris = len(kris)
        breached_kris = 0
        critical_kris = 0
        
        kri_details = []
        
        for kri in kris:
            status = self.get_threshold_status(kri, kri.current_value) if kri.current_value else 'unknown'
            
            if status in ['amber', 'red', 'critical']:
                breached_kris += 1
            if status == 'critical':
                critical_kris += 1
            
            # Get associated risk
            risk = None
            if kri.risk_id:
                risk = db.query(Risk).filter(Risk.id == kri.risk_id).first()
            
            kri_details.append({
                "id": str(kri.id),
                "name": kri.name,
                "category": kri.category,
                "current_value": kri.current_value,
                "threshold_green": kri.threshold_green,
                "threshold_amber": kri.threshold_amber,
                "threshold_red": kri.threshold_red,
                "status": status,
                "trend": kri.trend if hasattr(kri, 'trend') else None,
                "last_updated": kri.last_updated.isoformat() if kri.last_updated else None,
                "risk_title": risk.title if risk else None,
                "frequency": kri.frequency
            })
        
        return {
            "summary": {
                "total_kris": total_kris,
                "breached_kris": breached_kris,
                "critical_kris": critical_kris,
                "compliance_rate": round((total_kris - breached_kris) / total_kris * 100, 2) if total_kris > 0 else 100
            },
            "kris": kri_details,
            "last_check": datetime.utcnow().isoformat()
        }

# Create singleton instance
kri_monitoring_service = KRIMonitoringService()