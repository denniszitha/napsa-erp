"""
Controls Management Blueprint
Handles control functionality including CRUD operations, testing, and risk mapping
"""
from flask import Blueprint, render_template, jsonify, request
from app.utils.auth import login_required
from app.services.api_service import APIService
import logging

logger = logging.getLogger(__name__)

controls_bp = Blueprint('controls', __name__, template_folder='templates')


@controls_bp.route('/')
@login_required
def index():
    """Controls management main page"""
    return render_template('controls/index.html')


@controls_bp.route('/api/list')
@login_required
def get_controls():
    """Get controls from backend API"""
    import requests
    from flask import current_app, session
    
    params = {
        'skip': request.args.get('skip', 0, type=int),
        'limit': request.args.get('limit', 100, type=int),
        'category': request.args.get('category'),
        'status': request.args.get('status'),
        'type': request.args.get('type'),
        'search': request.args.get('search'),
        'sort_by': request.args.get('sort_by', 'name'),
        'sort_order': request.args.get('sort_order', 'asc')
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {}
        
        # Only add Authorization header if we have a valid token
        # Backend may not require authentication for some endpoints
        if token and len(token) > 10:  # Basic validation
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.info("No valid auth token, proceeding without Authorization header")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/controls/',
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Format response for frontend
            if isinstance(data, dict) and 'data' in data:
                return jsonify({
                    'success': True,
                    'data': {
                        'items': data['data'],
                        'total': data.get('total', len(data['data'])),
                        'skip': data.get('skip', params.get('skip', 0)),
                        'limit': data.get('limit', params.get('limit', 100))
                    }
                })
            else:
                # Return empty data if backend response format is unexpected
                return jsonify({
                    'success': True,
                    'data': {'items': [], 'total': 0, 'skip': 0, 'limit': 100}
                })
        else:
            logger.error(f"Failed to fetch controls: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': 'Failed to fetch controls from backend',
                'data': {'items': [], 'total': 0, 'skip': 0, 'limit': 100}
            })
            
    except Exception as e:
        logger.error(f"Exception fetching controls: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch controls',
            'data': {'items': [], 'total': 0, 'skip': 0, 'limit': 100}
        })


@controls_bp.route('/api/<control_id>')
@login_required
def get_control(control_id):
    """Get single control details"""
    import requests
    from flask import current_app, session
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {}
        
        # Only add Authorization header if we have a valid token
        # Backend may not require authentication for some endpoints
        if token and len(token) > 10:  # Basic validation
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.info("No valid auth token, proceeding without Authorization header")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/controls/{control_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            control_data = response.json()
            return jsonify({
                'success': True,
                'data': control_data
            })
        else:
            logger.error(f"Failed to fetch control {control_id}: {response.status_code}")
            return jsonify({
                'success': False,
                'error': 'Control not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Exception fetching control {control_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch control'
        }), 500


@controls_bp.route('/api/create', methods=['POST'])
@login_required
def create_control():
    """Create new control"""
    import requests
    from flask import current_app, session
    
    data = request.get_json()
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        
        # Debug logging
        logger.info(f"Create control request from {request.remote_addr}")
        logger.info(f"Cookies available: {list(request.cookies.keys())}")
        logger.info(f"Session keys: {list(session.keys())}")
        logger.info(f"Token found: {bool(token)}, Length: {len(token) if token else 0}")
        
        if not token:
            logger.error("No authentication token found in cookies or session")
            logger.error(f"Available cookies: {list(request.cookies.keys())}")
            logger.error(f"Session data: {list(session.keys())}")
            return jsonify({
                'success': False,
                'error': 'Not authenticated - please login again'
            }), 401
        
        headers = {'Content-Type': 'application/json'}
        headers['Authorization'] = f'Bearer {token}'
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        logger.info(f"Creating control with data: {data}")
        logger.info(f"Using backend URL: {backend_url}/controls")
        logger.info(f"Token present: {bool(token)}, Token prefix: {token[:20] if token else 'None'}...")
        
        response = requests.post(
            f'{backend_url}/controls/',
            json=data,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"Backend response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            control_data = response.json()
            return jsonify({
                'success': True,
                'data': control_data,
                'message': 'Control created successfully'
            })
        elif response.status_code == 401:
            logger.error("Backend returned 401 Unauthorized")
            return jsonify({
                'success': False,
                'error': 'Not authenticated - please login again'
            }), 401
        else:
            # Try to get error message
            error_msg = f'Failed to create control (Status: {response.status_code})'
            try:
                error_data = response.json()
                logger.error(f"Backend error response: {error_data}")
                if 'detail' in error_data:
                    error_msg = str(error_data['detail'])
                elif 'message' in error_data:
                    error_msg = str(error_data['message'])
            except Exception as e:
                logger.error(f"Could not parse error response: {e}")
                error_msg = f'Backend error: {response.text[:200] if response.text else "Unknown error"}'
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), response.status_code if response.status_code < 500 else 400
            
    except Exception as e:
        logger.error(f"Exception creating control: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create control'
        }), 500


