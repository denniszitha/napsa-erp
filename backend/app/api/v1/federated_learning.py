"""
Federated Learning API
Provides endpoints for privacy-preserving federated machine learning
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.federated_learning import (
    get_fl_coordinator,
    ParticipantRole,
    FLStatus
)

router = APIRouter()

# Pydantic models for API
class CreateExperimentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    name: str
    description: str
    model_type: str
    min_participants: int = 3
    max_rounds: int = 10
    privacy_budget: float = 1.0

class RegisterParticipantRequest(BaseModel):
    name: str
    role: str = "participant"
    data_samples: int = 0

class JoinExperimentRequest(BaseModel):
    participant_id: str
    experiment_id: str

class ModelUpdateRequest(BaseModel):
    participant_id: str
    experiment_id: str
    encrypted_model: str

class ExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    status: str
    current_round: int
    max_rounds: int
    participants: int
    privacy_budget: float
    created_at: str

@router.post("/experiments/create")
async def create_experiment(
    request: CreateExperimentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new federated learning experiment
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        coordinator = get_fl_coordinator()
        
        # Validate model type
        valid_model_types = ["fraud_detection", "risk_scoring", "customer_segmentation", "anomaly_detection"]
        if request.model_type not in valid_model_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type. Must be one of: {valid_model_types}"
            )
        
        experiment_id = coordinator.create_experiment(
            name=request.name,
            description=request.description,
            model_type=request.model_type,
            min_participants=request.min_participants,
            max_rounds=request.max_rounds,
            privacy_budget=request.privacy_budget
        )
        
        return {
            "status": "success",
            "experiment_id": experiment_id,
            "message": "Federated learning experiment created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create experiment: {str(e)}")

@router.post("/participants/register")
async def register_participant(
    request: RegisterParticipantRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Register a new federated learning participant
    """
    try:
        coordinator = get_fl_coordinator()
        
        # Validate role
        try:
            role = ParticipantRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {[r.value for r in ParticipantRole]}"
            )
        
        participant_id = coordinator.register_participant(
            name=request.name,
            role=role,
            data_samples=request.data_samples
        )
        
        return {
            "status": "success",
            "participant_id": participant_id,
            "message": "Participant registered successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register participant: {str(e)}")

