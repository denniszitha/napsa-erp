"""
Advanced ML Prediction Engine for AML and Risk Management
Provides predictive analytics, anomaly detection, and risk forecasting capabilities
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error
from sklearn.cluster import DBSCAN, KMeans
import joblib
import os
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.aml.transaction import Transaction
from app.models.aml.customer import CustomerProfile
from app.models.aml.case import ComplianceCase
from app.core.clickhouse import get_clickhouse_client

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Result of ML prediction"""
    prediction: float
    confidence: float
    feature_importance: Dict[str, float]
    model_type: str
    timestamp: datetime

@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    is_anomaly: bool
    anomaly_score: float
    risk_factors: List[str]
    severity: str  # low, medium, high, critical
    timestamp: datetime

@dataclass
class RiskForecast:
    """Risk forecasting result"""
    forecast_period: str
    predicted_risk_score: float
    confidence_interval: Tuple[float, float]
    trend_direction: str  # increasing, decreasing, stable
    key_drivers: List[str]

class MLPredictionEngine:
    """Advanced ML engine for AML and risk predictions"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_directory = "ml_models"
        self.clickhouse_client = None
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize ML models and create model directory"""
        os.makedirs(self.model_directory, exist_ok=True)
        
        # Initialize models
        self.models = {
            'fraud_classifier': RandomForestClassifier(
                n_estimators=100, 
                max_depth=10, 
                random_state=42,
                class_weight='balanced'
            ),
            'risk_regressor': GradientBoostingRegressor(
                n_estimators=100, 
                max_depth=8, 
                random_state=42
            ),
            'anomaly_detector': IsolationForest(
                contamination=0.1, 
                random_state=42,
                n_estimators=100
            ),
            'clustering_model': DBSCAN(eps=0.5, min_samples=5)
        }
        
        # Initialize scalers and encoders
        self.scalers = {
            'transaction_scaler': StandardScaler(),
            'customer_scaler': StandardScaler()
        }
        
        self.encoders = {
            'categorical_encoder': LabelEncoder()
        }
        
        try:
            self.clickhouse_client = get_clickhouse_client()
        except Exception as e:
            logger.warning(f"ClickHouse not available: {e}")

    def prepare_features(self, data: pd.DataFrame, feature_type: str = 'transaction') -> pd.DataFrame:
        """Prepare features for ML models"""
        try:
            if feature_type == 'transaction':
                return self._prepare_transaction_features(data)
            elif feature_type == 'customer':
                return self._prepare_customer_features(data)
            else:
                raise ValueError(f"Unknown feature type: {feature_type}")
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return pd.DataFrame()

    def _prepare_transaction_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare transaction-specific features"""
        features = data.copy()
        
        # Basic transaction features
        if 'amount' in features.columns:
            features['log_amount'] = np.log1p(features['amount'])
            features['amount_z_score'] = (features['amount'] - features['amount'].mean()) / features['amount'].std()
        
        # Time-based features
        if 'transaction_date' in features.columns:
            features['hour'] = pd.to_datetime(features['transaction_date']).dt.hour
            features['day_of_week'] = pd.to_datetime(features['transaction_date']).dt.dayofweek
            features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
            features['is_night'] = ((features['hour'] >= 22) | (features['hour'] <= 6)).astype(int)
        
        # Customer behavior features (if customer data available)
        if 'customer_id' in features.columns:
            customer_stats = features.groupby('customer_id')['amount'].agg([
                'count', 'sum', 'mean', 'std', 'min', 'max'
            ]).reset_index()
            customer_stats.columns = ['customer_id', 'tx_count', 'tx_sum', 'tx_mean', 'tx_std', 'tx_min', 'tx_max']
            features = features.merge(customer_stats, on='customer_id', how='left')
        
        # Geographic features
        if 'country' in features.columns:
            country_risk = {
                'US': 0.1, 'CA': 0.1, 'GB': 0.2, 'DE': 0.2, 'FR': 0.2,
                'CN': 0.6, 'RU': 0.7, 'IR': 0.9, 'KP': 0.9
            }
            features['country_risk'] = features['country'].map(country_risk).fillna(0.5)
        
        # Round amount patterns
        if 'amount' in features.columns:
            features['is_round_100'] = (features['amount'] % 100 == 0).astype(int)
            features['is_round_1000'] = (features['amount'] % 1000 == 0).astype(int)
        
        return features

    def _prepare_customer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare customer-specific features"""
        features = data.copy()
        
        # Customer profile features
        if 'age' in features.columns:
            features['age_risk'] = np.where(features['age'] < 25, 0.3,
                                  np.where(features['age'] > 65, 0.4, 0.1))
        
        # Account features
        if 'account_balance' in features.columns:
            features['log_balance'] = np.log1p(features['account_balance'])
        
        # Transaction history aggregations (requires transaction data)
        # This would be populated from transaction history analysis
        
        return features

    def train_fraud_classifier(self, db: Session, retrain: bool = False) -> Dict[str, Any]:
        """Train fraud classification model"""
        try:
            model_path = os.path.join(self.model_directory, 'fraud_classifier.joblib')
            
            # Check if model exists and retrain is False
            if os.path.exists(model_path) and not retrain:
                self.models['fraud_classifier'] = joblib.load(model_path)
                return {"status": "loaded", "message": "Existing model loaded"}
            
            # Get training data
            training_data = self._get_fraud_training_data(db)
            if training_data.empty:
                return {"status": "error", "message": "No training data available"}
            
            # Prepare features
            features = self.prepare_features(training_data, 'transaction')
            
            # Select numeric features for training
            numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
            if 'is_fraud' in numeric_features:
                numeric_features.remove('is_fraud')
            
            X = features[numeric_features].fillna(0)
            y = features['is_fraud'] if 'is_fraud' in features.columns else np.zeros(len(features))
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
            )
            
            # Scale features
            X_train_scaled = self.scalers['transaction_scaler'].fit_transform(X_train)
            X_test_scaled = self.scalers['transaction_scaler'].transform(X_test)
            
            # Train model
            self.models['fraud_classifier'].fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_score = self.models['fraud_classifier'].score(X_train_scaled, y_train)
            test_score = self.models['fraud_classifier'].score(X_test_scaled, y_test)
            
            # Save model and scaler
            joblib.dump(self.models['fraud_classifier'], model_path)
            joblib.dump(self.scalers['transaction_scaler'], 
                       os.path.join(self.model_directory, 'transaction_scaler.joblib'))
            
            return {
                "status": "success",
                "train_score": train_score,
                "test_score": test_score,
                "features_used": numeric_features,
                "training_samples": len(X_train)
            }
            
        except Exception as e:
            logger.error(f"Error training fraud classifier: {e}")
            return {"status": "error", "message": str(e)}

    def predict_fraud_probability(self, transaction_data: Dict[str, Any]) -> PredictionResult:
        """Predict fraud probability for a transaction"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame([transaction_data])
            
            # Prepare features
            features = self.prepare_features(df, 'transaction')
            numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
            X = features[numeric_features].fillna(0)
            
            # Scale features
            X_scaled = self.scalers['transaction_scaler'].transform(X)
            
            # Predict
            fraud_prob = self.models['fraud_classifier'].predict_proba(X_scaled)[0][1]
            confidence = max(self.models['fraud_classifier'].predict_proba(X_scaled)[0]) - 0.5
            
            # Get feature importance
            feature_importance = dict(zip(
                numeric_features,
                self.models['fraud_classifier'].feature_importances_
            ))
            
            return PredictionResult(
                prediction=fraud_prob,
                confidence=confidence,
                feature_importance=feature_importance,
                model_type="RandomForest",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error predicting fraud: {e}")
            return PredictionResult(
                prediction=0.5,
                confidence=0.0,
                feature_importance={},
                model_type="Error",
                timestamp=datetime.now()
            )

    def detect_anomalies(self, transaction_data: List[Dict[str, Any]]) -> List[AnomalyResult]:
        """Detect anomalies in transaction data"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(transaction_data)
            
            # Prepare features
            features = self.prepare_features(df, 'transaction')
            numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
            X = features[numeric_features].fillna(0)
            
            # Detect anomalies
            anomaly_scores = self.models['anomaly_detector'].decision_function(X)
            anomalies = self.models['anomaly_detector'].predict(X)
            
            results = []
            for i, (score, is_anomaly) in enumerate(zip(anomaly_scores, anomalies)):
                # Determine severity based on score
                if score < -0.5:
                    severity = "critical"
                elif score < -0.2:
                    severity = "high"
                elif score < 0:
                    severity = "medium"
                else:
                    severity = "low"
                
                # Identify risk factors
                risk_factors = []
                row = features.iloc[i]
                
                if 'amount' in row and row['amount'] > row.get('tx_mean', 0) * 3:
                    risk_factors.append("Unusually high amount")
                if row.get('is_night', 0) == 1:
                    risk_factors.append("Night transaction")
                if row.get('country_risk', 0) > 0.5:
                    risk_factors.append("High-risk country")
                if row.get('is_round_1000', 0) == 1:
                    risk_factors.append("Round amount pattern")
                
                results.append(AnomalyResult(
                    is_anomaly=(is_anomaly == -1),
                    anomaly_score=abs(score),
                    risk_factors=risk_factors,
                    severity=severity,
                    timestamp=datetime.now()
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    def forecast_customer_risk(self, customer_id: int, db: Session, 
                             forecast_days: int = 30) -> RiskForecast:
        """Forecast customer risk for the next period"""
        try:
            # Get historical data
            historical_data = self._get_customer_historical_risk(customer_id, db)
            
            if len(historical_data) < 10:  # Need minimum data points
                return RiskForecast(
                    forecast_period=f"{forecast_days} days",
                    predicted_risk_score=50.0,
                    confidence_interval=(40.0, 60.0),
                    trend_direction="stable",
                    key_drivers=["Insufficient historical data"]
                )
            
            # Prepare time series data
            risk_series = pd.Series(historical_data['risk_score'].values, 
                                  index=pd.to_datetime(historical_data['date']))
            
            # Simple trend analysis (can be replaced with more sophisticated models)
            recent_trend = risk_series.tail(7).mean() - risk_series.head(7).mean()
            
            # Forecast using simple exponential smoothing
            alpha = 0.3  # Smoothing parameter
            forecast = risk_series.iloc[-1]
            
            for _ in range(forecast_days):
                forecast = alpha * forecast + (1 - alpha) * risk_series.mean()
            
            # Determine trend direction
            if recent_trend > 5:
                trend = "increasing"
            elif recent_trend < -5:
                trend = "decreasing"
            else:
                trend = "stable"
            
            # Calculate confidence interval (simple approach)
            std_dev = risk_series.std()
            confidence_lower = max(0, forecast - 1.96 * std_dev)
            confidence_upper = min(100, forecast + 1.96 * std_dev)
            
            # Identify key risk drivers
            key_drivers = self._identify_risk_drivers(customer_id, db)
            
            return RiskForecast(
                forecast_period=f"{forecast_days} days",
                predicted_risk_score=forecast,
                confidence_interval=(confidence_lower, confidence_upper),
                trend_direction=trend,
                key_drivers=key_drivers
            )
            
        except Exception as e:
            logger.error(f"Error forecasting customer risk: {e}")
            return RiskForecast(
                forecast_period=f"{forecast_days} days",
                predicted_risk_score=50.0,
                confidence_interval=(40.0, 60.0),
                trend_direction="stable",
                key_drivers=["Error in calculation"]
            )

    def cluster_customers(self, db: Session) -> Dict[str, Any]:
        """Cluster customers based on behavior patterns"""
        try:
            # Get customer data with aggregated features
            customer_data = self._get_customer_clustering_data(db)
            
            if customer_data.empty:
                return {"status": "error", "message": "No customer data available"}
            
            # Prepare features for clustering
            features = self.prepare_features(customer_data, 'customer')
            numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
            X = features[numeric_features].fillna(0)
            
            # Scale features
            X_scaled = self.scalers['customer_scaler'].fit_transform(X)
            
            # Perform clustering
            clusters = self.models['clustering_model'].fit_predict(X_scaled)
            
            # Analyze clusters
            cluster_analysis = {}
            for cluster_id in set(clusters):
                if cluster_id == -1:  # Noise points in DBSCAN
                    continue
                    
                cluster_mask = clusters == cluster_id
                cluster_data = features[cluster_mask]
                
                cluster_analysis[f"cluster_{cluster_id}"] = {
                    "size": int(cluster_mask.sum()),
                    "avg_transaction_amount": float(cluster_data.get('tx_mean', pd.Series([0])).mean()),
                    "avg_transaction_count": float(cluster_data.get('tx_count', pd.Series([0])).mean()),
                    "risk_level": self._assess_cluster_risk(cluster_data)
                }
            
            return {
                "status": "success",
                "clusters": cluster_analysis,
                "total_customers": len(features),
                "noise_points": int((clusters == -1).sum())
            }
            
        except Exception as e:
            logger.error(f"Error clustering customers: {e}")
            return {"status": "error", "message": str(e)}

    def _get_fraud_training_data(self, db: Session) -> pd.DataFrame:
        """Get training data for fraud detection model"""
        try:
            # Query transactions with fraud labels (alerts as proxy for fraud)
            query = """
            SELECT 
                t.id,
                t.amount,
                t.transaction_date,
                t.country,
                t.customer_id,
                CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END as is_fraud
            FROM transactions t
            LEFT JOIN alerts a ON t.id = a.transaction_id
            WHERE t.transaction_date > NOW() - INTERVAL '6 months'
            """
            
            return pd.read_sql(query, db.bind)
            
        except Exception as e:
            logger.error(f"Error getting fraud training data: {e}")
            return pd.DataFrame()

    def _get_customer_historical_risk(self, customer_id: int, db: Session) -> pd.DataFrame:
        """Get historical risk scores for a customer"""
        try:
            # This would typically come from a risk scoring history table
            # For now, we'll simulate based on transaction patterns
            transactions = db.query(Transaction).filter(
                Transaction.customer_id == customer_id
            ).order_by(Transaction.transaction_date.desc()).limit(100).all()
            
            # Convert to DataFrame and calculate daily risk scores
            data = []
            for tx in transactions:
                # Simple risk scoring based on amount and patterns
                risk_score = min(100, (tx.amount / 1000) * 10 + np.random.normal(50, 10))
                data.append({
                    'date': tx.transaction_date,
                    'risk_score': max(0, risk_score)
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error getting customer historical risk: {e}")
            return pd.DataFrame()

    def _get_customer_clustering_data(self, db: Session) -> pd.DataFrame:
        """Get customer data for clustering analysis"""
        try:
            query = """
            SELECT 
                c.id as customer_id,
                c.age,
                c.account_balance,
                COUNT(t.id) as transaction_count,
                AVG(t.amount) as avg_amount,
                SUM(t.amount) as total_amount,
                MAX(t.amount) as max_amount,
                MIN(t.amount) as min_amount,
                COUNT(DISTINCT t.country) as country_count
            FROM customers c
            LEFT JOIN transactions t ON c.id = t.customer_id
            WHERE t.transaction_date > NOW() - INTERVAL '3 months'
            GROUP BY c.id, c.age, c.account_balance
            """
            
            return pd.read_sql(query, db.bind)
            
        except Exception as e:
            logger.error(f"Error getting customer clustering data: {e}")
            return pd.DataFrame()

    def _identify_risk_drivers(self, customer_id: int, db: Session) -> List[str]:
        """Identify key risk drivers for a customer"""
        drivers = []
        
        try:
            # Get recent transactions
            recent_txs = db.query(Transaction).filter(
                Transaction.customer_id == customer_id,
                Transaction.transaction_date > datetime.now() - timedelta(days=30)
            ).all()
            
            if not recent_txs:
                return ["No recent activity"]
            
            # Analyze patterns
            amounts = [tx.amount for tx in recent_txs]
            avg_amount = np.mean(amounts)
            
            if avg_amount > 10000:
                drivers.append("High-value transactions")
            
            if len(recent_txs) > 50:
                drivers.append("High transaction frequency")
            
            # Check for unusual patterns
            countries = set(tx.country for tx in recent_txs if tx.country)
            if len(countries) > 5:
                drivers.append("Multi-jurisdiction activity")
            
            # Check for round amounts
            round_amounts = sum(1 for amount in amounts if amount % 1000 == 0)
            if round_amounts / len(amounts) > 0.3:
                drivers.append("Frequent round amounts")
            
            return drivers if drivers else ["Normal activity patterns"]
            
        except Exception as e:
            logger.error(f"Error identifying risk drivers: {e}")
            return ["Error in analysis"]

    def _assess_cluster_risk(self, cluster_data: pd.DataFrame) -> str:
        """Assess risk level of a customer cluster"""
        avg_amount = cluster_data.get('tx_mean', pd.Series([0])).mean()
        avg_count = cluster_data.get('tx_count', pd.Series([0])).mean()
        
        if avg_amount > 50000 or avg_count > 100:
            return "high"
        elif avg_amount > 10000 or avg_count > 50:
            return "medium"
        else:
            return "low"

    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all models"""
        metrics = {}
        
        for model_name, model in self.models.items():
            try:
                model_path = os.path.join(self.model_directory, f"{model_name}.joblib")
                if os.path.exists(model_path):
                    metrics[model_name] = {
                        "status": "loaded",
                        "last_updated": datetime.fromtimestamp(
                            os.path.getmtime(model_path)
                        ).isoformat(),
                        "model_type": type(model).__name__
                    }
                else:
                    metrics[model_name] = {
                        "status": "not_trained",
                        "model_type": type(model).__name__
                    }
            except Exception as e:
                metrics[model_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return metrics

# Global instance
ml_engine = MLPredictionEngine()

def get_ml_engine() -> MLPredictionEngine:
    """Get the global ML prediction engine instance"""
    return ml_engine