@controls_bp.route('/api/<control_id>/update', methods=['PUT'])
@login_required
def update_control(control_id):
    """Update existing control"""
    import requests
    from flask import current_app, session
    
    data = request.get_json()
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.warning("No auth token found for request")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.put(
            f'{backend_url}/controls/{control_id}',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            control_data = response.json()
            return jsonify({
                'success': True,
                'data': control_data,
                'message': 'Control updated successfully'
            })
        else:
            # Try to get error message
            error_msg = 'Failed to update control'
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    error_msg = str(error_data['detail'])
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
            
    except Exception as e:
        logger.error(f"Exception updating control {control_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update control'
        }), 500


@controls_bp.route('/api/<control_id>/delete', methods=['DELETE'])
@login_required
def delete_control(control_id):
    """Delete control"""
    import requests
    from flask import current_app, session
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {}
        
        # Only add Authorization header if we have a valid token
        # Backend may not require authentication for some endpoints
        if token and len(token) > 10:  # Basic validation
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.info("No valid auth token, proceeding without Authorization header")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.delete(
            f'{backend_url}/controls/{control_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            return jsonify({
                'success': True,
                'message': 'Control deleted successfully'
            })
        else:
            logger.error(f"Failed to delete control {control_id}: {response.status_code}")
            return jsonify({
                'success': False,
                'error': 'Failed to delete control'
            }), 400
            
    except Exception as e:
        logger.error(f"Exception deleting control {control_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete control'
        }), 500


@controls_bp.route('/api/<control_id>/test', methods=['POST'])
@login_required
def test_control(control_id):
    """Test control effectiveness"""
    import requests
    from flask import current_app, session
    
    data = request.get_json()
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.warning("No auth token found for request")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.post(
            f'{backend_url}/controls/{control_id}/test',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            test_result = response.json()
            return jsonify({
                'success': True,
                'data': test_result,
                'message': 'Control test completed successfully'
            })
        else:
            logger.error(f"Failed to test control {control_id}: {response.status_code}")
            return jsonify({
                'success': False,
                'error': 'Failed to test control'
            }), 400
            
    except Exception as e:
        logger.error(f"Exception testing control {control_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to test control'
        }), 500


@controls_bp.route('/api/effectiveness')
@login_required
def get_control_effectiveness():
    """Get control effectiveness summary"""
    import requests
    from flask import current_app, session
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {}
        
        # Only add Authorization header if we have a valid token
        # Backend may not require authentication for some endpoints
        if token and len(token) > 10:  # Basic validation
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.info("No valid auth token, proceeding without Authorization header")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/controls/effectiveness',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            effectiveness_data = response.json()
            return jsonify({
                'success': True,
                'data': effectiveness_data
            })
        else:
            logger.error(f"Failed to fetch control effectiveness: {response.status_code}")
            # Backend has a bug - calculate locally from controls list
            try:
                controls_response = requests.get(
                    f'{backend_url}/controls/',
                    headers=headers,
                    timeout=10
                )
                
                if controls_response.status_code == 200:
                    controls = controls_response.json()
                    
                    # Calculate effectiveness summary
                    effectiveness_data = {
                        'effective': len([c for c in controls if c.get('status') == 'effective']),
                        'partially_effective': len([c for c in controls if c.get('status') == 'partially_effective']),
                        'ineffective': len([c for c in controls if c.get('status') == 'ineffective']),
                        'not_tested': len([c for c in controls if c.get('status') == 'not_tested']),
                        'total': len(controls),
                        'average_effectiveness': 0
                    }
                    
                    # Calculate average effectiveness
                    rated_controls = [c for c in controls if c.get('effectiveness_rating') is not None]
                    if rated_controls:
                        total_rating = sum(c.get('effectiveness_rating', 0) for c in rated_controls)
                        effectiveness_data['average_effectiveness'] = round(total_rating / len(rated_controls), 1)
                    
                    return jsonify({
                        'success': True,
                        'data': effectiveness_data
                    })
            except Exception as e:
                logger.error(f"Error calculating effectiveness locally: {e}")
            
            # Return default empty data structure
            return jsonify({
                'success': True,
                'data': {
                    'effective': 0,
                    'partially_effective': 0,
                    'ineffective': 0,
                    'not_tested': 0,
                    'total': 0,
                    'average_effectiveness': 0
                }
            })
            
    except Exception as e:
        logger.error(f"Exception fetching control effectiveness: {e}")
        return jsonify({
            'success': True,
            'data': {
                'effective': 0,
                'partially_effective': 0,
                'ineffective': 0,
                'not_tested': 0,
                'total': 0
            }
        })


