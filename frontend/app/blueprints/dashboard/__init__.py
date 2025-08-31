"""
Dashboard Blueprint
"""
from flask import Blueprint, render_template, jsonify
from app.utils.auth import login_required, get_current_user
from app.services.api_service import APIService
from app.utils.decorators import cache_response
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    import requests
    from flask import current_app, session
    
    # Try to fetch dashboard stats from backend
    try:
        # Get token from cookies instead of session
        from app.utils.auth import get_auth_token
        token = get_auth_token()
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        response = requests.get(
            f'{backend_url}/dashboard/stats',
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            backend_data = response.json()
            stats = backend_data.get('data', {})
            
            # Calculate medium and low risks from total
            total_risks = stats.get('total_risks', 0)
            high_risks = stats.get('high_risk_count', 0)
            risk_by_status = stats.get('risk_by_status', {})
            
            # Estimate medium and low (can be refined with actual data)
            medium_risks = max(0, total_risks - high_risks) // 2
            low_risks = max(0, total_risks - high_risks - medium_risks)
            
            # Map backend data to expected template structure
            data = {
                'risk_summary': {
                    'total': total_risks,
                    'high': high_risks,
                    'medium': medium_risks,
                    'low': low_risks
                },
                'compliance_score': 85,  # Mock for now - would need compliance module
                'open_incidents': stats.get('open_incidents', 0),
                'pending_assessments': stats.get('total_assessments', 0),
                'kri_breaches': stats.get('kri_breaches', 0),
                'total_controls': stats.get('total_controls', 0),
                'aml_alerts': stats.get('aml_alerts', 0),
                'suspicious_transactions': stats.get('suspicious_transactions', 0),
                'risk_by_category': stats.get('risk_by_category', {}),
                'risk_by_status': risk_by_status,
                'new_risks_week': stats.get('new_risks_week', 0),
                'recent_activities': []
            }
        else:
            # Fallback to API service
            dashboard_response = APIService.get('/dashboard/overview')
            if dashboard_response.get('success'):
                data = dashboard_response.get('data', {})
            else:
                data = {}
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        data = {}
    
    # Default data structure
    default_data = {
        'risk_summary': {'total': 0, 'high': 0, 'medium': 0, 'low': 0},
        'compliance_score': 0,
        'open_incidents': 0,
        'pending_assessments': 0,
        'recent_activities': []
    }
    
    # Ensure all required keys exist
    for key in default_data:
        if key not in data:
            data[key] = default_data[key]
    
    return render_template('dashboard/index.html', data=data)


@dashboard_bp.route('/api/stats')
@login_required
def get_stats():
    """Get dashboard statistics directly from backend"""
    import requests
    from flask import current_app, session
    
    try:
        token = session.get('access_token')
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        response = requests.get(
            f'{backend_url}/dashboard/stats',
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            # Fallback with mock data
            return jsonify({
                'success': False,
                'data': {
                    'total_risks': 0,
                    'high_risk_count': 0,
                    'open_incidents': 0,
                    'kri_breaches': 0
                }
            })
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'success': False,
            'data': {
                'total_risks': 0,
                'high_risk_count': 0,
                'open_incidents': 0,
                'kri_breaches': 0
            }
        })


@dashboard_bp.route('/api/risk-matrix')
@login_required
@cache_response(timeout=300)
def get_risk_matrix():
    """Get risk matrix data"""
    matrix_data = APIService.get('/dashboard/risk-matrix')
    return jsonify(matrix_data)


@dashboard_bp.route('/api/recent-activities')
@login_required
def get_recent_activities():
    """Get recent activities"""
    activities = APIService.get('/dashboard/recent-activities', params={'limit': 10})
    return jsonify(activities)


@dashboard_bp.route('/api/charts/risk-trend')
@login_required
@cache_response(timeout=300)
def get_risk_trend():
    """Get risk trend data for charts"""
    trend_data = APIService.get('/analytics/trends')
    return jsonify(trend_data)


@dashboard_bp.route('/api/charts/compliance-status')
@login_required
@cache_response(timeout=300)
def get_compliance_status():
    """Get compliance status data"""
    compliance_data = APIService.get('/analytics/compliance-metrics')
    return jsonify(compliance_data)