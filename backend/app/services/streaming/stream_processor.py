"""
Real-time Streaming and Complex Event Processing Service
Provides real-time data processing, event streaming, and complex event processing capabilities
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import time
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of streaming events"""
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_UPDATED = "transaction_updated"
    ALERT_TRIGGERED = "alert_triggered"
    RISK_THRESHOLD_EXCEEDED = "risk_threshold_exceeded"
    CUSTOMER_PROFILE_CHANGED = "customer_profile_changed"
    SUSPICIOUS_PATTERN_DETECTED = "suspicious_pattern_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_HEALTH_UPDATE = "system_health_update"
    ML_MODEL_PREDICTION = "ml_model_prediction"
    BLOCKCHAIN_EVENT = "blockchain_event"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class StreamEvent:
    """Streaming event data structure"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    source: str
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class ProcessingRule:
    """Complex event processing rule"""
    rule_id: str
    name: str
    description: str
    event_types: List[EventType]
    conditions: Dict[str, Any]
    time_window: timedelta
    action: str
    enabled: bool = True

@dataclass
class Alert:
    """Real-time alert"""
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    event_data: Dict[str, Any]
    triggered_by: List[str]  # Event IDs that triggered this alert
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False

class EventProcessor(ABC):
    """Abstract base class for event processors"""
    
    @abstractmethod
    async def process(self, event: StreamEvent) -> Optional[Alert]:
        pass

class TransactionVelocityProcessor(EventProcessor):
    """Process transaction velocity events"""
    
    def __init__(self, velocity_threshold: int = 10, time_window: int = 300):
        self.velocity_threshold = velocity_threshold
        self.time_window = time_window  # seconds
        self.customer_transactions = defaultdict(deque)
    
    async def process(self, event: StreamEvent) -> Optional[Alert]:
        if event.event_type != EventType.TRANSACTION_CREATED:
            return None
        
        customer_id = event.entity_id
        current_time = event.timestamp
        
        # Clean old transactions outside time window
        cutoff_time = current_time - timedelta(seconds=self.time_window)
        while (self.customer_transactions[customer_id] and 
               self.customer_transactions[customer_id][0] < cutoff_time):
            self.customer_transactions[customer_id].popleft()
        
        # Add current transaction
        self.customer_transactions[customer_id].append(current_time)
        
        # Check if velocity threshold exceeded
        transaction_count = len(self.customer_transactions[customer_id])
        if transaction_count > self.velocity_threshold:
            return Alert(
                alert_id=f"velocity_{customer_id}_{current_time.timestamp()}",
                title="High Transaction Velocity Detected",
                description=f"Customer {customer_id} has {transaction_count} transactions in {self.time_window} seconds",
                severity=AlertSeverity.HIGH,
                event_data={
                    "customer_id": customer_id,
                    "transaction_count": transaction_count,
                    "time_window": self.time_window,
                    "threshold": self.velocity_threshold
                },
                triggered_by=[event.event_id],
                timestamp=current_time
            )
        
        return None

class LargeAmountProcessor(EventProcessor):
    """Process large amount transactions"""
    
    def __init__(self, amount_threshold: float = 50000.0):
        self.amount_threshold = amount_threshold
    
    async def process(self, event: StreamEvent) -> Optional[Alert]:
        if event.event_type != EventType.TRANSACTION_CREATED:
            return None
        
        amount = event.data.get('amount', 0)
        if amount > self.amount_threshold:
            return Alert(
                alert_id=f"large_amount_{event.entity_id}_{event.timestamp.timestamp()}",
                title="Large Amount Transaction",
                description=f"Transaction amount ${amount:,.2f} exceeds threshold ${self.amount_threshold:,.2f}",
                severity=AlertSeverity.MEDIUM,
                event_data={
                    "transaction_id": event.entity_id,
                    "amount": amount,
                    "threshold": self.amount_threshold,
                    "customer_id": event.data.get('customer_id')
                },
                triggered_by=[event.event_id],
                timestamp=event.timestamp
            )
        
        return None

class StructuringDetectionProcessor(EventProcessor):
    """Detect structuring patterns in real-time"""
    
    def __init__(self, threshold: float = 10000.0, pattern_window: int = 86400):  # 24 hours
        self.threshold = threshold
        self.pattern_window = pattern_window
        self.customer_amounts = defaultdict(list)
    
    async def process(self, event: StreamEvent) -> Optional[Alert]:
        if event.event_type != EventType.TRANSACTION_CREATED:
            return None
        
        amount = event.data.get('amount', 0)
        customer_id = event.data.get('customer_id')
        
        if not customer_id or amount >= self.threshold:
            return None
        
        current_time = event.timestamp
        
        # Clean old transactions
        cutoff_time = current_time - timedelta(seconds=self.pattern_window)
        self.customer_amounts[customer_id] = [
            (amt, ts) for amt, ts in self.customer_amounts[customer_id]
            if ts > cutoff_time
        ]
        
        # Add current transaction
        self.customer_amounts[customer_id].append((amount, current_time))
        
        # Check for structuring pattern
        transactions = self.customer_amounts[customer_id]
        if len(transactions) >= 3:  # Need at least 3 transactions
            total_amount = sum(amt for amt, _ in transactions)
            near_threshold_count = sum(1 for amt, _ in transactions if amt > self.threshold * 0.8)
            
            if (total_amount > self.threshold * 1.5 and 
                near_threshold_count >= len(transactions) * 0.6):  # 60% near threshold
                
                return Alert(
                    alert_id=f"structuring_{customer_id}_{current_time.timestamp()}",
                    title="Potential Structuring Pattern",
                    description=f"Customer {customer_id} has {len(transactions)} transactions totaling ${total_amount:,.2f} in pattern suggesting structuring",
                    severity=AlertSeverity.HIGH,
                    event_data={
                        "customer_id": customer_id,
                        "transaction_count": len(transactions),
                        "total_amount": total_amount,
                        "threshold": self.threshold,
                        "pattern_window_hours": self.pattern_window / 3600
                    },
                    triggered_by=[event.event_id],
                    timestamp=current_time
                )
        
        return None

class RiskScoreProcessor(EventProcessor):
    """Process ML risk score predictions"""
    
    def __init__(self, high_risk_threshold: float = 0.8):
        self.high_risk_threshold = high_risk_threshold
    
    async def process(self, event: StreamEvent) -> Optional[Alert]:
        if event.event_type != EventType.ML_MODEL_PREDICTION:
            return None
        
        risk_score = event.data.get('risk_score', 0)
        if risk_score > self.high_risk_threshold:
            return Alert(
                alert_id=f"high_risk_{event.entity_id}_{event.timestamp.timestamp()}",
                title="High Risk Score Detected",
                description=f"ML model predicted high risk score ({risk_score:.2%}) for {event.entity_type} {event.entity_id}",
                severity=AlertSeverity.HIGH if risk_score > 0.9 else AlertSeverity.MEDIUM,
                event_data={
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "risk_score": risk_score,
                    "threshold": self.high_risk_threshold,
                    "model_confidence": event.data.get('confidence', 0)
                },
                triggered_by=[event.event_id],
                timestamp=event.timestamp
            )
        
        return None

class StreamingService:
    """Main streaming service for real-time event processing"""
    
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.processors: List[EventProcessor] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.event_history = deque(maxlen=10000)  # Keep last 10k events
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.is_running = False
        self.processing_stats = {
            'events_processed': 0,
            'alerts_generated': 0,
            'processing_time_avg': 0.0,
            'last_event_time': None
        }
        
        # Initialize default processors
        self._initialize_processors()
    
    def _initialize_processors(self):
        """Initialize default event processors"""
        self.processors = [
            TransactionVelocityProcessor(velocity_threshold=15, time_window=300),
            LargeAmountProcessor(amount_threshold=50000.0),
            StructuringDetectionProcessor(threshold=10000.0, pattern_window=86400),
            RiskScoreProcessor(high_risk_threshold=0.7)
        ]
    
    async def start(self):
        """Start the streaming service"""
        self.is_running = True
        logger.info("Starting streaming service...")
        
        # Start processing loop
        processing_task = asyncio.create_task(self._processing_loop())
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        await asyncio.gather(processing_task, cleanup_task)
    
    async def stop(self):
        """Stop the streaming service"""
        self.is_running = False
        logger.info("Stopping streaming service...")
    
    async def publish_event(self, event: StreamEvent):
        """Publish an event to the stream"""
        try:
            await self.event_queue.put(event)
            logger.debug(f"Published event: {event.event_type.value} for {event.entity_type}:{event.entity_id}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
    
    def subscribe(self, event_type: str, callback: Callable[[StreamEvent], None]):
        """Subscribe to specific event types"""
        self.subscribers[event_type].append(callback)
        logger.info(f"Added subscriber for event type: {event_type}")
    
    def add_processor(self, processor: EventProcessor):
        """Add a custom event processor"""
        self.processors.append(processor)
        logger.info(f"Added custom processor: {type(processor).__name__}")
    
    async def _processing_loop(self):
        """Main event processing loop"""
        logger.info("Event processing loop started")
        
        while self.is_running:
            try:
                # Get event from queue with timeout
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                start_time = time.time()
                
                # Store event in history
                self.event_history.append(event)
                
                # Process event through all processors
                alerts = []
                for processor in self.processors:
                    try:
                        alert = await processor.process(event)
                        if alert:
                            alerts.append(alert)
                    except Exception as e:
                        logger.error(f"Processor error: {e}")
                
                # Handle generated alerts
                for alert in alerts:
                    self.active_alerts[alert.alert_id] = alert
                    await self._notify_subscribers("alert_generated", {
                        "alert": asdict(alert),
                        "triggering_event": asdict(event)
                    })
                
                # Notify event subscribers
                await self._notify_subscribers(event.event_type.value, event)
                
                # Update statistics
                processing_time = time.time() - start_time
                self.processing_stats['events_processed'] += 1
                self.processing_stats['alerts_generated'] += len(alerts)
                self.processing_stats['processing_time_avg'] = (
                    (self.processing_stats['processing_time_avg'] * (self.processing_stats['events_processed'] - 1) + processing_time) /
                    self.processing_stats['events_processed']
                )
                self.processing_stats['last_event_time'] = event.timestamp.isoformat()
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
    
    async def _cleanup_loop(self):
        """Cleanup old alerts and events"""
        while self.is_running:
            try:
                # Remove old resolved alerts (older than 1 hour)
                cutoff_time = datetime.now() - timedelta(hours=1)
                old_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.resolved and alert.timestamp < cutoff_time
                ]
                
                for alert_id in old_alerts:
                    del self.active_alerts[alert_id]
                
                if old_alerts:
                    logger.info(f"Cleaned up {len(old_alerts)} old alerts")
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _notify_subscribers(self, event_type: str, data: Any):
        """Notify subscribers of events"""
        try:
            for callback in self.subscribers.get(event_type, []):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Subscriber callback error: {e}")
        except Exception as e:
            logger.error(f"Error notifying subscribers: {e}")
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active (unresolved) alerts"""
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged by user {user_id}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str, user_id: str, resolution_note: str = None) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            logger.info(f"Alert {alert_id} resolved by user {user_id}")
            return True
        return False
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.processing_stats,
            'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved]),
            'total_alerts': len(self.active_alerts),
            'event_queue_size': self.event_queue.qsize(),
            'processors_count': len(self.processors),
            'subscribers_count': sum(len(subs) for subs in self.subscribers.values())
        }
    
    def get_event_history(self, limit: int = 100) -> List[StreamEvent]:
        """Get recent event history"""
        history_list = list(self.event_history)
        return history_list[-limit:] if limit else history_list

