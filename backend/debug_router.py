#!/usr/bin/env python3
"""
Debug script to test router registration
"""
from fastapi import FastAPI
from app.api.v1.assessment_templates import router as assessment_router

# Create minimal FastAPI app
app = FastAPI()

# Register just the assessment templates router
app.include_router(assessment_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    print("Starting debug server with only assessment templates router...")
    print("Available routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path} -> {route.methods if hasattr(route, 'methods') else 'unknown'}")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)