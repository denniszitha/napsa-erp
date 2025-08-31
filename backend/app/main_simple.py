"""
Simplified FastAPI application for testing
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="NAPSA ERM API",
    description="Risk Management System - Simplified",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection test
def test_db_connection():
    """Test database connection"""
    try:
        import psycopg2
        db_url = os.getenv("DATABASE_URL", "postgresql://napsa_admin@postgres:5432/napsa_erm")
        
        # Parse connection string - handle both with and without password
        if "postgresql://" in db_url:
            # Remove postgresql:// prefix
            conn_str = db_url.replace("postgresql://", "")
            
            # Check if @ exists (has host info)
            if "@" in conn_str:
                # Split user/pass from host/db
                user_part, host_part = conn_str.split("@", 1)
                
                # Parse user and optional password
                if ":" in user_part:
                    user, password = user_part.split(":", 1)
                else:
                    user = user_part
                    password = None
                
                # Parse host, port, and database
                if "/" in host_part:
                    host_port, database = host_part.split("/", 1)
                    if ":" in host_port:
                        host, port = host_port.split(":", 1)
                    else:
                        host = host_port
                        port = "5432"
                else:
                    host = host_part
                    port = "5432"
                    database = "napsa_erm"
                
                # Connect with or without password
                conn_params = {
                    "host": host,
                    "port": int(port),
                    "database": database,
                    "user": user
                }
                if password:
                    conn_params["password"] = password
                
                conn = psycopg2.connect(**conn_params)
                conn.close()
                return True, f"Connected to {database} on {host}:{port}"
            else:
                return False, "Invalid connection string format"
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False, str(e)
    return False, "Unable to parse DATABASE_URL"

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    db_status, db_message = test_db_connection()
    return {
        "message": "NAPSA ERM API",
        "status": "running",
        "version": "1.0.0",
        "database": "connected" if db_status else "disconnected",
        "db_message": db_message,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api/v1"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status, db_message = test_db_connection()
    return {
        "status": "healthy",
        "database": "connected" if db_status else "disconnected",
        "details": db_message
    }

# API v1 endpoints
@app.get("/api/v1")
async def api_root():
    """API v1 root"""
    return {
        "version": "1.0",
        "endpoints": [
            "/api/v1/risks",
            "/api/v1/users",
            "/api/v1/assessments",
            "/api/v1/controls"
        ]
    }

# Mock endpoints for testing
@app.get("/api/v1/risks")
async def get_risks(skip: int = 0, limit: int = 100):
    """Get risks - mock endpoint"""
    return {
        "data": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }

@app.post("/api/v1/risks")
async def create_risk(risk: dict):
    """Create risk - mock endpoint"""
    return {
        "id": "mock-id",
        "message": "Risk created (mock)",
        **risk
    }

@app.get("/api/v1/users")
async def get_users(skip: int = 0, limit: int = 100):
    """Get users - mock endpoint"""
    return {
        "data": [
            {
                "id": "1",
                "email": "admin@napsa.co.zm",
                "username": "admin",
                "full_name": "System Administrator",
                "is_active": True
            }
        ],
        "total": 1,
        "skip": skip,
        "limit": limit
    }

@app.get("/api/v1/assessments")
async def get_assessments():
    """Get assessments - mock endpoint"""
    return {"data": [], "total": 0}

@app.get("/api/v1/controls")
async def get_controls():
    """Get controls - mock endpoint"""
    return {"data": [], "total": 0}

# Auth endpoints (mock)
@app.post("/api/v1/auth/login")
async def login(username: str = "admin", password: str = "admin"):
    """Mock login endpoint"""
    return {
        "access_token": "mock-token",
        "token_type": "bearer",
        "user": {
            "username": username,
            "email": f"{username}@napsa.co.zm",
            "full_name": "Test User"
        }
    }

@app.get("/api/v1/auth/me")
async def get_current_user():
    """Mock current user endpoint"""
    return {
        "username": "admin",
        "email": "admin@napsa.co.zm",
        "full_name": "System Administrator",
        "is_active": True
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting NAPSA ERM API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)