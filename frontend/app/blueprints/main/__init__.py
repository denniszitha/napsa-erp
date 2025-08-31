"""
Main Blueprint for root routes
"""
from flask import Blueprint, redirect, url_for, render_template, jsonify
from app.utils.auth import is_authenticated, login_required
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Root route - redirect to appropriate page"""
    if is_authenticated():
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@main_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@main_bp.route('/test')
@login_required
def test_dashboard():
    """Test dashboard for checking all features"""
    return render_template('test_dashboard.html')

@main_bp.route('/api/risks')
@login_required
def get_risks():
    """Get all risks for dropdowns"""
    from app.services.api_service import APIService
    
    try:
        # Get risks from backend
        result = APIService.get('/risks/')
        
        if result.get('success'):
            # Get risks data - handle both 'items' and 'data' formats
            data = result.get('data', {})
            if isinstance(data, dict):
                # Backend returns data in 'data' field directly
                risks = data.get('items', data.get('data', []))
            else:
                # Data is already a list
                risks = data
                
            return jsonify({
                'success': True,
                'data': risks
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to fetch risks')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main_bp.route('/api/users')
@login_required
def get_users():
    """Get all users for dropdowns"""
    from app.services.api_service import APIService
    
    try:
        # Get users from backend
        result = APIService.get('/users/')
        
        if result.get('success'):
            # Get users data - handle both 'items' and 'data' formats
            data = result.get('data', {})
            if isinstance(data, dict):
                # Backend returns data in 'data' field directly
                users = data.get('items', data.get('data', []))
            else:
                # Data is already a list
                users = data
                
            return jsonify({
                'success': True,
                'data': users
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to fetch users')
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500