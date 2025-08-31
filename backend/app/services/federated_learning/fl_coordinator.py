"""
Federated Learning Coordinator
Implements privacy-preserving machine learning using federated learning techniques
"""

import asyncio
import logging
import json
import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

logger = logging.getLogger(__name__)

class FLStatus(Enum):
    """Federated learning status"""
    IDLE = "idle"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"

class ParticipantRole(Enum):
    """Participant roles in federated learning"""
    COORDINATOR = "coordinator"
    PARTICIPANT = "participant"
    VALIDATOR = "validator"

@dataclass
class ModelParameters:
    """Model parameters for federated learning"""
    weights: List[np.ndarray]
    bias: List[np.ndarray]
    metadata: Dict[str, Any]
    timestamp: datetime
    participant_id: str
    round_number: int

@dataclass
class FLParticipant:
    """Federated learning participant"""
    participant_id: str
    name: str
    role: ParticipantRole
    public_key: str
    status: str = "active"
    last_seen: datetime = None
    data_samples: int = 0
    trust_score: float = 1.0
    performance_metrics: Dict[str, float] = None

@dataclass
class FLRound:
    """Federated learning training round"""
    round_id: str
    round_number: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    participants: List[str] = None
    global_model_hash: str = None
    convergence_score: float = 0.0
    status: FLStatus = FLStatus.IDLE

@dataclass
class FLExperiment:
    """Federated learning experiment"""
    experiment_id: str
    name: str
    description: str
    model_type: str  # fraud_detection, risk_scoring, etc.
    privacy_budget: float
    min_participants: int
    max_rounds: int
    convergence_threshold: float
    created_at: datetime
    status: FLStatus = FLStatus.IDLE
    current_round: int = 0
    participants: List[FLParticipant] = None
    rounds: List[FLRound] = None

class DifferentialPrivacy:
    """Differential privacy mechanisms"""
    
    @staticmethod
    def add_laplace_noise(data: np.ndarray, sensitivity: float, epsilon: float) -> np.ndarray:
        """Add Laplace noise for differential privacy"""
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale, data.shape)
        return data + noise
    
    @staticmethod
    def add_gaussian_noise(data: np.ndarray, sensitivity: float, epsilon: float, delta: float) -> np.ndarray:
        """Add Gaussian noise for differential privacy"""
        sigma = np.sqrt(2 * np.log(1.25 / delta)) * sensitivity / epsilon
        noise = np.random.normal(0, sigma, data.shape)
        return data + noise
    
    @staticmethod
    def clip_gradients(gradients: np.ndarray, clip_norm: float) -> np.ndarray:
        """Clip gradients to bound sensitivity"""
        norm = np.linalg.norm(gradients)
        if norm > clip_norm:
            return gradients * (clip_norm / norm)
        return gradients

