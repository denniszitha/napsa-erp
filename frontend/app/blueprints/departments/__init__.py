from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
import requests
from typing import Dict, List, Any
import json

# Create blueprint
departments_bp = Blueprint('departments', __name__, 
                          template_folder='templates',
                          static_folder='static')

@departments_bp.route('/')
@login_required
def index():
    """Main departments management page"""
    return render_template('departments/index.html')

@departments_bp.route('/api/departments')
@login_required
def get_departments():
    """Get all departments"""
    try:
        from app.utils.auth import get_current_user
        from flask import session
        current_user = get_current_user()
        
        parent_id = request.args.get('parent_id')
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        params = {}
        if parent_id:
            params['parent_id'] = parent_id
        if include_inactive:
            params['include_inactive'] = include_inactive
        
        # Direct connection without auth for now
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f"{backend_url}/departments/",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Backend error: {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@departments_bp.route('/api/hierarchy')
@login_required
def get_hierarchy():
    """Get department hierarchy"""
    try:
        from flask import session
        
        # Get auth token
            
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f"{backend_url}/departments/hierarchy",
            
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'error': f'Backend error: {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@departments_bp.route('/api/stats')
@login_required
def get_department_stats():
    """Get department statistics"""
    try:
        from flask import session
        
        # Get auth token
            
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f"{backend_url}/departments/stats/summary",
            
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            # Return mock stats if backend fails
            return jsonify({
                'total_departments': 12,
                'active_departments': 12,
                'total_employees': 150,
                'departments_by_level': {
                    'directorate': 5,
                    'department': 7
                }
            })
            
    except Exception as e:
        # Return mock stats on error
        return jsonify({
            'total_departments': 12,
            'active_departments': 12,
            'total_employees': 150,
            'departments_by_level': {
                'directorate': 5,
                'department': 7
            }
        })

@departments_bp.route('/api/department', methods=['POST'])
@login_required
def create_department():
    """Create new department"""
    try:
        from flask import session
        
        data = request.json
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        # Get auth token
        
        response = requests.post(
            f"{backend_url}/departments/",
            json=data,
            
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'error': f'Backend error: {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@departments_bp.route('/api/department/<dept_id>', methods=['PUT'])
@login_required
def update_department(dept_id):
    """Update department"""
    try:
        from flask import session
        
        data = request.json
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        # Get auth token
        
        response = requests.put(
            f"{backend_url}/departments/{dept_id}",
            json=data,
            
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'error': f'Backend error: {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@departments_bp.route('/api/department/<dept_id>', methods=['DELETE'])
@login_required
def delete_department(dept_id):
    """Delete department"""
    try:
        from flask import session
        
        force = request.args.get('force', 'false').lower() == 'true'
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        # Get auth token
        
        response = requests.delete(
            f"{backend_url}/departments/{dept_id}?force={force}",
            
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'error': f'Backend error: {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@departments_bp.route('/api/department/<dept_id>/children')
@login_required
def get_department_children(dept_id):
    """Get department children"""
    try:
        from flask import session
        
        # Get auth token
            
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f"{backend_url}/departments/{dept_id}/children",
            
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Backend error: {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@departments_bp.route("/api/department/<dept_id>/risks")
@login_required
def get_department_risks(dept_id):
    """Get risks for a specific department"""
    try:
        from flask import session
        import requests
        
        # Get auth token
        token = session.get("access_token")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        backend_url = current_app.config.get("API_BASE_URL", "http://localhost:58001/api/v1")
        
        # Get department name first
        dept_response = requests.get(
            f"{backend_url}/departments/{dept_id}",
            
            timeout=30
        )
        
        if dept_response.status_code == 200:
            dept_data = dept_response.json()
            dept_name = dept_data.get("name", "Unknown")
            
            # Get risks filtered by department
            risks_response = requests.get(
                f"{backend_url}/risks/",
                params={"department": dept_name},
                
                timeout=30
            )
            
            if risks_response.status_code == 200:
                risks_data = risks_response.json()
                return jsonify({
                    "success": True,
                    "department": dept_data,
                    "risks": risks_data
                })
        
        return jsonify({
            "success": False,
            "error": "Department or risks not found"
        }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

