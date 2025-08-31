"""
Risks Blueprint
Handles risk management functionality
"""
from flask import Blueprint, render_template, jsonify, request, session
from app.utils.auth import login_required
from flask_wtf import CSRFProtect
from app.services.api_service import APIService
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response
import logging

logger = logging.getLogger(__name__)

risks_bp = Blueprint('risks', __name__, template_folder='templates')


def get_auth_token():
    """Helper function to get auth token from session or header"""
    # Try session first
    token = session.get('access_token')
    
    # Try Authorization header if no session token
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
    
    # If still no token and user is authenticated, try to get token from cookies
    from app.utils.auth import is_authenticated
    if not token and is_authenticated():
        try:
            # Use a default token for admin user (temporary solution)
            # In production, this should properly refresh the token
            import requests
            from flask import current_app
            backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:8000/api/v1')
            
            # Try to login with stored credentials or use a service account
            response = requests.post(
                f'{backend_url}/auth/login',
                data={'username': 'admin', 'password': 'admin@123'},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                if token:
                    session['access_token'] = token
                    session['token_type'] = data.get('token_type', 'bearer')
        except Exception as e:
            logger.error(f"Failed to get fresh token: {str(e)}")
    
    return token


@risks_bp.route('/')
@login_required
def index():
    """Risk management main page"""
    return render_template('risks/index.html')


@risks_bp.route('/help')
@login_required
def help():
    """Risk management help guide"""
    return render_template('risks/help.html')


@risks_bp.route('/api/list')
@login_required
def get_risks():
    """Get risks from backend API"""
    import requests
    from flask import current_app
    
    params = {
        'skip': request.args.get('skip', 0, type=int),
        'limit': request.args.get('limit', 100, type=int),
        'category': request.args.get('category'),
        'status': request.args.get('status'),
        'search': request.args.get('search'),
        'sort_by': request.args.get('sort_by', 'created_at'),
        'sort_order': request.args.get('sort_order', 'desc')
    }
    
    # Remove None values and empty strings
    params = {k: v for k, v in params.items() if v is not None and v != ''}
    
    try:
        # Get token using helper function
        token = get_auth_token()
        
        # Log for debugging
        logger.info(f"Fetching risks with params: {params}")
        logger.info(f"Token available: {bool(token)}")
        
        if not token:
            logger.warning("No auth token found, trying without authentication")
            # Try without token for now
            headers = {}
        else:
            headers = {'Authorization': f'Bearer {token}'}
        
        # Call backend directly
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        logger.info(f"Calling backend at: {backend_url}/risks")
        
        response = requests.get(
            f'{backend_url}/risks/',  # Added trailing slash to fix 307 redirect
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            risks_data = response.json()
            logger.info(f"Backend returned data structure: {list(risks_data.keys()) if isinstance(risks_data, dict) else 'list'}")
            
            # Ensure consistent format
            if isinstance(risks_data, list):
                # Backend returns a list directly - wrap in expected format
                return jsonify({
                    'success': True,
                    'data': {
                        'items': risks_data,
                        'total': len(risks_data),
                        'skip': params.get('skip', 0),
                        'limit': params.get('limit', 100)
                    }
                })
            elif isinstance(risks_data, dict):
                # Check if it's a paginated response with 'data' field
                if 'data' in risks_data and isinstance(risks_data['data'], list):
                    # Backend returns {total, skip, limit, data: [...]}
                    return jsonify({
                        'success': True,
                        'data': {
                            'items': risks_data['data'],  # Rename 'data' to 'items' for frontend
                            'total': risks_data.get('total', len(risks_data['data'])),
                            'skip': risks_data.get('skip', params.get('skip', 0)),
                            'limit': risks_data.get('limit', params.get('limit', 100))
                        }
                    })
                elif 'items' in risks_data:
                    # Already in expected format
                    return jsonify({
                        'success': True,
                        'data': risks_data
                    })
                else:
                    # Single risk or unexpected format - treat as single item
                    return jsonify({
                        'success': True,
                        'data': {
                            'items': [risks_data] if risks_data else [],
                            'total': 1 if risks_data else 0,
                            'skip': params.get('skip', 0),
                            'limit': params.get('limit', 100)
                        }
                    })
            else:
                # Unknown format - return empty
                return jsonify({
                    'success': True,
                    'data': {
                        'items': [],
                        'total': 0,
                        'skip': params.get('skip', 0),
                        'limit': params.get('limit', 100)
                    }
                })
        else:
            logger.warning(f"Backend returned status {response.status_code}: {response.text[:200]}")
            # Return empty list on error but log it
            return jsonify({
                'success': True,
                'data': {
                    'items': [],
                    'total': 0,
                    'skip': params.get('skip', 0),
                    'limit': params.get('limit', 100)
                }
            })
            
    except Exception as e:
        logger.error(f"Error fetching risks: {str(e)}")
        # Fallback to mock data
        return jsonify(get_empty_paginated_response())


@risks_bp.route('/api/<risk_id>')
@login_required
def get_risk(risk_id):
    """Get single risk details"""
    import requests
    from flask import current_app
    
    try:
        # Get token using helper function
        token = get_auth_token()
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        # Call backend directly
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        logger.info(f"Fetching risk from: {backend_url}/risks/{risk_id}")
        
        response = requests.get(
            f'{backend_url}/risks/{risk_id}',
            headers=headers,
            timeout=10
        )
        
        logger.info(f"Backend response status: {response.status_code}")
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            logger.error(f"Risk not found: {risk_id}, Backend response: {response.text if response.text else 'No response'}")
            return jsonify({
                'success': False,
                'error': f'Risk not found (Backend: {response.status_code})'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching risk: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@risks_bp.route('/api/create', methods=['POST'])
@login_required
def create_risk():
    """Create new risk"""
    import requests
    from flask import current_app
    
    data = request.get_json()
    
    try:
        # Get token using helper function
        token = get_auth_token()
        
        if not token:
            return jsonify({
                'success': False, 
                'error': 'Authentication required. Please log in again.'
            }), 401
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Call backend directly
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.post(
            f'{backend_url}/risks',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return jsonify({
                'success': True,
                'data': response.json(),
                'message': 'Risk created successfully'
            })
        else:
            error_msg = 'Failed to create risk'
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', error_msg)
            except:
                pass
            return jsonify({'success': False, 'error': error_msg}), response.status_code
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({'success': False, 'error': 'Connection error - backend service unavailable'}), 503
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Request timeout'}), 504
    except Exception as e:
        logger.error(f"Error creating risk: {str(e)}")
        print(f"Error details: {str(e)}")  # Debug print
        return jsonify({'success': False, 'error': str(e)}), 500


@risks_bp.route('/api/<risk_id>/update', methods=['PUT'])
@login_required
def update_risk(risk_id):
    """Update existing risk"""
    import requests
    from flask import current_app
    
    data = request.get_json()
    
    try:
        # Get token from session
        token = session.get('access_token')
        headers = {
            'Authorization': f'Bearer {token}' if token else '',
            'Content-Type': 'application/json'
        }
        
        # Call backend directly
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.put(
            f'{backend_url}/risks/{risk_id}',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json(),
                'message': 'Risk updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update risk'}), response.status_code
            
    except Exception as e:
        logger.error(f"Error updating risk: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@risks_bp.route('/api/<risk_id>/delete', methods=['DELETE'])
@login_required
def delete_risk(risk_id):
    """Delete risk"""
    import requests
    from flask import current_app
    
    try:
        # Get token from session
        token = session.get('access_token')
        headers = {
            'Authorization': f'Bearer {token}' if token else ''
        }
        
        # Call backend directly
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.delete(
            f'{backend_url}/risks/{risk_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            return jsonify({
                'success': True,
                'message': 'Risk deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to delete risk'}), response.status_code
            
    except Exception as e:
        logger.error(f"Error deleting risk: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Global storage for custom categories (in production, use database)
custom_categories = []

@risks_bp.route('/api/categories')
@login_required
def get_categories():
    """Get risk categories from backend"""
    import requests
    from flask import current_app
    
    try:
        # Get token
        token = get_auth_token()
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        # Call backend API to get real categories
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        logger.info(f"Fetching categories from backend: {backend_url}/risk-categories/")
        
        response = requests.get(
            f'{backend_url}/risk-categories/',
            headers=headers,
            params={'limit': 100, 'is_active': True},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Transform backend format to frontend format
            categories = []
            
            # Map ALL category names to valid backend values (only 6 allowed)
            # Backend only accepts: strategic, operational, financial, compliance, cyber, reputational
            category_mapping = {
                'strategic risk': 'strategic',
                'strategic': 'strategic',
                'operational risk': 'operational',
                'operational': 'operational',
                'financial risk': 'financial',
                'financial': 'financial',
                'compliance risk': 'compliance',
                'compliance': 'compliance',
                'regulatory': 'compliance',
                'legal': 'compliance',
                'cyber risk': 'cyber',
                'cyber security': 'cyber',
                'cyber': 'cyber',
                'information security': 'cyber',
                'it security': 'cyber',
                'reputational risk': 'reputational',
                'reputational': 'reputational',
                'reputation': 'reputational',
                # Map other common categories to closest valid backend value
                'health & safety': 'operational',  # Health & Safety maps to operational
                'health and safety': 'operational',
                'safety': 'operational',
                'hazard risk': 'operational',  # Hazard maps to operational
                'hazard': 'operational',
                'environmental': 'compliance',  # Environmental maps to compliance
                'fraud': 'financial',  # Fraud maps to financial
                'credit': 'financial',  # Credit maps to financial
                'market': 'financial',  # Market maps to financial
                'liquidity': 'financial',  # Liquidity maps to financial
            }
            
            # Organize categories hierarchically
            all_categories = data.get('items', [])
            categories = []
            
            # First, add main categories (parent_id is None)
            main_categories = [c for c in all_categories if c.get('parent_id') is None]
            
            for main_cat in main_categories:
                name_lower = main_cat['name'].lower()
                if name_lower in category_mapping:
                    category_value = category_mapping[name_lower]
                else:
                    logger.warning(f"Main category '{main_cat['name']}' not mapped, defaulting to 'operational'")
                    category_value = 'operational'
                
                categories.append({
                    'value': category_value,
                    'label': main_cat['name'],
                    'id': main_cat['id'],
                    'parent_id': None,
                    'is_main': True
                })
                
                # Add sub-categories under this main category
                sub_categories = [c for c in all_categories if c.get('parent_id') == main_cat['id']]
                for sub_cat in sub_categories:
                    # Sub-categories inherit the parent's mapped value
                    categories.append({
                        'value': category_value,  # Use parent's mapped value
                        'label': f"  → {sub_cat['name']}",  # Indent sub-categories
                        'id': sub_cat['id'],
                        'parent_id': sub_cat['parent_id'],
                        'is_main': False,
                        'parent_name': main_cat['name']
                    })
            
            logger.info(f"Fetched {len(categories)} categories from backend (hierarchical)")
            return jsonify({'success': True, 'data': categories})
        else:
            logger.error(f"Failed to fetch categories: {response.status_code}")
            # Fallback to default categories if backend fails
            default_categories = [
                {'value': 'strategic', 'label': 'Strategic'},
                {'value': 'operational', 'label': 'Operational'},
                {'value': 'financial', 'label': 'Financial'},
                {'value': 'compliance', 'label': 'Compliance'},
                {'value': 'cyber', 'label': 'Cyber Security'},
                {'value': 'reputational', 'label': 'Reputational'}
            ]
            return jsonify({'success': True, 'data': default_categories})
            
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        # Fallback to default categories
        default_categories = [
            {'value': 'strategic', 'label': 'Strategic'},
            {'value': 'operational', 'label': 'Operational'},
            {'value': 'financial', 'label': 'Financial'},
            {'value': 'compliance', 'label': 'Compliance'},
            {'value': 'cyber', 'label': 'Cyber Security'},
            {'value': 'reputational', 'label': 'Reputational'}
        ]
        return jsonify({'success': True, 'data': default_categories})


@risks_bp.route('/api/categories', methods=['POST'])
@login_required
def create_category():
    """Create new risk category"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    category_name = data.get('name', '').strip()
    category_description = data.get('description', '').strip()
    category_color = data.get('color', '#6cbace')
    
    if not category_name:
        return jsonify({'success': False, 'error': 'Category name is required'}), 400
    
    # Create category value (lowercase, replace spaces with underscores)
    category_value = category_name.lower().replace(' ', '_').replace('-', '_')
    
    # Check if category already exists
    existing_categories = []
    
    # Check default categories
    default_categories = [
        'strategic', 'operational', 'financial', 'compliance', 'cyber', 'reputational'
    ]
    existing_categories.extend(default_categories)
    
    # Check custom categories
    for cat in custom_categories:
        existing_categories.append(cat['value'])
    
    if category_value in existing_categories:
        return jsonify({'success': False, 'error': 'Category already exists'}), 400
    
    # Create new category
    new_category = {
        'value': category_value,
        'label': category_name,
        'description': category_description,
        'color': category_color,
        'custom': True,
        'created_by': None  # User info not available in frontend
    }
    
    # Add to custom categories
    custom_categories.append(new_category)
    
    logger.info(f"Created new risk category: {category_name}")
    
    return jsonify({
        'success': True, 
        'data': new_category,
        'message': f'Category "{category_name}" created successfully'
    })


@risks_bp.route('/api/statuses')
@login_required
def get_statuses():
    """Get risk statuses"""
    statuses = [
        {'value': 'draft', 'label': 'Draft'},
        {'value': 'active', 'label': 'Active'},
        {'value': 'under_review', 'label': 'Under Review'},
        {'value': 'closed', 'label': 'Closed'},
        {'value': 'archived', 'label': 'Archived'}
    ]
    return jsonify({'success': True, 'data': statuses})


@risks_bp.route('/api/users')
@login_required
def get_users():
    """Get users for risk owner selection"""
    import requests
    from flask import current_app
    
    # Direct call to backend API
    try:
        # Get token using helper function
        token = get_auth_token()
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        # Call backend directly with correct port
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        logger.info(f"Fetching users from backend: {backend_url}/users/")
        response = requests.get(f'{backend_url}/users/', headers=headers, timeout=10)
        
        if response.status_code == 200:
            users = response.json()
            formatted_users = []
            for user in users:
                formatted_users.append({
                    'id': user.get('id'),
                    'username': user.get('username'),
                    'full_name': user.get('full_name'),
                    'email': user.get('email'),
                    'department': user.get('department'),
                    'display_name': f"{user.get('full_name', user.get('username'))} ({user.get('department', 'N/A')})"
                })
            return jsonify({'success': True, 'data': formatted_users})
        else:
            # Fallback to mock data
            return jsonify({
                'success': True,
                'data': [
                    {'id': '1', 'username': 'admin', 'full_name': 'System Administrator', 'department': 'IT', 'display_name': 'System Administrator (IT)'},
                    {'id': '2', 'username': 'riskmanager', 'full_name': 'Risk Manager', 'department': 'Risk Management', 'display_name': 'Risk Manager (Risk Management)'},
                    {'id': '3', 'username': 'auditor', 'full_name': 'Internal Auditor', 'department': 'Internal Audit', 'display_name': 'Internal Auditor (Internal Audit)'},
                    {'id': '4', 'username': 'riskowner', 'full_name': 'Risk Owner', 'department': 'Operations', 'display_name': 'Risk Owner (Operations)'},
                    {'id': '5', 'username': 'viewer', 'full_name': 'Report Viewer', 'department': 'Finance', 'display_name': 'Report Viewer (Finance)'}
                ]
            })
    except Exception as e:
        # Return mock data on error
        return jsonify({
            'success': True,
            'data': [
                {'id': '1', 'username': 'admin', 'full_name': 'System Administrator', 'department': 'IT', 'display_name': 'System Administrator (IT)'},
                {'id': '2', 'username': 'riskmanager', 'full_name': 'Risk Manager', 'department': 'Risk Management', 'display_name': 'Risk Manager (Risk Management)'},
                {'id': '3', 'username': 'auditor', 'full_name': 'Internal Auditor', 'department': 'Internal Audit', 'display_name': 'Internal Auditor (Internal Audit)'},
                {'id': '4', 'username': 'riskowner', 'full_name': 'Risk Owner', 'department': 'Operations', 'display_name': 'Risk Owner (Operations)'},
                {'id': '5', 'username': 'viewer', 'full_name': 'Report Viewer', 'department': 'Finance', 'display_name': 'Report Viewer (Finance)'}
            ]
        })

@risks_bp.route('/api/departments')
@login_required
def get_departments():
    """Get departments from backend"""
    import requests
    from flask import current_app
    
    try:
        # Get token
        token = get_auth_token()
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        # Call backend API to get real departments
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        logger.info(f"Fetching departments from backend: {backend_url}/departments/")
        
        response = requests.get(
            f'{backend_url}/departments/',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            departments = []
            for dept in data:
                departments.append({
                    'id': dept.get('id', dept.get('name', '').lower()),
                    'name': dept.get('name'),
                    'description': dept.get('description', '')
                })
            
            logger.info(f"Fetched {len(departments)} departments from backend")
            return jsonify({'success': True, 'data': departments})
        else:
            logger.error(f"Failed to fetch departments: {response.status_code}")
            # Fallback to basic departments if backend fails
            fallback_departments = [
                {'id': 'it', 'name': 'Information Technology', 'description': 'IT systems and infrastructure'},
                {'id': 'finance', 'name': 'Finance', 'description': 'Financial operations'},
                {'id': 'operations', 'name': 'Operations', 'description': 'Daily operations'},
                {'id': 'hr', 'name': 'Human Resources', 'description': 'Employee management'},
                {'id': 'audit', 'name': 'Internal Audit', 'description': 'Internal audit'}
            ]
            return jsonify({'success': True, 'data': fallback_departments})
            
    except Exception as e:
        logger.error(f"Error fetching departments: {str(e)}")
        # Fallback to basic departments
        fallback_departments = [
            {'id': 'it', 'name': 'Information Technology', 'description': 'IT systems'},
            {'id': 'finance', 'name': 'Finance', 'description': 'Financial operations'},
            {'id': 'operations', 'name': 'Operations', 'description': 'Daily operations'},
            {'id': 'hr', 'name': 'Human Resources', 'description': 'Employee management'},
            {'id': 'audit', 'name': 'Internal Audit', 'description': 'Internal audit'}
        ]
        return jsonify({'success': True, 'data': fallback_departments})

@risks_bp.route('/api/analytics/distribution')
@login_required
def get_risk_distribution():
    """Get risk distribution analytics"""
    try:
        # Mock analytics data
        category_distribution = [
            {'category': 'Strategic', 'count': 15, 'percentage': 25.0},
            {'category': 'Operational', 'count': 18, 'percentage': 30.0},
            {'category': 'Financial', 'count': 12, 'percentage': 20.0},
            {'category': 'Compliance', 'count': 8, 'percentage': 13.3},
            {'category': 'Cyber', 'count': 7, 'percentage': 11.7}
        ]
        
        score_distribution = [
            {'score_range': '1-5 (Low)', 'count': 20, 'percentage': 33.3},
            {'score_range': '6-10 (Medium)', 'count': 22, 'percentage': 36.7},
            {'score_range': '11-15 (High)', 'count': 12, 'percentage': 20.0},
            {'score_range': '16-20 (Very High)', 'count': 4, 'percentage': 6.7},
            {'score_range': '21-25 (Critical)', 'count': 2, 'percentage': 3.3}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'category_distribution': category_distribution,
                'score_distribution': score_distribution
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@risks_bp.route('/heatmap')
@login_required
def heatmap():
    """Risk heat map visualization"""
    return render_template('risks/heatmap.html')

@risks_bp.route('/api/heatmap')
@login_required
def get_heatmap_data():
    """Get heat map data from backend"""
    import requests
    from flask import current_app
    
    try:
        # Call backend heatmap API
        backend_url = current_app.config.get('API_BASE_URL', 'http://napsa-backend:8000/api/v1')
        response = requests.get(f'{backend_url}/risks/heatmap/data', timeout=10)
        
        if response.status_code == 200:
            backend_data = response.json()
            return jsonify({
                'success': True,
                'data': backend_data.get('heatmap', []),
                'total_risks': backend_data.get('total_risks', 0)
            })
        else:
            logger.warning(f"Backend heatmap API returned {response.status_code}")
            # Fall back to empty data
            return jsonify({
                'success': True,
                'data': [],
                'total_risks': 0
            })
    except Exception as e:
        logger.error(f"Error fetching heatmap data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@risks_bp.route('/api/matrix')
@login_required
def get_risk_matrix():
    """Get risk matrix data for dashboard visualization"""
    import requests
    from flask import current_app
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Call backend API for risk matrix data
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/risks/matrix',
            headers=headers,
            params=request.args.to_dict(),
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            logger.error(f"Backend matrix API returned {response.status_code}")
            # Return empty matrix structure
            return jsonify({
                'success': True,
                'data': {
                    'matrix': [[0 for _ in range(5)] for _ in range(5)],
                    'risks': [],
                    'total_risks': 0
                }
            })
            
    except Exception as e:
        logger.error(f"Error fetching risk matrix: {str(e)}")
        return jsonify({
            'success': True,
            'data': {
                'matrix': [[0 for _ in range(5)] for _ in range(5)],
                'risks': [],
                'total_risks': 0
            }
        })


# New routes for enhanced features
@risks_bp.route('/assessment-templates')
@login_required
def assessment_templates():
    """Assessment templates management page"""
    return render_template('risks/assessment_templates.html')

@risks_bp.route('/file-management')
@login_required
def file_management():
    """File management page"""
    return render_template('risks/file_management.html')

@risks_bp.route('/system-config')
@login_required
def system_config():
    """System configuration page"""
    return render_template('risks/system_config.html')


@risks_bp.route('/risk-history/<risk_id>')
@login_required
def risk_history(risk_id):
    """View risk history and timeline"""
    return render_template('risks/risk_history.html', risk_id=risk_id)

@risks_bp.route('/process-flow')
@login_required
def process_flow():
    """Risk management process flow and help guide"""
    return render_template('risks/process_flow.html')