@controls_bp.route('/api/map-to-risk', methods=['POST'])
@login_required
def map_control_to_risk():
    """Map control to risk"""
    import requests
    from flask import current_app, session
    
    data = request.get_json()
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.warning("No auth token found for request")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.post(
            f'{backend_url}/controls/map-to-risk',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return jsonify({
                'success': True,
                'data': result,
                'message': result.get('message', 'Control mapped to risk successfully')
            })
        else:
            logger.error(f"Failed to map control to risk: {response.status_code}")
            return jsonify({
                'success': False,
                'error': 'Failed to map control to risk'
            }), 400
            
    except Exception as e:
        logger.error(f"Exception mapping control to risk: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to map control to risk'
        }), 500


@controls_bp.route('/api/risk/<risk_id>')
@login_required
def get_controls_for_risk(risk_id):
    """Get controls mapped to a specific risk"""
    import requests
    from flask import current_app, session
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {}
        
        # Only add Authorization header if we have a valid token
        # Backend may not require authentication for some endpoints
        if token and len(token) > 10:  # Basic validation
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.info("No valid auth token, proceeding without Authorization header")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/controls/risk/{risk_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            controls = response.json()
            return jsonify({
                'success': True,
                'data': controls
            })
        else:
            # Return empty list on error
            return jsonify({
                'success': True,
                'data': []
            })
            
    except Exception as e:
        # Return empty list on exception
        return jsonify({
            'success': True,
            'data': []
        })

@controls_bp.route('/api/unmap-from-risk', methods=['DELETE', 'POST'])
@login_required
def unmap_control_from_risk():
    """Remove control-risk mapping"""
    import requests
    from flask import current_app, session
    
    data = request.get_json()
    
    try:
        # Get auth token - try cookies first, then session
        token = request.cookies.get('napsa_token') or session.get('access_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.warning("No auth token found for request")
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.delete(
            f'{backend_url}/controls/unmap-from-risk',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201, 204]:
            if response.status_code == 204:
                return jsonify({
                    'success': True,
                    'message': 'Control unmapped from risk successfully'
                })
            else:
                result = response.json()
                return jsonify({
                    'success': True,
                    'data': result,
                    'message': result.get('message', 'Control unmapped from risk successfully')
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to unmap control from risk'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@controls_bp.route('/api/control-types')
@login_required
def get_control_types():
    """Get available control types"""
    control_types = [
        {'value': 'preventive', 'label': 'Preventive', 'description': 'Prevents risks from occurring'},
        {'value': 'detective', 'label': 'Detective', 'description': 'Detects when risks occur'},
        {'value': 'corrective', 'label': 'Corrective', 'description': 'Corrects issues after occurrence'},
        {'value': 'compensating', 'label': 'Compensating', 'description': 'Alternative controls when primary fails'}
    ]
    return jsonify({'success': True, 'data': control_types})


@controls_bp.route('/api/categories')
@login_required
def get_control_categories():
    """Get available control categories"""
    categories = [
        'IT Security', 'Finance', 'Data Management', 'Investment Management',
        'Fraud Prevention', 'Compliance', 'Operations', 'Risk Management',
        'Human Resources', 'Vendor Management', 'Business Continuity'
    ]
    return jsonify({'success': True, 'data': categories})


@controls_bp.route('/api/testing-frequencies')
@login_required
def get_testing_frequencies():
    """Get available testing frequencies"""
    frequencies = [
        {'value': 'Monthly', 'label': 'Monthly'},
        {'value': 'Quarterly', 'label': 'Quarterly'},
        {'value': 'Semi-Annual', 'label': 'Semi-Annual'},
        {'value': 'Annual', 'label': 'Annual'},
        {'value': 'Ad-hoc', 'label': 'Ad-hoc'}
    ]
    return jsonify({'success': True, 'data': frequencies})