# Global streaming service instance
streaming_service = None

def get_streaming_service() -> StreamingService:
    """Get the global streaming service instance"""
    global streaming_service
    if streaming_service is None:
        streaming_service = StreamingService()
    return streaming_service

async def publish_transaction_event(transaction_data: Dict[str, Any], event_type: str = "created"):
    """Convenience function to publish transaction events"""
    service = get_streaming_service()
    
    event = StreamEvent(
        event_id=f"tx_{transaction_data.get('id')}_{int(time.time())}",
        event_type=EventType.TRANSACTION_CREATED if event_type == "created" else EventType.TRANSACTION_UPDATED,
        timestamp=datetime.now(),
        source="transaction_api",
        entity_type="transaction",
        entity_id=str(transaction_data.get('id', '')),
        data=transaction_data,
        user_id=transaction_data.get('user_id')
    )
    
    await service.publish_event(event)

async def publish_ml_prediction_event(entity_type: str, entity_id: str, prediction_data: Dict[str, Any]):
    """Convenience function to publish ML prediction events"""
    service = get_streaming_service()
    
    event = StreamEvent(
        event_id=f"ml_{entity_type}_{entity_id}_{int(time.time())}",
        event_type=EventType.ML_MODEL_PREDICTION,
        timestamp=datetime.now(),
        source="ml_engine",
        entity_type=entity_type,
        entity_id=entity_id,
        data=prediction_data
    )
    
    await service.publish_event(event)

async def publish_alert_event(alert_data: Dict[str, Any]):
    """Convenience function to publish alert events"""
    service = get_streaming_service()
    
    event = StreamEvent(
        event_id=f"alert_{alert_data.get('id')}_{int(time.time())}",
        event_type=EventType.ALERT_TRIGGERED,
        timestamp=datetime.now(),
        source="alert_system",
        entity_type="alert",
        entity_id=str(alert_data.get('id', '')),
        data=alert_data
    )
    
    await service.publish_event(event)