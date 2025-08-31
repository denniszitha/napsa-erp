#!/usr/bin/env python3
"""
Simple FastAPI server with all endpoints for testing
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
import random

app = FastAPI(title="NAPSA ERM API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Mock database
mock_data = {
    "risks": [
        {"id": 1, "title": "Data Breach Risk", "category": "Cybersecurity", "likelihood": 3, "impact": 5, "status": "open"},
        {"id": 2, "title": "Compliance Violation", "category": "Regulatory", "likelihood": 2, "impact": 4, "status": "mitigated"}
    ],
    "kris": [
        {"id": 1, "name": "System Availability", "current_value": 99.5, "threshold_red": 90, "status": "green"}
    ],
    "controls": [
        {"id": 1, "name": "Multi-Factor Authentication", "type": "preventive", "effectiveness": "high"}
    ],
    "incidents": [
        {"id": 1, "title": "Suspicious Login", "severity": "medium", "status": "resolved"}
    ],
    "aml_customers": [
        {"id": 1, "name": "ABC Corp", "risk_rating": "low", "pep_status": False}
    ],
    "aml_transactions": [
        {"id": 1, "amount": 50000, "risk_score": 25, "flagged": False}
    ]
}

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Helper functions
def create_token(username: str) -> str:
    expires = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"sub": username, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = None):
    if not token:
        return None
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        return None

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Authentication endpoints
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # Mock authentication - accept any username/password
    token = create_token(request.username)
    return {"access_token": token}

@app.get("/api/v1/auth/me")
async def get_current_user():
    return {"id": 1, "username": "admin", "email": "admin@napsa.co.zm", "role": "admin"}

@app.post("/api/v1/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

# Risk Management endpoints
@app.get("/api/v1/risks")
async def get_risks():
    return mock_data["risks"]

@app.post("/api/v1/risks")
async def create_risk(risk: Dict[str, Any]):
    new_risk = {"id": len(mock_data["risks"]) + 1, **risk}
    mock_data["risks"].append(new_risk)
    return new_risk

@app.get("/api/v1/risks/{risk_id}")
async def get_risk(risk_id: int):
    for risk in mock_data["risks"]:
        if risk["id"] == risk_id:
            return risk
    raise HTTPException(status_code=404, detail="Risk not found")

@app.get("/api/v1/kris")
async def get_kris():
    return mock_data["kris"]

@app.post("/api/v1/kris")
async def create_kri(kri: Dict[str, Any]):
    new_kri = {"id": len(mock_data["kris"]) + 1, **kri}
    mock_data["kris"].append(new_kri)
    return new_kri

@app.get("/api/v1/controls")
async def get_controls():
    return mock_data["controls"]

@app.post("/api/v1/controls")
async def create_control(control: Dict[str, Any]):
    new_control = {"id": len(mock_data["controls"]) + 1, **control}
    mock_data["controls"].append(new_control)
    return new_control

@app.get("/api/v1/incidents")
async def get_incidents():
    return mock_data["incidents"]

@app.post("/api/v1/incidents")
async def create_incident(incident: Dict[str, Any]):
    new_incident = {"id": len(mock_data["incidents"]) + 1, **incident}
    mock_data["incidents"].append(new_incident)
    return new_incident

# AML endpoints
@app.get("/api/v1/aml/customers")
async def get_aml_customers():
    return mock_data["aml_customers"]

@app.get("/api/v1/aml/transactions")
async def get_aml_transactions():
    return mock_data["aml_transactions"]

@app.get("/api/v1/aml/cases")
async def get_aml_cases():
    return [{"id": 1, "status": "open", "priority": "high"}]

@app.post("/api/v1/aml/customers/{customer_id}/screen")
async def screen_customer(customer_id: int):
    return {"customer_id": customer_id, "screening_result": "clear", "timestamp": datetime.now().isoformat()}

# Analytics endpoints
@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    return {
        "total_risks": len(mock_data["risks"]),
        "open_incidents": 1,
        "kri_breaches": 0,
        "compliance_score": 92
    }

@app.get("/api/v1/analytics/risk-heatmap")
async def get_risk_heatmap():
    return {
        "data": [
            {"category": "Operational", "likelihood": 3, "impact": 4, "count": 5},
            {"category": "Financial", "likelihood": 2, "impact": 5, "count": 3}
        ]
    }

@app.get("/api/v1/analytics/compliance-trends")
async def get_compliance_trends():
    return {
        "trends": [
            {"date": "2024-01", "score": 88},
            {"date": "2024-02", "score": 90},
            {"date": "2024-03", "score": 92}
        ]
    }

# Government Integration endpoints
@app.get("/api/v1/integrations/{service}/status")
async def get_integration_status(service: str):
    services = ["zra", "napsa", "pacra", "zppa", "ccpc", "goaml"]
    if service in services:
        return {
            "service": service,
            "status": "connected",
            "last_sync": datetime.now().isoformat(),
            "pending_items": random.randint(0, 10)
        }
    raise HTTPException(status_code=404, detail="Service not found")

# Compliance endpoints
@app.get("/api/v1/compliance/requirements")
async def get_compliance_requirements():
    return [
        {"id": 1, "name": "PIA Monthly Report", "status": "compliant", "deadline": "2024-02-28"},
        {"id": 2, "name": "AML Quarterly Review", "status": "pending", "deadline": "2024-03-31"}
    ]

@app.get("/api/v1/compliance/status")
async def get_compliance_status():
    return {"overall_score": 92, "compliant": 45, "non_compliant": 5, "pending": 3}

# Assessment endpoints
@app.get("/api/v1/assessments")
async def get_assessments():
    return [
        {"id": 1, "name": "Q1 Risk Assessment", "type": "risk", "status": "completed", "score": 85}
    ]

@app.post("/api/v1/assessments")
async def create_assessment(assessment: Dict[str, Any]):
    return {"id": 2, **assessment}

# System endpoints
@app.get("/api/v1/system/health")
async def get_system_health():
    return {
        "status": "healthy",
        "uptime": 3600,
        "cpu_usage": 25,
        "memory_usage": 45,
        "disk_usage": 60
    }

@app.get("/api/v1/system/metrics")
async def get_system_metrics():
    return {
        "requests_per_minute": 150,
        "average_response_time": 45,
        "error_count": 2,
        "active_sessions": 25
    }

# Blockchain endpoints
@app.get("/api/v1/blockchain-audit/status")
async def get_blockchain_status():
    return {"chain_height": 1000, "last_block_time": datetime.now().isoformat(), "status": "synced"}

# Streaming endpoints
@app.get("/api/v1/streaming/metrics")
async def get_stream_metrics():
    return {"messages_per_second": 100, "active_streams": 5, "queue_depth": 250}

# ML endpoints
@app.post("/api/v1/ml-predictions/fraud")
async def predict_fraud(data: Dict[str, Any]):
    return {"prediction": 0.15, "risk_level": "low", "confidence": 0.92}

@app.get("/api/v1/federated-learning/experiments")
async def get_ml_experiments():
    return [
        {"id": 1, "name": "Fraud Detection v2", "status": "completed", "accuracy": 0.94}
    ]

# Report endpoints
@app.get("/api/v1/reports/risk")
async def generate_risk_report(format: str = "pdf"):
    return {"report_id": "RPT001", "format": format, "status": "generated", "url": f"/reports/risk.{format}"}

# Simulation endpoints
@app.post("/api/v1/simulation/risk")
async def run_risk_simulation(scenario: Dict[str, Any]):
    return {
        "simulation_id": "SIM001",
        "status": "completed",
        "mean_loss": 250000,
        "var_95": 500000
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)