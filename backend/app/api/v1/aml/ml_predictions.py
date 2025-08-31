"""
ML Predictions API for advanced analytics and predictive capabilities
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.aml.ml_prediction_engine import get_ml_engine, PredictionResult, AnomalyResult, RiskForecast

router = APIRouter()

# Pydantic models for request/response
class TransactionPredictionRequest(BaseModel):
    amount: float
    country: Optional[str] = None
    customer_id: Optional[int] = None
    transaction_date: Optional[datetime] = None
    transaction_type: Optional[str] = None

class AnomalyDetectionRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    sensitivity: float = 0.1

class RiskForecastRequest(BaseModel):
    customer_id: int
    forecast_days: int = 30

class ModelTrainingRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    model_type: str
    retrain: bool = False

class PredictionResponse(BaseModel):
    prediction: float
    confidence: float
    risk_level: str
    explanation: List[str]
    timestamp: datetime

class AnomalyResponse(BaseModel):
    total_transactions: int
    anomalies_detected: int
    anomaly_rate: float
    results: List[Dict[str, Any]]

class ForecastResponse(BaseModel):
    customer_id: int
    forecast: Dict[str, Any]
    recommendations: List[str]

@router.post("/predict/fraud", response_model=PredictionResponse)
def predict_fraud(
    request: TransactionPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Predict fraud probability for a transaction using ML models
    """
    try:
        ml_engine = get_ml_engine()
        
        # Prepare transaction data
        transaction_data = {
            "amount": request.amount,
            "country": request.country or "US",
            "customer_id": request.customer_id or 0,
            "transaction_date": request.transaction_date or datetime.now(),
            "transaction_type": request.transaction_type or "transfer"
        }
        
        # Get prediction
        result = ml_engine.predict_fraud_probability(transaction_data)
        
        # Determine risk level
        if result.prediction > 0.8:
            risk_level = "CRITICAL"
        elif result.prediction > 0.6:
            risk_level = "HIGH"
        elif result.prediction > 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Generate explanation
        explanation = []
        for feature, importance in sorted(result.feature_importance.items(), 
                                        key=lambda x: x[1], reverse=True)[:5]:
            if importance > 0.1:
                explanation.append(f"{feature}: {importance:.2f} importance")
        
        return PredictionResponse(
            prediction=result.prediction,
            confidence=result.confidence,
            risk_level=risk_level,
            explanation=explanation,
            timestamp=result.timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/detect/anomalies", response_model=AnomalyResponse)
def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Detect anomalies in a batch of transactions
    """
    try:
        ml_engine = get_ml_engine()
        
        # Detect anomalies
        results = ml_engine.detect_anomalies(request.transactions)
        
        # Count anomalies
        anomalies_count = sum(1 for r in results if r.is_anomaly)
        anomaly_rate = anomalies_count / len(results) if results else 0
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append({
                "transaction_index": i,
                "is_anomaly": result.is_anomaly,
                "anomaly_score": result.anomaly_score,
                "severity": result.severity,
                "risk_factors": result.risk_factors,
                "timestamp": result.timestamp.isoformat()
            })
        
        return AnomalyResponse(
            total_transactions=len(request.transactions),
            anomalies_detected=anomalies_count,
            anomaly_rate=anomaly_rate,
            results=formatted_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@router.post("/forecast/risk", response_model=ForecastResponse)
def forecast_customer_risk(
    request: RiskForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Forecast customer risk for the specified period
    """
    try:
        ml_engine = get_ml_engine()
        
        # Get risk forecast
        forecast = ml_engine.forecast_customer_risk(
            request.customer_id, 
            db, 
            request.forecast_days
        )
        
        # Generate recommendations based on forecast
        recommendations = []
        if forecast.predicted_risk_score > 70:
            recommendations.extend([
                "Consider enhanced monitoring",
                "Review recent transaction patterns",
                "Update customer risk profile"
            ])
        elif forecast.trend_direction == "increasing":
            recommendations.extend([
                "Monitor for unusual activity",
                "Review account activity"
            ])
        else:
            recommendations.append("Continue standard monitoring")
        
        forecast_data = {
            "period": forecast.forecast_period,
            "predicted_score": forecast.predicted_risk_score,
            "confidence_interval": {
                "lower": forecast.confidence_interval[0],
                "upper": forecast.confidence_interval[1]
            },
            "trend": forecast.trend_direction,
            "key_drivers": forecast.key_drivers
        }
        
        return ForecastResponse(
            customer_id=request.customer_id,
            forecast=forecast_data,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk forecasting failed: {str(e)}")

@router.post("/models/train")
def train_model(
    request: ModelTrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Train or retrain ML models
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    ml_engine = get_ml_engine()
    
    def train_model_background():
        if request.model_type == "fraud_classifier":
            return ml_engine.train_fraud_classifier(db, request.retrain)
        else:
            return {"status": "error", "message": f"Unknown model type: {request.model_type}"}
    
    # Start training in background
    background_tasks.add_task(train_model_background)
    
    return {
        "status": "training_started",
        "model_type": request.model_type,
        "message": "Model training started in background"
    }

@router.get("/models/performance")
def get_model_performance(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get performance metrics for all ML models
    """
    ml_engine = get_ml_engine()
    return ml_engine.get_model_performance_metrics()

@router.post("/clustering/customers")
def cluster_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Perform customer clustering analysis
    """
    try:
        ml_engine = get_ml_engine()
        results = ml_engine.cluster_customers(db)
        
        # Add insights based on clustering results
        if results.get("status") == "success":
            insights = []
            clusters = results.get("clusters", {})
            
            # Find high-risk clusters
            high_risk_clusters = [
                cluster_id for cluster_id, data in clusters.items()
                if data.get("risk_level") == "high"
            ]
            
            if high_risk_clusters:
                insights.append(f"Found {len(high_risk_clusters)} high-risk customer segments")
            
            # Find large transaction clusters
            large_clusters = [
                cluster_id for cluster_id, data in clusters.items()
                if data.get("size", 0) > 50
            ]
            
            if large_clusters:
                insights.append(f"Identified {len(large_clusters)} major customer segments")
            
            results["insights"] = insights
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer clustering failed: {str(e)}")

@router.get("/analytics/risk-trends")
def get_risk_trends(
    days: int = 30,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get risk trend analysis using ML predictions
    """
    try:
        ml_engine = get_ml_engine()
        
        # Get recent transactions for trend analysis
        from app.models.aml.transaction import Transaction
        
        query = db.query(Transaction)
        if customer_id:
            query = query.filter(Transaction.customer_id == customer_id)
        
        transactions = query.filter(
            Transaction.transaction_date > datetime.now() - timedelta(days=days)
        ).all()
        
        if not transactions:
            return {"message": "No transactions found for the specified period"}
        
        # Convert to transaction data format
        transaction_data = []
        for tx in transactions:
            transaction_data.append({
                "amount": tx.amount,
                "country": tx.country,
                "customer_id": tx.customer_id,
                "transaction_date": tx.transaction_date,
                "transaction_type": getattr(tx, 'transaction_type', 'transfer')
            })
        
        # Get fraud predictions for all transactions
        risk_scores = []
        for tx_data in transaction_data[:100]:  # Limit for performance
            prediction = ml_engine.predict_fraud_probability(tx_data)
            risk_scores.append({
                "date": tx_data["transaction_date"].date().isoformat(),
                "risk_score": prediction.prediction * 100,
                "amount": tx_data["amount"]
            })
        
        # Group by date and calculate daily averages
        daily_risks = {}
        for score in risk_scores:
            date = score["date"]
            if date not in daily_risks:
                daily_risks[date] = {"scores": [], "amounts": []}
            daily_risks[date]["scores"].append(score["risk_score"])
            daily_risks[date]["amounts"].append(score["amount"])
        
        trend_data = []
        for date, data in sorted(daily_risks.items()):
            trend_data.append({
                "date": date,
                "avg_risk_score": sum(data["scores"]) / len(data["scores"]),
                "max_risk_score": max(data["scores"]),
                "transaction_count": len(data["scores"]),
                "total_amount": sum(data["amounts"])
            })
        
        # Calculate trend direction
        if len(trend_data) >= 2:
            recent_avg = sum(day["avg_risk_score"] for day in trend_data[-7:]) / min(7, len(trend_data))
            earlier_avg = sum(day["avg_risk_score"] for day in trend_data[:7]) / min(7, len(trend_data))
            trend = "increasing" if recent_avg > earlier_avg + 5 else "decreasing" if recent_avg < earlier_avg - 5 else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "period": f"{days} days",
            "customer_id": customer_id,
            "trend_direction": trend,
            "daily_data": trend_data,
            "summary": {
                "total_transactions_analyzed": len(risk_scores),
                "avg_risk_score": sum(day["avg_risk_score"] for day in trend_data) / len(trend_data) if trend_data else 0,
                "high_risk_days": len([day for day in trend_data if day["avg_risk_score"] > 60])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk trend analysis failed: {str(e)}")

@router.get("/analytics/predictive-insights")
def get_predictive_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get AI-powered predictive insights for risk management
    """
    try:
        ml_engine = get_ml_engine()
        
        # Get model performance
        model_metrics = ml_engine.get_model_performance_metrics()
        
        # Generate insights based on model status and performance
        insights = []
        
        if model_metrics.get("fraud_classifier", {}).get("status") == "loaded":
            insights.append({
                "type": "model_status",
                "title": "Fraud Detection Model Active",
                "description": "ML-powered fraud detection is available for real-time transaction scoring",
                "impact": "high",
                "recommendation": "Continue monitoring model performance and retrain monthly"
            })
        else:
            insights.append({
                "type": "model_status",
                "title": "Fraud Detection Model Not Trained",
                "description": "ML fraud detection model needs training with historical data",
                "impact": "high",
                "recommendation": "Train the fraud detection model with recent transaction data"
            })
        
        # Add general ML insights
        insights.extend([
            {
                "type": "capability",
                "title": "Anomaly Detection Available",
                "description": "Batch anomaly detection can identify unusual transaction patterns",
                "impact": "medium",
                "recommendation": "Run weekly anomaly detection on high-value customers"
            },
            {
                "type": "capability",
                "title": "Customer Risk Forecasting",
                "description": "Predictive models can forecast customer risk trends",
                "impact": "medium",
                "recommendation": "Use risk forecasting for proactive customer management"
            },
            {
                "type": "optimization",
                "title": "Customer Clustering Analysis",
                "description": "ML clustering can segment customers by behavior patterns",
                "impact": "low",
                "recommendation": "Perform quarterly customer segmentation for targeted monitoring"
            }
        ])
        
        return {
            "insights": insights,
            "model_status": model_metrics,
            "recommendations": [
                "Implement regular model retraining schedule",
                "Monitor model performance metrics",
                "Use ensemble methods for critical predictions",
                "Maintain feature quality and consistency"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")