"""
Assessment Periods Blueprint - Production Version
Direct backend integration for managing assessment cycles
"""
from flask import Blueprint, render_template, jsonify, request, session
from functools import wraps
import requests
import logging
import os
import socket
from datetime import datetime, date
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
assessment_periods_bp = Blueprint(
    'assessment_periods', 
    __name__,
    template_folder='templates',
    url_prefix='/assessment-periods'
)

# Backend API configuration
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://napsa-backend:8000')
# Fallback to host network if container name doesn't resolve
try:
    socket.gethostbyname('napsa-backend')
except:
    BACKEND_URL = 'http://102.23.120.243:58001'

API_BASE = f"{BACKEND_URL}/api/v1"


def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers from cookies or session"""
    headers = {'Content-Type': 'application/json'}
    
    # First try to get token from cookies (primary source)
    token = request.cookies.get('napsa_token')
    if token:
        headers['Authorization'] = f"Bearer {token}"
    # Fallback to session if no cookie
    elif 'access_token' in session:
        headers['Authorization'] = f"Bearer {session['access_token']}"
    
    return headers


def handle_backend_error(response: requests.Response, operation: str) -> Dict:
    """Handle backend API errors properly"""
    try:
        error_detail = response.json().get('detail', 'Unknown error')
    except:
        error_detail = response.text or 'Backend communication error'
    
    logger.error(f"{operation} failed: {response.status_code} - {error_detail}")
    
    return {
        'success': False,
        'error': f"{operation} failed: {error_detail}",
        'status_code': response.status_code
    }


@assessment_periods_bp.route('/')
def index():
    """Render assessment periods page"""
    return render_template('assessment_periods/index.html')


@assessment_periods_bp.route('/api/list')
def list_periods():
    """Get all assessment periods from backend"""
    try:
        # Get query parameters
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        is_active = request.args.get('is_active')
        search = request.args.get('search')
        
        # Build query parameters
        params = {'skip': skip, 'limit': limit}
        if is_active is not None:
            params['is_active'] = is_active.lower() == 'true'
        if search:
            params['search'] = search
        
        # Call backend API
        response = requests.get(
            f"{API_BASE}/assessment-periods/",
            headers=get_auth_headers(),
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Process dates for display
            for period in data.get('data', []):
                # Format dates for better display
                if 'start_date' in period:
                    period['start_date_display'] = period['start_date']
                if 'end_date' in period:
                    period['end_date_display'] = period['end_date']
                    
            return jsonify({
                'success': True,
                'periods': data.get('data', []),
                'total': data.get('total', 0),
                'skip': data.get('skip', 0),
                'limit': data.get('limit', 100)
            })
        else:
            return jsonify(handle_backend_error(response, "Fetch periods"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error fetching periods: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessment_periods_bp.route('/api/active')
def get_active_periods():
    """Get currently active assessment periods"""
    try:
        response = requests.get(
            f"{API_BASE}/assessment-periods/active",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            periods = response.json()
            return jsonify({
                'success': True,
                'periods': periods
            })
        else:
            return jsonify(handle_backend_error(response, "Fetch active periods"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503


@assessment_periods_bp.route('/api/upcoming')
def get_upcoming_periods():
    """Get upcoming assessment periods"""
    try:
        days = request.args.get('days', 30, type=int)
        
        response = requests.get(
            f"{API_BASE}/assessment-periods/upcoming",
            headers=get_auth_headers(),
            params={'days': days},
            timeout=10
        )
        
        if response.status_code == 200:
            periods = response.json()
            return jsonify({
                'success': True,
                'periods': periods
            })
        else:
            return jsonify(handle_backend_error(response, "Fetch upcoming periods"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503


@assessment_periods_bp.route('/api/create', methods=['POST'])
def create_period():
    """Create new assessment period"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Ensure dates are in ISO format
        if 'T' not in data['start_date']:
            data['start_date'] = f"{data['start_date']}T00:00:00"
        if 'T' not in data['end_date']:
            data['end_date'] = f"{data['end_date']}T00:00:00"
        
        # Set default assessment type if not provided
        if 'assessment_type' not in data:
            data['assessment_type'] = 'Periodic Review'
        
        # Call backend API
        response = requests.post(
            f"{API_BASE}/assessment-periods/",
            headers=get_auth_headers(),
            json=data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            period_data = response.json()
            return jsonify({
                'success': True,
                'message': 'Assessment period created successfully',
                'data': period_data
            })
        else:
            return jsonify(handle_backend_error(response, "Create period"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error creating period: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessment_periods_bp.route('/api/get/<int:period_id>')
def get_period(period_id):
    """Get single assessment period by ID"""
    try:
        response = requests.get(
            f"{API_BASE}/assessment-periods/{period_id}",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Assessment period not found'
            }), 404
        else:
            return jsonify(handle_backend_error(response, "Get period"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503


@assessment_periods_bp.route('/api/update/<int:period_id>', methods=['PUT'])
def update_period(period_id):
    """Update existing assessment period"""
    try:
        data = request.json
        
        # Format dates if provided
        if 'start_date' in data and data['start_date']:
            if 'T' not in data['start_date']:
                data['start_date'] = f"{data['start_date']}T00:00:00"
        if 'end_date' in data and data['end_date']:
            if 'T' not in data['end_date']:
                data['end_date'] = f"{data['end_date']}T00:00:00"
        
        response = requests.put(
            f"{API_BASE}/assessment-periods/{period_id}",
            headers=get_auth_headers(),
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Assessment period updated successfully',
                'data': response.json()
            })
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Assessment period not found'
            }), 404
        else:
            return jsonify(handle_backend_error(response, "Update period"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503


@assessment_periods_bp.route('/api/delete/<int:period_id>', methods=['DELETE'])
def delete_period(period_id):
    """Delete assessment period"""
    try:
        response = requests.delete(
            f"{API_BASE}/assessment-periods/{period_id}",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            return jsonify({
                'success': True,
                'message': 'Assessment period deleted successfully'
            })
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Assessment period not found'
            }), 404
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Cannot delete period')
            return jsonify({
                'success': False,
                'error': error_detail
            }), 400
        else:
            return jsonify(handle_backend_error(response, "Delete period"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503


@assessment_periods_bp.route('/api/activate/<int:period_id>', methods=['POST'])
def activate_period(period_id):
    """Activate assessment period"""
    try:
        response = requests.post(
            f"{API_BASE}/assessment-periods/{period_id}/activate",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Assessment period activated successfully'
            })
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Assessment period not found'
            }), 404
        else:
            return jsonify(handle_backend_error(response, "Activate period"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503


@assessment_periods_bp.route('/api/deactivate/<int:period_id>', methods=['POST'])
def deactivate_period(period_id):
    """Deactivate assessment period"""
    try:
        response = requests.post(
            f"{API_BASE}/assessment-periods/{period_id}/deactivate",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Assessment period deactivated successfully'
            })
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Assessment period not found'
            }), 404
        else:
            return jsonify(handle_backend_error(response, "Deactivate period"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503


@assessment_periods_bp.route('/api/statistics/<int:period_id>')
def get_period_statistics(period_id):
    """Get statistics for assessment period"""
    try:
        response = requests.get(
            f"{API_BASE}/assessment-periods/{period_id}/statistics",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'statistics': response.json()
            })
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Assessment period not found'
            }), 404
        else:
            return jsonify(handle_backend_error(response, "Get statistics"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503


# Error handlers
@assessment_periods_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Resource not found'}), 404


@assessment_periods_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500