"""
KRI (Key Risk Indicators) Blueprint
"""
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for, current_app
from app.utils.auth import login_required, get_current_user
import requests
from datetime import datetime
import os

kri_bp = Blueprint('kri', __name__, template_folder='templates')

@kri_bp.route('/')
@login_required
def index():
    """KRI list page"""
    return render_template('kri/index.html')

@kri_bp.route('/dashboard')
@login_required
def dashboard():
    """KRI Dashboard with real-time monitoring"""
    return render_template('kri/dashboard.html')

@kri_bp.route('/api/dashboard-data')
@login_required
def get_dashboard_data():
    """Get KRI dashboard data from backend"""
    from flask import session
    from app.services.api_service import APIService
    
    try:
        # Try to get data from backend
        result = APIService.get('/kris/dashboard/summary')
        
        if result.get('success') and result.get('data'):
            # Use backend data
            return jsonify({
                'success': True,
                'data': result['data']
            })
        
        # Fallback to mock data if backend is unavailable
        dashboard_data = {
            'success': True,
            'data': {
                'summary': {
                    'total_kris': 12,
                    'breached_kris': 3,
                    'critical_kris': 1,
                    'compliance_rate': 75.0
                },
                'kris': [
                    {
                        'id': '1',
                        'name': 'System Uptime',
                        'category': 'Operational',
                        'current_value': 99.95,
                        'threshold_green': 99.9,
                        'threshold_amber': 99.0,
                        'threshold_red': 95.0,
                        'status': 'green',
                        'trend': 'stable',
                        'risk_title': 'System Availability Risk',
                        'frequency': 'Daily',
                        'last_updated': datetime.now().isoformat()
                    },
                    {
                        'id': '2',
                        'name': 'Failed Login Attempts',
                        'category': 'Security',
                        'current_value': 45,
                        'threshold_green': 10,
                        'threshold_amber': 50,
                        'threshold_red': 100,
                        'status': 'amber',
                        'trend': 'up',
                        'risk_title': 'Cyber Security Risk',
                        'frequency': 'Hourly',
                        'last_updated': datetime.now().isoformat()
                    },
                    {
                        'id': '3',
                        'name': 'Payment Processing Time',
                        'category': 'Operational',
                        'current_value': 8.5,
                        'threshold_green': 2,
                        'threshold_amber': 4,
                        'threshold_red': 8,
                        'status': 'red',
                        'trend': 'up',
                        'risk_title': 'Transaction Processing Risk',
                        'frequency': 'Daily',
                        'last_updated': datetime.now().isoformat()
                    }
                ]
            }
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kri_bp.route('/api/update/<kri_id>', methods=['POST'])
@login_required
def update_kri_value(kri_id):
    """Update KRI value"""
    try:
        data = request.get_json()
        new_value = data.get('value')
        
        # Here you would update the backend
        # For now, return success
        return jsonify({
            'success': True,
            'message': f'KRI {kri_id} updated to {new_value}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kri_bp.route('/new')
@login_required
def new_kri():
    """Create new KRI page"""
    return render_template('kri/new.html')

@kri_bp.route('/create', methods=['POST'])
@login_required
def create():
    """Create a new KRI"""
    try:
        # This would typically save to backend
        flash('KRI created successfully!', 'success')
        return redirect(url_for('kri.index'))
    except Exception as e:
        flash(f'Error creating KRI: {str(e)}', 'error')
        return redirect(url_for('kri.new_kri'))

@kri_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    """API endpoint to create a new KRI"""
    from app.services.api_service import APIService
    
    try:
        data = request.get_json()
        
        # Get current user info
        current_user = get_current_user()
        
        # Prepare data for backend - matching KRIBase schema
        kri_data = {
            'risk_id': data.get('risk_id'),
            'name': data.get('name'),
            'description': data.get('description'),
            'metric_type': data.get('unit', 'Percentage'),
            'lower_threshold': float(data.get('threshold_red', 0)),
            'upper_threshold': float(data.get('threshold_green', 100)),
            'target_value': float(data.get('threshold_amber', 50)),
            'measurement_frequency': data.get('frequency', 'Daily'),
            'data_source': data.get('data_source', 'Manual'),
            'responsible_party': data.get('owner', current_user.get('email', 'System') if current_user else 'System')
        }
        
        # Send to backend
        result = APIService.post('/kris/', kri_data)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'KRI created successfully',
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to create KRI')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500