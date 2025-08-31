from flask import Blueprint, render_template, request, jsonify, session, current_app
from app.utils.auth import login_required
import requests
import logging

logger = logging.getLogger(__name__)

risk_categories_bp = Blueprint('risk_categories', __name__, url_prefix='/risk-categories')

def get_auth_token():
    """Get authentication token from cookies or session"""
    # First try to get from cookies (primary source)
    token = request.cookies.get('napsa_token')
    if token:
        return token
    # Fallback to session
    return session.get('access_token')

@risk_categories_bp.route('/')
@login_required
def index():
    """Risk Categories management page"""
    return render_template('risk_categories/index.html')

@risk_categories_bp.route('/api/list', methods=['GET'])
@login_required
def get_categories():
    """Get all risk categories from backend API"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        token = get_auth_token()
        
        logger.info(f"Risk categories API - Token available: {bool(token)}, Backend URL: {backend_url}")
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            logger.info(f"Using token for authentication: {token[:20]}...")
        
        # Get query parameters
        skip = request.args.get('skip', 0)
        limit = request.args.get('limit', 100)
        search = request.args.get('search')
        parent_id = request.args.get('parent_id')
        is_active = request.args.get('is_active')
        
        params = {
            'skip': skip,
            'limit': limit
        }
        if search:
            params['search'] = search
        if parent_id:
            params['parent_id'] = parent_id
        if is_active is not None:
            params['is_active'] = is_active.lower() == 'true'
        
        logger.info(f"Calling backend: {backend_url}/risk-categories/ with params: {params}")
        
        response = requests.get(
            f'{backend_url}/risk-categories/',
            headers=headers,
            params=params,
            timeout=10
        )
        
        logger.info(f"Backend response status: {response.status_code}")
        
        if response.status_code == 200:
            backend_data = response.json()
            logger.info(f"Backend returned {backend_data.get('total', 0)} categories")
            return jsonify({
                'success': True,
                'data': {
                    'items': backend_data.get('items', []),
                    'total': backend_data.get('total', 0)
                }
            })
        elif response.status_code == 401:
            logger.error("Authentication failed - user needs to login again")
            return jsonify({
                'success': False,
                'error': 'Authentication required. Please login again.',
                'require_login': True
            }), 401
        else:
            logger.error(f"Backend API error: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': f'Backend error: {response.status_code}. Please try again.'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@risk_categories_bp.route('/api/tree', methods=['GET'])
@login_required
def get_category_tree():
    """Get categories in tree structure from backend API"""
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        token = get_auth_token()
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Get query parameters
        is_active = request.args.get('is_active')
        params = {}
        if is_active is not None:
            params['is_active'] = is_active.lower() == 'true'
        
        response = requests.get(
            f'{backend_url}/risk-categories/tree',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            backend_data = response.json()
            return jsonify({
                'success': True,
                'data': backend_data
            })
        else:
            logger.error(f"Backend API error: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': 'Failed to fetch category tree from backend'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching category tree: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@risk_categories_bp.route('/api/<int:category_id>', methods=['GET'])
@login_required
def get_category(category_id):
    """Get a specific category"""
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        token = get_auth_token()
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.get(
            f'{backend_url}/risk-categories/{category_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Category not found'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching category: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@risk_categories_bp.route('/api/create', methods=['POST'])
@login_required
def create_category():
    """Create a new category"""
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        token = get_auth_token()
        
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        data = request.json
        
        response = requests.post(
            f'{backend_url}/risk-categories/',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            return jsonify({
                'success': True,
                'message': 'Category created successfully',
                'data': response.json()
            })
        else:
            error_msg = response.json().get('detail', 'Failed to create category')
            return jsonify({
                'success': False,
                'error': error_msg
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@risk_categories_bp.route('/api/<int:category_id>/update', methods=['PUT'])
@login_required
def update_category(category_id):
    """Update an existing category"""
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        token = get_auth_token()
        
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        data = request.json
        
        response = requests.put(
            f'{backend_url}/risk-categories/{category_id}',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Category updated successfully',
                'data': response.json()
            })
        else:
            error_msg = response.json().get('detail', 'Failed to update category')
            return jsonify({
                'success': False,
                'error': error_msg
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error updating category: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@risk_categories_bp.route('/api/<int:category_id>/delete', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """Delete a category"""
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        token = get_auth_token()
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Check if force delete is requested
        force = request.args.get('force', 'false').lower() == 'true'
        params = {'force': force}
        
        response = requests.delete(
            f'{backend_url}/risk-categories/{category_id}',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 204:
            return jsonify({
                'success': True,
                'message': 'Category deleted successfully'
            })
        else:
            error_msg = response.json().get('detail', 'Failed to delete category')
            return jsonify({
                'success': False,
                'error': error_msg
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error deleting category: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@risk_categories_bp.route('/api/<int:category_id>/toggle-status', methods=['POST'])
@login_required
def toggle_category_status(category_id):
    """Toggle category active status"""
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        token = get_auth_token()
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # First get the category to check current status
        response = requests.get(
            f'{backend_url}/risk-categories/{category_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        category = response.json()
        is_active = category.get('is_active', True)
        
        # Toggle the status
        action = 'deactivate' if is_active else 'activate'
        response = requests.post(
            f'{backend_url}/risk-categories/{category_id}/{action}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'Category {"deactivated" if is_active else "activated"} successfully',
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to {action} category'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error toggling category status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@risk_categories_bp.route('/api/<int:category_id>/risks', methods=['GET'])
@login_required
def get_category_risks(category_id):
    """Get risks for a specific category"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        token = get_auth_token()
        
        logger.info(f"Getting risks for category {category_id}, Token available: {bool(token)}")
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            logger.info(f"Using token: {token[:20]}...")
        
        params = {
            'include_children': request.args.get('include_children', 'false').lower() == 'true',
            'skip': request.args.get('skip', 0),
            'limit': request.args.get('limit', 100)
        }
        
        response = requests.get(
            f'{backend_url}/risk-categories/{category_id}/risks',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch category risks'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching category risks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500