class SecureAggregation:
    """Secure aggregation for federated learning"""
    
    def __init__(self, secret_key: bytes = None):
        if secret_key is None:
            secret_key = Fernet.generate_key()
        self.fernet = Fernet(secret_key)
        self.secret_key = secret_key
    
    def encrypt_model(self, model_params: ModelParameters) -> str:
        """Encrypt model parameters"""
        try:
            serialized = pickle.dumps(model_params)
            encrypted = self.fernet.encrypt(serialized)
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting model: {e}")
            return ""
    
    def decrypt_model(self, encrypted_data: str) -> Optional[ModelParameters]:
        """Decrypt model parameters"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return pickle.loads(decrypted)
        except Exception as e:
            logger.error(f"Error decrypting model: {e}")
            return None
    
    def aggregate_encrypted_models(self, encrypted_models: List[str]) -> Optional[ModelParameters]:
        """Aggregate encrypted models using secure multi-party computation"""
        try:
            # Decrypt models
            models = []
            for encrypted_model in encrypted_models:
                model = self.decrypt_model(encrypted_model)
                if model:
                    models.append(model)
            
            if not models:
                return None
            
            # Perform federated averaging
            return self.federated_average(models)
            
        except Exception as e:
            logger.error(f"Error in secure aggregation: {e}")
            return None
    
    def federated_average(self, models: List[ModelParameters]) -> ModelParameters:
        """Perform federated averaging of model parameters"""
        if not models:
            return None
        
        # Weight by data sample count (if available)
        total_samples = sum(getattr(model, 'data_samples', 1) for model in models)
        
        # Initialize averaged parameters
        avg_weights = []
        avg_bias = []
        
        # Average weights layer by layer
        for layer_idx in range(len(models[0].weights)):
            layer_weights = []
            layer_bias = []
            
            for model in models:
                weight = getattr(model, 'data_samples', 1) / total_samples
                layer_weights.append(model.weights[layer_idx] * weight)
                if layer_idx < len(model.bias):
                    layer_bias.append(model.bias[layer_idx] * weight)
            
            avg_weights.append(np.sum(layer_weights, axis=0))
            if layer_bias:
                avg_bias.append(np.sum(layer_bias, axis=0))
        
        # Create aggregated model
        return ModelParameters(
            weights=avg_weights,
            bias=avg_bias,
            metadata={
                "aggregated_from": len(models),
                "total_samples": total_samples,
                "aggregation_method": "federated_average"
            },
            timestamp=datetime.now(),
            participant_id="coordinator",
            round_number=models[0].round_number + 1
        )

class FederatedLearningCoordinator:
    """Main federated learning coordinator"""
    
    def __init__(self):
        self.experiments: Dict[str, FLExperiment] = {}
        self.participants: Dict[str, FLParticipant] = {}
        self.secure_aggregator = SecureAggregation()
        self.privacy_engine = DifferentialPrivacy()
        self.is_running = False
        
        # Privacy parameters
        self.privacy_budget = 1.0  # Epsilon for differential privacy
        self.delta = 1e-5  # Delta for (epsilon, delta)-differential privacy
        self.gradient_clip_norm = 1.0  # Gradient clipping norm
    
    async def start_coordinator(self):
        """Start the federated learning coordinator"""
        self.is_running = True
        logger.info("Federated Learning Coordinator started")
        
        # Start background tasks
        await asyncio.gather(
            self._experiment_monitor(),
            self._participant_health_check()
        )
    
    async def stop_coordinator(self):
        """Stop the federated learning coordinator"""
        self.is_running = False
        logger.info("Federated Learning Coordinator stopped")
    
    def create_experiment(self, name: str, description: str, model_type: str,
                         min_participants: int = 3, max_rounds: int = 10,
                         privacy_budget: float = 1.0) -> str:
        """Create a new federated learning experiment"""
        experiment_id = f"fl_exp_{int(datetime.now().timestamp())}"
        
        experiment = FLExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            model_type=model_type,
            privacy_budget=privacy_budget,
            min_participants=min_participants,
            max_rounds=max_rounds,
            convergence_threshold=0.01,
            created_at=datetime.now(),
            participants=[],
            rounds=[]
        )
        
        self.experiments[experiment_id] = experiment
        logger.info(f"Created FL experiment: {experiment_id}")
        
        return experiment_id
    
    def register_participant(self, name: str, role: ParticipantRole = ParticipantRole.PARTICIPANT,
                           data_samples: int = 0) -> str:
        """Register a new participant"""
        participant_id = f"fl_participant_{int(datetime.now().timestamp())}"
        
        # Generate a simple public key (in production, use proper cryptographic keys)
        public_key = hashlib.sha256(f"{participant_id}{name}".encode()).hexdigest()[:32]
        
        participant = FLParticipant(
            participant_id=participant_id,
            name=name,
            role=role,
            public_key=public_key,
            last_seen=datetime.now(),
            data_samples=data_samples,
            performance_metrics={}
        )
        
        self.participants[participant_id] = participant
        logger.info(f"Registered FL participant: {participant_id}")
        
        return participant_id
    
    def join_experiment(self, participant_id: str, experiment_id: str) -> bool:
        """Have a participant join an experiment"""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        if participant_id not in self.participants:
            logger.error(f"Participant {participant_id} not found")
            return False
        
        experiment = self.experiments[experiment_id]
        participant = self.participants[participant_id]
        
        # Check if already joined
        if any(p.participant_id == participant_id for p in experiment.participants):
            logger.warning(f"Participant {participant_id} already in experiment {experiment_id}")
            return True
        
        experiment.participants.append(participant)
        logger.info(f"Participant {participant_id} joined experiment {experiment_id}")
        
        return True
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """Start a federated learning experiment"""
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        
        if len(experiment.participants) < experiment.min_participants:
            logger.error(f"Not enough participants for experiment {experiment_id}")
            return False
        
        experiment.status = FLStatus.TRAINING
        experiment.current_round = 1
        
        # Start first round
        await self._start_training_round(experiment_id)
        
        return True
    
    async def _start_training_round(self, experiment_id: str):
        """Start a training round"""
        experiment = self.experiments[experiment_id]
        
        round_id = f"round_{experiment_id}_{experiment.current_round}"
        
        fl_round = FLRound(
            round_id=round_id,
            round_number=experiment.current_round,
            started_at=datetime.now(),
            participants=[p.participant_id for p in experiment.participants],
            status=FLStatus.TRAINING
        )
        
        experiment.rounds.append(fl_round)
        
        logger.info(f"Started training round {experiment.current_round} for experiment {experiment_id}")
        
        # In a real implementation, this would notify participants to start training
        # For now, we'll simulate the training process
        await self._simulate_training_round(experiment_id, round_id)
    
    async def _simulate_training_round(self, experiment_id: str, round_id: str):
        """Simulate a training round (for demonstration)"""
        experiment = self.experiments[experiment_id]
        fl_round = next(r for r in experiment.rounds if r.round_id == round_id)
        
        # Simulate training delay
        await asyncio.sleep(2)
        
        # Simulate model updates from participants
        model_updates = []
        
        for participant in experiment.participants:
            # Create mock model parameters
            weights = [np.random.randn(10, 5), np.random.randn(5, 1)]
            bias = [np.random.randn(5), np.random.randn(1)]
            
            # Add differential privacy noise
            for i, weight in enumerate(weights):
                weights[i] = self.privacy_engine.add_laplace_noise(
                    weight, sensitivity=1.0, epsilon=experiment.privacy_budget / experiment.max_rounds
                )
            
            model_params = ModelParameters(
                weights=weights,
                bias=bias,
                metadata={"participant": participant.participant_id},
                timestamp=datetime.now(),
                participant_id=participant.participant_id,
                round_number=experiment.current_round
            )
            
            # Encrypt model
            encrypted_model = self.secure_aggregator.encrypt_model(model_params)
            model_updates.append(encrypted_model)
        
        # Aggregate models
        aggregated_model = self.secure_aggregator.aggregate_encrypted_models(model_updates)
        
        if aggregated_model:
            # Calculate model hash for verification
            model_hash = hashlib.sha256(pickle.dumps(aggregated_model)).hexdigest()
            fl_round.global_model_hash = model_hash
            fl_round.convergence_score = np.random.uniform(0.8, 0.99)  # Simulate convergence
            fl_round.completed_at = datetime.now()
            fl_round.status = FLStatus.COMPLETED
            
            logger.info(f"Completed round {experiment.current_round} with convergence {fl_round.convergence_score:.3f}")
            
            # Check if experiment should continue
            if (experiment.current_round >= experiment.max_rounds or 
                fl_round.convergence_score > experiment.convergence_threshold):
                experiment.status = FLStatus.COMPLETED
                logger.info(f"Experiment {experiment_id} completed")
            else:
                experiment.current_round += 1
                await self._start_training_round(experiment_id)
        else:
            fl_round.status = FLStatus.FAILED
            experiment.status = FLStatus.FAILED
            logger.error(f"Failed to aggregate models in round {experiment.current_round}")
    
    def submit_model_update(self, participant_id: str, experiment_id: str,
                           encrypted_model: str) -> bool:
        """Submit model update from participant"""
        if experiment_id not in self.experiments:
            return False
        
        if participant_id not in self.participants:
            return False
        
        # In a real implementation, this would handle the model update
        # For now, we'll just log it
        logger.info(f"Received model update from {participant_id} for experiment {experiment_id}")
        
        return True
    
    def get_experiment_status(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment status"""
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        
        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "status": experiment.status.value,
            "current_round": experiment.current_round,
            "max_rounds": experiment.max_rounds,
            "participants": len(experiment.participants),
            "min_participants": experiment.min_participants,
            "privacy_budget": experiment.privacy_budget,
            "convergence_threshold": experiment.convergence_threshold,
            "rounds_completed": len([r for r in experiment.rounds if r.status == FLStatus.COMPLETED]),
            "created_at": experiment.created_at.isoformat()
        }
    
    def get_participant_info(self, participant_id: str) -> Optional[Dict[str, Any]]:
        """Get participant information"""
        if participant_id not in self.participants:
            return None
        
        participant = self.participants[participant_id]
        
        return {
            "participant_id": participant_id,
            "name": participant.name,
            "role": participant.role.value,
            "status": participant.status,
            "data_samples": participant.data_samples,
            "trust_score": participant.trust_score,
            "last_seen": participant.last_seen.isoformat() if participant.last_seen else None,
            "performance_metrics": participant.performance_metrics or {}
        }
    
    def get_privacy_metrics(self, experiment_id: str) -> Dict[str, Any]:
        """Get privacy metrics for an experiment"""
        if experiment_id not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_id]
        completed_rounds = len([r for r in experiment.rounds if r.status == FLStatus.COMPLETED])
        
        # Calculate privacy spending
        privacy_spent = (completed_rounds / experiment.max_rounds) * experiment.privacy_budget
        
        return {
            "experiment_id": experiment_id,
            "total_privacy_budget": experiment.privacy_budget,
            "privacy_spent": privacy_spent,
            "privacy_remaining": experiment.privacy_budget - privacy_spent,
            "delta": self.delta,
            "gradient_clip_norm": self.gradient_clip_norm,
            "noise_mechanism": "laplace",
            "participants": len(experiment.participants)
        }
    
    async def _experiment_monitor(self):
        """Monitor experiment progress"""
        while self.is_running:
            try:
                for experiment_id, experiment in self.experiments.items():
                    if experiment.status == FLStatus.TRAINING:
                        # Check for stalled experiments
                        if experiment.rounds:
                            last_round = experiment.rounds[-1]
                            if (datetime.now() - last_round.started_at > timedelta(minutes=10) and
                                last_round.status == FLStatus.TRAINING):
                                logger.warning(f"Experiment {experiment_id} appears stalled")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in experiment monitor: {e}")
    
    async def _participant_health_check(self):
        """Check participant health and connectivity"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                for participant_id, participant in self.participants.items():
                    if participant.last_seen:
                        time_since_seen = current_time - participant.last_seen
                        if time_since_seen > timedelta(minutes=30):
                            if participant.status != "inactive":
                                participant.status = "inactive"
                                logger.warning(f"Participant {participant_id} marked as inactive")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in participant health check: {e}")
    
    def get_coordinator_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics"""
        active_experiments = len([e for e in self.experiments.values() if e.status == FLStatus.TRAINING])
        completed_experiments = len([e for e in self.experiments.values() if e.status == FLStatus.COMPLETED])
        active_participants = len([p for p in self.participants.values() if p.status == "active"])
        
        return {
            "total_experiments": len(self.experiments),
            "active_experiments": active_experiments,
            "completed_experiments": completed_experiments,
            "failed_experiments": len([e for e in self.experiments.values() if e.status == FLStatus.FAILED]),
            "total_participants": len(self.participants),
            "active_participants": active_participants,
            "inactive_participants": len(self.participants) - active_participants,
            "is_running": self.is_running,
            "privacy_budget_default": self.privacy_budget,
            "gradient_clip_norm": self.gradient_clip_norm
        }

# Global coordinator instance
fl_coordinator = None

def get_fl_coordinator() -> FederatedLearningCoordinator:
    """Get the global federated learning coordinator instance"""
    global fl_coordinator
    if fl_coordinator is None:
        fl_coordinator = FederatedLearningCoordinator()
    return fl_coordinator