@router.post("/experiments/join")
async def join_experiment(
    request: JoinExperimentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Have a participant join an experiment
    """
    try:
        coordinator = get_fl_coordinator()
        
        success = coordinator.join_experiment(
            participant_id=request.participant_id,
            experiment_id=request.experiment_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to join experiment")
        
        return {
            "status": "success",
            "message": "Participant joined experiment successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join experiment: {str(e)}")

@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Start a federated learning experiment
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        coordinator = get_fl_coordinator()
        
        # Start experiment in background
        async def start_experiment_background():
            success = await coordinator.start_experiment(experiment_id)
            if not success:
                logger.error(f"Failed to start experiment {experiment_id}")
        
        background_tasks.add_task(start_experiment_background)
        
        return {
            "status": "success",
            "message": "Experiment start initiated",
            "experiment_id": experiment_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start experiment: {str(e)}")

@router.get("/experiments/{experiment_id}/status")
async def get_experiment_status(
    experiment_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get experiment status and progress
    """
    try:
        coordinator = get_fl_coordinator()
        status = coordinator.get_experiment_status(experiment_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get experiment status: {str(e)}")

@router.get("/experiments")
async def list_experiments(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all federated learning experiments
    """
    try:
        coordinator = get_fl_coordinator()
        
        experiments = []
        for experiment_id in coordinator.experiments:
            exp_status = coordinator.get_experiment_status(experiment_id)
            if exp_status and (not status or exp_status["status"] == status):
                experiments.append(exp_status)
        
        return {
            "experiments": experiments,
            "total": len(experiments),
            "filter": {"status": status} if status else {}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")

@router.get("/participants/{participant_id}")
async def get_participant_info(
    participant_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get participant information
    """
    try:
        coordinator = get_fl_coordinator()
        info = coordinator.get_participant_info(participant_id)
        
        if not info:
            raise HTTPException(status_code=404, detail="Participant not found")
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get participant info: {str(e)}")

@router.get("/participants")
async def list_participants(
    status: Optional[str] = None,
    role: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    List all federated learning participants
    """
    try:
        coordinator = get_fl_coordinator()
        
        participants = []
        for participant_id in coordinator.participants:
            info = coordinator.get_participant_info(participant_id)
            if info:
                # Apply filters
                if status and info["status"] != status:
                    continue
                if role and info["role"] != role:
                    continue
                participants.append(info)
        
        return {
            "participants": participants,
            "total": len(participants),
            "filters": {"status": status, "role": role}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list participants: {str(e)}")

@router.post("/models/submit")
async def submit_model_update(
    request: ModelUpdateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit model update from participant
    """
    try:
        coordinator = get_fl_coordinator()
        
        success = coordinator.submit_model_update(
            participant_id=request.participant_id,
            experiment_id=request.experiment_id,
            encrypted_model=request.encrypted_model
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to submit model update")
        
        return {
            "status": "success",
            "message": "Model update submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit model update: {str(e)}")

@router.get("/experiments/{experiment_id}/privacy")
async def get_privacy_metrics(
    experiment_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get privacy metrics for an experiment
    """
    try:
        coordinator = get_fl_coordinator()
        metrics = coordinator.get_privacy_metrics(experiment_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get privacy metrics: {str(e)}")

@router.get("/coordinator/stats")
async def get_coordinator_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get federated learning coordinator statistics
    """
    try:
        coordinator = get_fl_coordinator()
        stats = coordinator.get_coordinator_stats()
        
        return {
            "coordinator_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get coordinator stats: {str(e)}")

@router.post("/coordinator/start")
async def start_coordinator(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Start the federated learning coordinator
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        coordinator = get_fl_coordinator()
        
        if coordinator.is_running:
            return {
                "status": "already_running",
                "message": "Federated learning coordinator is already running"
            }
        
        # Start coordinator in background
        background_tasks.add_task(coordinator.start_coordinator)
        
        return {
            "status": "success",
            "message": "Federated learning coordinator started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start coordinator: {str(e)}")

@router.post("/coordinator/stop")
async def stop_coordinator(
    current_user: User = Depends(get_current_active_user)
):
    """
    Stop the federated learning coordinator
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        coordinator = get_fl_coordinator()
        await coordinator.stop_coordinator()
        
        return {
            "status": "success",
            "message": "Federated learning coordinator stopped"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop coordinator: {str(e)}")

@router.get("/privacy/info")
async def get_privacy_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get information about privacy-preserving techniques used
    """
    return {
        "differential_privacy": {
            "description": "Adds calibrated noise to protect individual data points",
            "mechanisms": ["Laplace", "Gaussian"],
            "default_epsilon": 1.0,
            "default_delta": 1e-5
        },
        "secure_aggregation": {
            "description": "Encrypts model updates during aggregation",
            "encryption": "Fernet (symmetric)",
            "aggregation_method": "Federated averaging"
        },
        "gradient_clipping": {
            "description": "Bounds gradient sensitivity for privacy guarantees",
            "default_clip_norm": 1.0
        },
        "federated_learning": {
            "description": "Trains models without centralizing raw data",
            "benefits": [
                "Data locality preservation",
                "Privacy by design",
                "Reduced data transfer",
                "Collaborative learning"
            ]
        }
    }

@router.get("/model-types")
async def get_supported_model_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get supported model types for federated learning
    """
    return {
        "supported_models": [
            {
                "type": "fraud_detection",
                "name": "Fraud Detection",
                "description": "Binary classification for fraudulent transaction detection",
                "use_case": "AML compliance and fraud prevention"
            },
            {
                "type": "risk_scoring",
                "name": "Risk Scoring", 
                "description": "Regression model for customer risk assessment",
                "use_case": "Customer risk profiling and scoring"
            },
            {
                "type": "customer_segmentation",
                "name": "Customer Segmentation",
                "description": "Clustering model for customer behavior analysis",
                "use_case": "Marketing and personalization"
            },
            {
                "type": "anomaly_detection",
                "name": "Anomaly Detection",
                "description": "Unsupervised learning for unusual pattern detection",
                "use_case": "Operational monitoring and security"
            }
        ]
    }

@router.get("/health")
async def federated_learning_health_check():
    """
    Health check for federated learning service
    """
    try:
        coordinator = get_fl_coordinator()
        stats = coordinator.get_coordinator_stats()
        
        return {
            "status": "healthy" if coordinator.is_running else "stopped",
            "coordinator_running": coordinator.is_running,
            "active_experiments": stats["active_experiments"],
            "active_participants": stats["active_participants"],
            "total_experiments": stats["total_experiments"]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }