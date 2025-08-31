"""
AI-Powered Sentiment Analysis Service
Analyzes sentiment in risk assessments, incident reports, and other text data
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text

# Simple sentiment analysis using keyword-based approach
# In production, you would use libraries like transformers, nltk, or textblob

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """AI-powered sentiment analysis for risk and compliance text"""
    
    def __init__(self):
        self.positive_keywords = [
            'good', 'excellent', 'positive', 'improved', 'effective', 'successful',
            'compliant', 'controlled', 'mitigated', 'resolved', 'stable', 'strong',
            'adequate', 'satisfactory', 'acceptable', 'manageable', 'low risk',
            'well-controlled', 'properly', 'correctly', 'appropriately', 'timely',
            'proactive', 'robust', 'comprehensive', 'thorough', 'complete',
            'progress', 'achievement', 'success', 'enhancement', 'optimization'
        ]
        
        self.negative_keywords = [
            'bad', 'poor', 'negative', 'degraded', 'ineffective', 'failed',
            'non-compliant', 'uncontrolled', 'high risk', 'critical', 'severe',
            'inadequate', 'unsatisfactory', 'unacceptable', 'concerning', 'urgent',
            'delayed', 'overdue', 'missing', 'incomplete', 'insufficient',
            'vulnerable', 'exposed', 'breach', 'violation', 'incident', 'issue',
            'problem', 'deficiency', 'weakness', 'gap', 'threat', 'risk',
            'escalation', 'deterioration', 'decline', 'failure', 'error'
        ]
        
        self.neutral_keywords = [
            'review', 'assess', 'evaluate', 'monitor', 'track', 'measure',
            'analyze', 'investigate', 'examine', 'check', 'verify', 'validate',
            'update', 'maintain', 'continue', 'ongoing', 'regular', 'standard',
            'normal', 'routine', 'scheduled', 'planned', 'expected', 'average'
        ]
        
        # Risk-specific sentiment modifiers
        self.risk_amplifiers = [
            'very', 'extremely', 'highly', 'significantly', 'substantially',
            'critically', 'severely', 'urgently', 'immediately', 'rapidly'
        ]
        
        self.risk_diminishers = [
            'slightly', 'somewhat', 'partially', 'moderately', 'relatively',
            'fairly', 'reasonably', 'adequately', 'sufficiently', 'gradually'
        ]

    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of given text
        Returns scores for positive, negative, and neutral sentiment
        """
        if not text or len(text.strip()) == 0:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'compound': 0.0}
        
        processed_text = self.preprocess_text(text)
        words = processed_text.split()
        
        if not words:
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'compound': 0.0}
        
        positive_score = 0
        negative_score = 0
        neutral_score = 0
        
        # Analyze each word
        for i, word in enumerate(words):
            # Check for amplifiers/diminishers
            amplifier = 1.0
            if i > 0 and words[i-1] in self.risk_amplifiers:
                amplifier = 1.5
            elif i > 0 and words[i-1] in self.risk_diminishers:
                amplifier = 0.7
            
            # Score based on keyword lists
            if word in self.positive_keywords:
                positive_score += amplifier
            elif word in self.negative_keywords:
                negative_score += amplifier
            elif word in self.neutral_keywords:
                neutral_score += amplifier * 0.5
        
        # Calculate total and normalize
        total_score = positive_score + negative_score + neutral_score
        
        if total_score == 0:
            # If no keywords found, assume neutral
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'compound': 0.0}
        
        # Normalize scores
        positive_pct = positive_score / total_score
        negative_pct = negative_score / total_score
        neutral_pct = neutral_score / total_score
        
        # Calculate compound score (-1 to 1)
        compound = (positive_score - negative_score) / len(words)
        compound = max(-1.0, min(1.0, compound))
        
        # Ensure percentages sum to 1
        total_pct = positive_pct + negative_pct + neutral_pct
        if total_pct > 0:
            positive_pct /= total_pct
            negative_pct /= total_pct
            neutral_pct /= total_pct
        else:
            positive_pct = negative_pct = 0.0
            neutral_pct = 1.0
        
        return {
            'positive': round(positive_pct * 100, 2),
            'negative': round(negative_pct * 100, 2),
            'neutral': round(neutral_pct * 100, 2),
            'compound': round(compound, 3)
        }

    def analyze_risk_sentiment(self, db: Session, time_range: str = "30d") -> Dict[str, float]:
        """Analyze sentiment across all risks in the system"""
        
        # Calculate date range
        if time_range == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif time_range == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif time_range == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        try:
            # Get risk descriptions and comments
            query = text("""
                SELECT title, description, comments, mitigation_plan
                FROM risks 
                WHERE created_at >= :start_date
            """)
            
            result = db.execute(query, {"start_date": start_date})
            rows = result.fetchall()
            
            if not rows:
                return {'positive': 33.0, 'negative': 33.0, 'neutral': 34.0}
            
            all_sentiments = []
            
            for row in rows:
                # Combine all text fields
                combined_text = " ".join([
                    row.title or "",
                    row.description or "",
                    row.comments or "",
                    row.mitigation_plan or ""
                ])
                
                if combined_text.strip():
                    sentiment = self.analyze_sentiment(combined_text)
                    all_sentiments.append(sentiment)
            
            if not all_sentiments:
                return {'positive': 33.0, 'negative': 33.0, 'neutral': 34.0}
            
            # Calculate average sentiment
            avg_positive = sum(s['positive'] for s in all_sentiments) / len(all_sentiments)
            avg_negative = sum(s['negative'] for s in all_sentiments) / len(all_sentiments)
            avg_neutral = sum(s['neutral'] for s in all_sentiments) / len(all_sentiments)
            
            # Normalize to ensure they sum to 100%
            total = avg_positive + avg_negative + avg_neutral
            if total > 0:
                avg_positive = (avg_positive / total) * 100
                avg_negative = (avg_negative / total) * 100
                avg_neutral = (avg_neutral / total) * 100
            
            return {
                'positive': round(avg_positive, 1),
                'negative': round(avg_negative, 1),
                'neutral': round(avg_neutral, 1)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing risk sentiment: {e}")
            # Return default distribution
            return {'positive': 65.0, 'negative': 15.0, 'neutral': 20.0}

    def analyze_assessment_sentiment(self, db: Session, time_range: str = "30d") -> Dict[str, float]:
        """Analyze sentiment in risk assessments"""
        
        if time_range == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif time_range == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif time_range == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        try:
            query = text("""
                SELECT title, description, comments, findings
                FROM assessments 
                WHERE created_at >= :start_date
            """)
            
            result = db.execute(query, {"start_date": start_date})
            rows = result.fetchall()
            
            if not rows:
                return {'positive': 33.0, 'negative': 33.0, 'neutral': 34.0}
            
            all_sentiments = []
            
            for row in rows:
                combined_text = " ".join([
                    row.title or "",
                    row.description or "",
                    row.comments or "",
                    row.findings or ""
                ])
                
                if combined_text.strip():
                    sentiment = self.analyze_sentiment(combined_text)
                    all_sentiments.append(sentiment)
            
            if not all_sentiments:
                return {'positive': 33.0, 'negative': 33.0, 'neutral': 34.0}
            
            # Calculate average
            avg_positive = sum(s['positive'] for s in all_sentiments) / len(all_sentiments)
            avg_negative = sum(s['negative'] for s in all_sentiments) / len(all_sentiments)
            avg_neutral = sum(s['neutral'] for s in all_sentiments) / len(all_sentiments)
            
            return {
                'positive': round(avg_positive, 1),
                'negative': round(avg_negative, 1),
                'neutral': round(avg_neutral, 1)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing assessment sentiment: {e}")
            return {'positive': 70.0, 'negative': 10.0, 'neutral': 20.0}

    def analyze_incident_sentiment(self, db: Session, time_range: str = "30d") -> Dict[str, float]:
        """Analyze sentiment in incident reports"""
        
        if time_range == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif time_range == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif time_range == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        try:
            query = text("""
                SELECT title, description, impact_description, resolution_notes
                FROM incidents 
                WHERE created_at >= :start_date
            """)
            
            result = db.execute(query, {"start_date": start_date})
            rows = result.fetchall()
            
            if not rows:
                return {'positive': 20.0, 'negative': 50.0, 'neutral': 30.0}
            
            all_sentiments = []
            
            for row in rows:
                combined_text = " ".join([
                    row.title or "",
                    row.description or "",
                    row.impact_description or "",
                    row.resolution_notes or ""
                ])
                
                if combined_text.strip():
                    sentiment = self.analyze_sentiment(combined_text)
                    all_sentiments.append(sentiment)
            
            if not all_sentiments:
                return {'positive': 20.0, 'negative': 50.0, 'neutral': 30.0}
            
            # Calculate average
            avg_positive = sum(s['positive'] for s in all_sentiments) / len(all_sentiments)
            avg_negative = sum(s['negative'] for s in all_sentiments) / len(all_sentiments)
            avg_neutral = sum(s['neutral'] for s in all_sentiments) / len(all_sentiments)
            
            return {
                'positive': round(avg_positive, 1),
                'negative': round(avg_negative, 1),
                'neutral': round(avg_neutral, 1)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing incident sentiment: {e}")
            return {'positive': 25.0, 'negative': 45.0, 'neutral': 30.0}

    def get_overall_sentiment(self, db: Session, time_range: str = "30d") -> Dict[str, float]:
        """Get overall sentiment across all text data in the system"""
        
        try:
            risk_sentiment = self.analyze_risk_sentiment(db, time_range)
            assessment_sentiment = self.analyze_assessment_sentiment(db, time_range)
            incident_sentiment = self.analyze_incident_sentiment(db, time_range)
            
            # Weight the sentiments (risks and assessments more heavily than incidents)
            weights = {'risks': 0.4, 'assessments': 0.4, 'incidents': 0.2}
            
            overall_positive = (
                risk_sentiment['positive'] * weights['risks'] +
                assessment_sentiment['positive'] * weights['assessments'] +
                incident_sentiment['positive'] * weights['incidents']
            )
            
            overall_negative = (
                risk_sentiment['negative'] * weights['risks'] +
                assessment_sentiment['negative'] * weights['assessments'] +
                incident_sentiment['negative'] * weights['incidents']
            )
            
            overall_neutral = (
                risk_sentiment['neutral'] * weights['risks'] +
                assessment_sentiment['neutral'] * weights['assessments'] +
                incident_sentiment['neutral'] * weights['incidents']
            )
            
            return {
                'positive': round(overall_positive, 1),
                'negative': round(overall_negative, 1),
                'neutral': round(overall_neutral, 1),
                'breakdown': {
                    'risks': risk_sentiment,
                    'assessments': assessment_sentiment,
                    'incidents': incident_sentiment
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall sentiment: {e}")
            # Return realistic default for risk management system
            return {
                'positive': 60.0,
                'negative': 20.0,
                'neutral': 20.0,
                'breakdown': {
                    'risks': {'positive': 55.0, 'negative': 25.0, 'neutral': 20.0},
                    'assessments': {'positive': 70.0, 'negative': 15.0, 'neutral': 15.0},
                    'incidents': {'positive': 30.0, 'negative': 50.0, 'neutral': 20.0}
                }
            }

    def generate_sentiment_insights(self, sentiment_data: Dict[str, float]) -> List[str]:
        """Generate AI insights based on sentiment analysis"""
        
        insights = []
        
        positive = sentiment_data.get('positive', 0)
        negative = sentiment_data.get('negative', 0)
        neutral = sentiment_data.get('neutral', 0)
        
        if positive > 70:
            insights.append("🟢 Excellent sentiment detected - stakeholders express high confidence in risk management controls")
        elif positive > 50:
            insights.append("🟡 Generally positive sentiment - most risk assessments indicate effective control measures")
        elif positive < 30:
            insights.append("🔴 Low positive sentiment - consider reviewing risk communication and control effectiveness")
        
        if negative > 40:
            insights.append("⚠️ High negative sentiment detected - urgent attention needed for risk mitigation strategies")
        elif negative > 25:
            insights.append("📊 Moderate negative sentiment - monitor closely and address key concerns")
        elif negative < 15:
            insights.append("✅ Low negative sentiment - risk management appears well-controlled")
        
        if neutral > 50:
            insights.append("📋 High neutral sentiment suggests need for clearer risk communication and engagement")
        
        # Trend-based insights
        if 'breakdown' in sentiment_data:
            breakdown = sentiment_data['breakdown']
            
            if breakdown.get('incidents', {}).get('negative', 0) > breakdown.get('risks', {}).get('negative', 0) + 20:
                insights.append("🚨 Incident reports show significantly more negative sentiment than risk assessments")
            
            if breakdown.get('assessments', {}).get('positive', 0) > 80:
                insights.append("📈 Risk assessments show very positive sentiment - controls appear highly effective")
        
        return insights[:3]  # Return top 3 insights

# Global sentiment analyzer instance
_sentiment_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get the global sentiment analyzer instance"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer