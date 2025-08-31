"""
Executive Dashboard Blueprint - C-suite level dashboards and metrics
"""
from flask import Blueprint, render_template, jsonify, request
from app.utils.auth import login_required, get_current_user
import requests
from config import Config
from datetime import datetime, timedelta

executive_dashboard_bp = Blueprint('executive_dashboard', __name__)

API_BASE_URL = Config.API_BASE_URL

@executive_dashboard_bp.route('/')
@login_required
def index():
    """Main executive dashboard"""
    return render_template('executive_dashboard/index.html')

@executive_dashboard_bp.route('/api/metrics')
@login_required
def get_metrics():
    """Get executive metrics from API"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/executive-dashboard/metrics', headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Failed to fetch metrics'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@executive_dashboard_bp.route('/api/risk-summary')
@login_required
def get_risk_summary():
    """Get risk summary for executives"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/executive-dashboard/risk-summary', headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Failed to fetch risk summary'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@executive_dashboard_bp.route('/api/compliance-status')
@login_required
def get_compliance_status():
    """Get compliance status overview"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/executive-dashboard/compliance-status', headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Failed to fetch compliance status'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@executive_dashboard_bp.route('/api/kri-alerts')
@login_required
def get_kri_alerts():
    """Get KRI alerts for executives"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/executive-dashboard/kri-alerts', headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Failed to fetch KRI alerts'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@executive_dashboard_bp.route('/api/branch-performance')
@login_required
def get_branch_performance():
    """Get branch performance metrics"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/executive-dashboard/branch-performance', headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Failed to fetch branch performance'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@executive_dashboard_bp.route('/reports')
@login_required
def reports():
    """Executive reports page"""
    return render_template('executive_dashboard/reports.html')

@executive_dashboard_bp.route('/api/generate-report/<report_type>')
@login_required
def generate_report(report_type):
    """Generate executive report"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        # Add query parameters if needed
        params = {
            'start_date': request.args.get('start_date', (datetime.now() - timedelta(days=30)).isoformat()),
            'end_date': request.args.get('end_date', datetime.now().isoformat())
        }
        
        response = requests.get(
            f'{API_BASE_URL}/executive-dashboard/reports/{report_type}',
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': f'Failed to generate {report_type} report'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500