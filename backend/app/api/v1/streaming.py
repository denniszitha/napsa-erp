"""
Real-time Streaming API
Provides endpoints for real-time event streaming, alerts management, and complex event processing
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import asyncio
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.streaming import (
    get_streaming_service,
    StreamEvent,
    EventType,
    AlertSeverity,
    Alert,
    publish_transaction_event,
    publish_ml_prediction_event
)

router = APIRouter()

# Pydantic models for API
class EventPublishRequest(BaseModel):
    event_type: str
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    correlation_id: Optional[str] = None

class AlertAcknowledgeRequest(BaseModel):
    alert_id: str

class AlertResolveRequest(BaseModel):
    alert_id: str
    resolution_note: Optional[str] = None

class StreamStatsResponse(BaseModel):
    events_processed: int
    alerts_generated: int
    active_alerts: int
    processing_time_avg: float
    event_queue_size: int
    processors_count: int
    last_event_time: Optional[str]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except:
                # Connection closed, will be cleaned up
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts and events
    """
    await manager.connect(websocket)
    try:
        streaming_service = get_streaming_service()
        
        # Subscribe to alert events
        async def alert_callback(data):
            await websocket.send_text(json.dumps({
                "type": "alert",
                "data": data
            }, default=str))
        
        streaming_service.subscribe("alert_generated", alert_callback)
        
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
            client_message = json.loads(data)
            
            if client_message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/events/publish")
async def publish_event(
    request: EventPublishRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually publish an event to the streaming system
    """
    try:
        streaming_service = get_streaming_service()
        
        # Validate event type
        valid_event_types = [e.value for e in EventType]
        if request.event_type not in valid_event_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type. Must be one of: {valid_event_types}"
            )
        
        # Create and publish event
        event = StreamEvent(
            event_id=f"manual_{request.entity_type}_{request.entity_id}_{int(datetime.now().timestamp())}",
            event_type=EventType(request.event_type),
            timestamp=datetime.now(),
            source="manual_api",
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            data=request.data,
            correlation_id=request.correlation_id,
            user_id=str(current_user.id)
        )
        
        await streaming_service.publish_event(event)
        
        return {
            "status": "success",
            "event_id": event.event_id,
            "message": "Event published successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")

@router.get("/alerts/active")
async def get_active_alerts(
    severity: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get active (unresolved) alerts
    """
    try:
        streaming_service = get_streaming_service()
        
        # Validate severity if provided
        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid severity. Must be one of: {[s.value for s in AlertSeverity]}"
                )
        
        alerts = streaming_service.get_active_alerts(severity_filter)[:limit]
        
        # Convert to dict format
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "alert_id": alert.alert_id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity.value,
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged": alert.acknowledged,
                "resolved": alert.resolved,
                "event_data": alert.event_data,
                "triggered_by": alert.triggered_by
            })
        
        return {
            "total_alerts": len(alert_data),
            "filters": {"severity": severity, "limit": limit},
            "alerts": alert_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.post("/alerts/acknowledge")
async def acknowledge_alert(
    request: AlertAcknowledgeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Acknowledge an alert
    """
    try:
        streaming_service = get_streaming_service()
        
        success = streaming_service.acknowledge_alert(request.alert_id, str(current_user.id))
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Broadcast acknowledgment
        await manager.broadcast({
            "type": "alert_acknowledged",
            "alert_id": request.alert_id,
            "acknowledged_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "message": f"Alert {request.alert_id} acknowledged"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.post("/alerts/resolve")
async def resolve_alert(
    request: AlertResolveRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Resolve an alert
    """
    try:
        streaming_service = get_streaming_service()
        
        success = streaming_service.resolve_alert(
            request.alert_id, 
            str(current_user.id), 
            request.resolution_note
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Broadcast resolution
        await manager.broadcast({
            "type": "alert_resolved",
            "alert_id": request.alert_id,
            "resolved_by": current_user.email,
            "resolution_note": request.resolution_note,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "message": f"Alert {request.alert_id} resolved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

@router.get("/statistics", response_model=StreamStatsResponse)
async def get_streaming_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get streaming service statistics
    """
    try:
        streaming_service = get_streaming_service()
        stats = streaming_service.get_processing_statistics()
        
        return StreamStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/events/history")
async def get_event_history(
    limit: int = 100,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get recent event history
    """
    try:
        streaming_service = get_streaming_service()
        events = streaming_service.get_event_history(limit)
        
        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]
        
        # Filter by entity type if specified  
        if entity_type:
            events = [e for e in events if e.entity_type == entity_type]
        
        # Convert to dict format
        event_data = []
        for event in events:
            event_data.append({
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "user_id": event.user_id,
                "correlation_id": event.correlation_id,
                "data": event.data
            })
        
        return {
            "total_events": len(event_data),
            "filters": {
                "limit": limit,
                "event_type": event_type,
                "entity_type": entity_type
            },
            "events": event_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event history: {str(e)}")

@router.get("/alerts/feed")
async def get_alerts_feed(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get live alerts feed (Server-Sent Events)
    """
    async def event_stream():
        streaming_service = get_streaming_service()
        
        # Subscribe to new alerts
        alert_queue = asyncio.Queue()
        
        async def alert_callback(data):
            await alert_queue.put(data)
        
        streaming_service.subscribe("alert_generated", alert_callback)
        
        try:
            while True:
                try:
                    # Wait for new alert with timeout
                    alert_data = await asyncio.wait_for(alert_queue.get(), timeout=30.0)
                    
                    # Format as Server-Sent Event
                    yield f"data: {json.dumps(alert_data, default=str)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                    
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/test/transaction")
async def test_transaction_event(
    transaction_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """
    Test endpoint to simulate transaction events for testing
    """
    try:
        await publish_transaction_event(transaction_data, "created")
        
        return {
            "status": "success",
            "message": "Test transaction event published",
            "data": transaction_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish test event: {str(e)}")

@router.post("/test/ml-prediction")
async def test_ml_prediction_event(
    entity_type: str,
    entity_id: str,
    prediction_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """
    Test endpoint to simulate ML prediction events
    """
    try:
        await publish_ml_prediction_event(entity_type, entity_id, prediction_data)
        
        return {
            "status": "success",
            "message": "Test ML prediction event published",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "data": prediction_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish test event: {str(e)}")

@router.get("/health")
async def streaming_health_check():
    """
    Health check for streaming service
    """
    try:
        streaming_service = get_streaming_service()
        stats = streaming_service.get_processing_statistics()
        
        return {
            "status": "healthy" if streaming_service.is_running else "stopped",
            "uptime": "running" if streaming_service.is_running else "stopped",
            "queue_size": stats["event_queue_size"],
            "active_alerts": stats["active_alerts"],
            "events_processed": stats["events_processed"]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }