"""
Business Intelligence Tools Blueprint
Provides advanced analytics, reporting, and data visualization
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from app.services.api_service import APIService
import json
from datetime import datetime, timedelta
from functools import wraps

# Custom login_required decorator that allows mock mode
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In development, auto-create a mock session if none exists
        if 'user_id' not in session:
            session['user_id'] = 1
            session['username'] = 'admin'
            session['email'] = 'admin@napsa.co.zm'
            session['role'] = 'admin'
        return f(*args, **kwargs)
    return decorated_function

bi_tools = Blueprint('bi_tools', __name__, url_prefix='/bi-tools')

@bi_tools.route('/')
@login_required
def index():
    """BI Tools main dashboard"""
    try:
        api_service = APIService()
        
        # Get default dashboard data
        dashboard_data = api_service.get('/bi-tools/dashboard')
        
        # Get performance metrics
        metrics_data = api_service.get('/bi-tools/metrics/performance')
        
        # Get risk heatmap
        heatmap_data = api_service.get('/bi-tools/risk-heatmap')
        
        return render_template('bi_tools/index_enhanced.html',
                             dashboard_data=dashboard_data,
                             metrics_data=metrics_data,
                             heatmap_data=heatmap_data)
    
    except Exception as e:
        flash(f'Error loading BI dashboard: {str(e)}', 'error')
        return render_template('bi_tools/index_enhanced.html',
                             dashboard_data={},
                             metrics_data={},
                             heatmap_data=[])

@bi_tools.route('/analytics')
@login_required
def analytics():
    """Advanced analytics page"""
    try:
        api_service = APIService()
        
        # Get trend analysis data
        time_range = request.args.get('time_range', '90d')
        metric = request.args.get('metric', 'risks')
        period = request.args.get('period', 'weekly')
        
        trend_data = api_service.get('/bi-tools/trend-analysis', params={
            'metric': metric,
            'period': period,
            'time_range': time_range
        })
        
        return render_template('bi_tools/analytics.html',
                             trend_data=trend_data,
                             selected_metric=metric,
                             selected_period=period,
                             selected_time_range=time_range)
    
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('bi_tools/analytics.html',
                             trend_data={},
                             selected_metric='risks',
                             selected_period='weekly',
                             selected_time_range='90d')

@bi_tools.route('/reports')
@login_required
def reports():
    """Reports generation page"""
    return render_template('bi_tools/reports.html')

@bi_tools.route('/query-builder')
@login_required
def query_builder():
    """Custom query builder interface"""
    return render_template('bi_tools/query_builder.html')

@bi_tools.route('/dashboards')
@login_required
def dashboards():
    """Custom dashboards management"""
    return render_template('bi_tools/dashboards.html')

@bi_tools.route('/data-explorer')
@login_required
def data_explorer():
    """Interactive data exploration tool"""
    return render_template('bi_tools/data_explorer.html')

@bi_tools.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API endpoint for dashboard data"""
    try:
        api_service = APIService()
        time_range = request.args.get('time_range', '30d')
        department_id = request.args.get('department_id')
        
        params = {'time_range': time_range}
        if department_id:
            params['department_id'] = department_id
        
        data = api_service.get('/bi-tools/dashboard', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/trend-analysis')
@login_required
def api_trend_analysis():
    """API endpoint for trend analysis"""
    try:
        api_service = APIService()
        
        params = {
            'metric': request.args.get('metric', 'risks'),
            'period': request.args.get('period', 'weekly'),
            'time_range': request.args.get('time_range', '90d'),
            'department_id': request.args.get('department_id')
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        data = api_service.get('/bi-tools/trend-analysis', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/risk-heatmap')
@login_required
def api_risk_heatmap():
    """API endpoint for risk heatmap data"""
    try:
        api_service = APIService()
        department_id = request.args.get('department_id')
        
        params = {}
        if department_id:
            params['department_id'] = department_id
        
        data = api_service.get('/bi-tools/risk-heatmap', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/execute-query', methods=['POST'])
@login_required
def api_execute_query():
    """API endpoint for executing custom queries"""
    try:
        api_service = APIService()
        query_data = request.get_json()
        
        if not query_data or 'query' not in query_data:
            return jsonify({'error': 'Query is required'}), 400
        
        data = api_service.post('/bi-tools/custom-query', data=query_data)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/export', methods=['POST'])
@login_required
def api_export():
    """API endpoint for data export"""
    try:
        api_service = APIService()
        export_data = request.get_json()
        
        if not export_data:
            return jsonify({'error': 'Export configuration is required'}), 400
        
        data = api_service.post('/bi-tools/export', data=export_data)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/performance-metrics')
@login_required
def api_performance_metrics():
    """API endpoint for performance metrics"""
    try:
        api_service = APIService()
        
        params = {
            'time_range': request.args.get('time_range', '30d'),
            'department_id': request.args.get('department_id')
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        data = api_service.get('/bi-tools/metrics/performance', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/sentiment-analysis')
@login_required
def api_sentiment_analysis():
    """API endpoint for AI sentiment analysis"""
    try:
        api_service = APIService()
        
        params = {
            'time_range': request.args.get('time_range', '30d'),
            'category': request.args.get('category', 'overall')
        }
        
        data = api_service.get('/bi-tools/sentiment-analysis', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/ai-insights')
@login_required
def api_ai_insights():
    """API endpoint for AI-generated insights"""
    try:
        api_service = APIService()
        
        params = {
            'focus_area': request.args.get('focus_area', 'risks'),
            'time_range': request.args.get('time_range', '30d')
        }
        
        data = api_service.get('/bi-tools/ai-insights', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/sentiment')
@login_required
def sentiment_analysis():
    """AI-Powered Sentiment Analysis Dashboard"""
    try:
        api_service = APIService()
        
        # Get sentiment data
        sentiment_data = api_service.get('/bi-tools/sentiment-analysis', params={
            'time_range': request.args.get('time_range', '30d')
        })
        
        # Get monitored entities
        entities = api_service.get('/bi-tools/monitored-entities')
        
        # Get recent alerts
        alerts = api_service.get('/bi-tools/sentiment-alerts')
        
        return render_template('bi_tools/sentiment_enhanced.html',
                             sentiment_data=sentiment_data,
                             entities=entities,
                             alerts=alerts)
    
    except Exception as e:
        flash(f'Error loading sentiment analysis: {str(e)}', 'error')
        return render_template('bi_tools/sentiment_enhanced.html',
                             sentiment_data={},
                             entities=[],
                             alerts=[])

@bi_tools.route('/api/add-entity', methods=['POST'])
@login_required
def api_add_entity():
    """API endpoint to add entity for monitoring"""
    try:
        api_service = APIService()
        entity_data = request.get_json()
        
        if not entity_data or 'name' not in entity_data:
            return jsonify({'error': 'Entity name is required'}), 400
        
        # Add entity to monitoring
        result = api_service.post('/bi-tools/monitored-entities', data=entity_data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/entity-sentiment/<int:entity_id>')
@login_required
def api_entity_sentiment(entity_id):
    """API endpoint for entity-specific sentiment data"""
    try:
        api_service = APIService()
        
        params = {
            'time_range': request.args.get('time_range', '30d'),
            'entity_id': entity_id
        }
        
        data = api_service.get(f'/bi-tools/entity-sentiment/{entity_id}', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/compliance-sentiment')
@login_required
def api_compliance_sentiment():
    """API endpoint for compliance-specific sentiment analysis"""
    try:
        api_service = APIService()
        
        params = {
            'time_range': request.args.get('time_range', '30d'),
            'category': request.args.get('category', 'all')
        }
        
        data = api_service.get('/bi-tools/compliance-sentiment', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/api/news-sentiment')
@login_required
def api_news_sentiment():
    """API endpoint for news sentiment analysis"""
    try:
        api_service = APIService()
        
        params = {
            'sources': request.args.get('sources', 'all'),
            'limit': request.args.get('limit', '10')
        }
        
        data = api_service.get('/bi-tools/news-sentiment', params=params)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bi_tools.route('/help')
@login_required
def help():
    """BI Tools help and documentation"""
    return render_template('bi_tools/help.html')

# Error handlers
@bi_tools.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bi_tools.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500