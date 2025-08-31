"""
Risk Treatment Management Blueprint
Handles treatment strategies, planning, and monitoring
"""
from flask import Blueprint, render_template, jsonify, request
from app.utils.auth import login_required
from app.services.api_service import APIService
import logging

logger = logging.getLogger(__name__)

treatments_bp = Blueprint('treatments', __name__, template_folder='templates')


@treatments_bp.route('/')
@login_required
def index():
    """Risk treatments management main page"""
    return render_template('treatments/index.html')


@treatments_bp.route('/api/list')
@login_required
def get_treatments():
    """Get treatments from backend API"""
    import requests
    from flask import current_app
    
    params = {
        'skip': request.args.get('skip', 0, type=int),
        'limit': request.args.get('limit', 100, type=int),
        'risk_id': request.args.get('risk_id'),
        'strategy': request.args.get('strategy'),
        'status': request.args.get('status'),
        'owner': request.args.get('owner'),
        'search': request.args.get('search'),
        'sort_by': request.args.get('sort_by', 'created_at'),
        'sort_order': request.args.get('sort_order', 'desc')
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/treatments',
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle paginated response from backend
            if isinstance(data, dict) and 'data' in data:
                items = data.get('data', [])
                return jsonify({
                    'success': True,
                    'data': {
                        'items': items,
                        'total': data.get('total', len(items)),
                        'skip': data.get('skip', params.get('skip', 0)),
                        'limit': data.get('limit', params.get('limit', 100))
                    }
                })
            elif isinstance(data, list):
                return jsonify({
                    'success': True,
                    'data': {
                        'items': data,
                        'total': len(data),
                        'skip': params.get('skip', 0),
                        'limit': params.get('limit', 100)
                    }
                })
            else:
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
            logger.error(f"Backend returned {response.status_code} for treatments list")
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
        logger.error(f"Error fetching treatments: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch treatments: {str(e)}',
            'data': {
                'items': [],
                'total': 0,
                'skip': params.get('skip', 0),
                'limit': params.get('limit', 100)
            }
        })


@treatments_bp.route('/api/<treatment_id>')
@login_required
def get_treatment(treatment_id):
    """Get single treatment details"""
    import requests
    from flask import current_app
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/treatments/{treatment_id}',
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
                'error': f'Treatment not found or backend error: {response.status_code}'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching treatment: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error fetching treatment: {str(e)}'
        }), 500


@treatments_bp.route('/api/create', methods=['POST'])
@login_required
def create_treatment():
    """Create new treatment plan"""
    import requests
    from flask import current_app
    
    data = request.get_json()
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.post(
            f'{backend_url}/treatments/',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return jsonify({
                'success': True,
                'data': response.json(),
                'message': 'Treatment created successfully'
            })
        else:
            error_msg = 'Failed to create treatment'
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', error_msg)
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': error_msg
            }), response.status_code
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to backend: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error creating treatment: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@treatments_bp.route('/api/<treatment_id>/update', methods=['PUT'])
@login_required
def update_treatment(treatment_id):
    """Update existing treatment"""
    import requests
    from flask import current_app
    
    data = request.get_json()
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.put(
            f'{backend_url}/treatments/{treatment_id}',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json(),
                'message': 'Treatment updated successfully'
            })
        else:
            error_msg = 'Failed to update treatment'
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', error_msg)
            except:
                pass
            return jsonify({
                'success': False,
                'error': error_msg
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error updating treatment: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error updating treatment: {str(e)}'
        }), 500


@treatments_bp.route('/api/<treatment_id>/delete', methods=['DELETE'])
@login_required
def delete_treatment(treatment_id):
    """Delete treatment"""
    import requests
    from flask import current_app
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.delete(
            f'{backend_url}/treatments/{treatment_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            return jsonify({
                'success': True,
                'message': 'Treatment deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to delete treatment: {response.status_code}'
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error deleting treatment: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error deleting treatment: {str(e)}'
        }), 500


@treatments_bp.route('/api/statistics')
@login_required
def get_treatment_statistics():
    """Get treatment statistics for dashboard"""
    import requests
    from flask import current_app
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/treatments',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            treatments_list = data.get('data', []) if isinstance(data, dict) else data
            
            # Calculate statistics
            stats = {
                'total': len(treatments_list),
                'by_strategy': {
                    'accept': 0,
                    'mitigate': 0,
                    'transfer': 0,
                    'avoid': 0
                },
                'by_status': {
                    'draft': 0,
                    'pending_approval': 0,
                    'approved': 0,
                    'implemented': 0,
                    'monitoring': 0
                }
            }
            
            for treatment in treatments_list:
                strategy = treatment.get('strategy', '').lower()
                if strategy in stats['by_strategy']:
                    stats['by_strategy'][strategy] += 1
                
                status = treatment.get('status', '').lower()
                if status in stats['by_status']:
                    stats['by_status'][status] += 1
            
            return jsonify({
                'success': True,
                'data': stats
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'total': 0,
                    'by_strategy': {'accept': 0, 'mitigate': 0, 'transfer': 0, 'avoid': 0},
                    'by_status': {'draft': 0, 'pending_approval': 0, 'approved': 0, 'implemented': 0, 'monitoring': 0}
                }
            })
            
    except Exception as e:
        logger.error(f"Error fetching treatment statistics: {str(e)}")
        return jsonify({
            'success': True,
            'data': {
                'total': 0,
                'by_strategy': {'accept': 0, 'mitigate': 0, 'transfer': 0, 'avoid': 0},
                'by_status': {'draft': 0, 'pending_approval': 0, 'approved': 0, 'implemented': 0, 'monitoring': 0}
            }
        })


@treatments_bp.route('/api/<treatment_id>/approve', methods=['POST'])
@login_required
def approve_treatment(treatment_id):
    """Approve treatment plan"""
    import requests
    from flask import current_app
    
    data = request.get_json()
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.post(
            f'{backend_url}/treatments/{treatment_id}/approve',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return jsonify({
                'success': True,
                'data': response.json(),
                'message': 'Treatment approved successfully'
            })
        else:
            logger.error(f"Failed to approve treatment {treatment_id}: {response.status_code}")
            return jsonify({
                'success': False,
                'error': 'Failed to approve treatment'
            }), 400
            
    except Exception as e:
        logger.error(f"Exception approving treatment {treatment_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to approve treatment'
        }), 500


@treatments_bp.route('/api/<treatment_id>/implement', methods=['POST'])
@login_required
def implement_treatment(treatment_id):
    """Mark treatment as implemented"""
    import requests
    from flask import current_app
    
    data = request.get_json()
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.post(
            f'{backend_url}/treatments/{treatment_id}/implement',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return jsonify({
                'success': True,
                'data': response.json(),
                'message': 'Treatment marked as implemented'
            })
        else:
            logger.error(f"Failed to implement treatment {treatment_id}: {response.status_code}")
            return jsonify({
                'success': False,
                'error': 'Failed to implement treatment'
            }), 400
            
    except Exception as e:
        logger.error(f"Exception implementing treatment {treatment_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to implement treatment'
        }), 500


@treatments_bp.route('/api/<treatment_id>/review', methods=['POST'])
@login_required
def review_treatment(treatment_id):
    """Review treatment effectiveness"""
    import requests
    from flask import current_app
    
    data = request.get_json()
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.post(
            f'{backend_url}/treatments/{treatment_id}/review',
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return jsonify({
                'success': True,
                'data': response.json(),
                'message': 'Treatment review completed'
            })
        else:
            logger.error(f"Failed to review treatment {treatment_id}: {response.status_code}")
            return jsonify({
                'success': False,
                'error': 'Failed to review treatment'
            }), 400
            
    except Exception as e:
        logger.error(f"Exception reviewing treatment {treatment_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to review treatment'
        }), 500


@treatments_bp.route('/api/strategies')
@login_required
def get_treatment_strategies():
    """Get available treatment strategies"""
    strategies = [
        {
            'value': 'accept',
            'label': 'Accept',
            'description': 'Accept the risk and its potential consequences',
            'icon': 'fas fa-check-circle',
            'color': 'info'
        },
        {
            'value': 'mitigate',
            'label': 'Mitigate',
            'description': 'Implement controls to reduce likelihood or impact',
            'icon': 'fas fa-shield-alt',
            'color': 'primary'
        },
        {
            'value': 'transfer',
            'label': 'Transfer',
            'description': 'Transfer risk to third party (insurance, outsourcing)',
            'icon': 'fas fa-exchange-alt',
            'color': 'warning'
        },
        {
            'value': 'avoid',
            'label': 'Avoid',
            'description': 'Eliminate the risk by avoiding the activity',
            'icon': 'fas fa-ban',
            'color': 'danger'
        }
    ]
    return jsonify({'success': True, 'data': strategies})


@treatments_bp.route('/api/statuses')
@login_required
def get_treatment_statuses():
    """Get available treatment statuses"""
    statuses = [
        {'value': 'proposed', 'label': 'Proposed', 'color': 'secondary'},
        {'value': 'under_review', 'label': 'Under Review', 'color': 'info'},
        {'value': 'approved', 'label': 'Approved', 'color': 'primary'},
        {'value': 'in_progress', 'label': 'In Progress', 'color': 'warning'},
        {'value': 'implemented', 'label': 'Implemented', 'color': 'success'},
        {'value': 'rejected', 'label': 'Rejected', 'color': 'danger'},
        {'value': 'on_hold', 'label': 'On Hold', 'color': 'secondary'}
    ]
    return jsonify({'success': True, 'data': statuses})


@treatments_bp.route('/api/summary')
@login_required
def get_treatment_summary():
    """Get treatment summary statistics"""
    import requests
    from flask import current_app
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/treatments/summary',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            logger.error(f"Failed to fetch treatment summary: {response.status_code}")
            return jsonify({
                'success': True,
                'data': {
                    'total_treatments': 0,
                    'by_strategy': {'accept': 0, 'mitigate': 0, 'transfer': 0, 'avoid': 0},
                    'by_status': {'draft': 0, 'pending_approval': 0, 'approved': 0, 'implemented': 0},
                    'cost_estimate': 0.0
                }
            })
            
    except Exception as e:
        logger.error(f"Exception fetching treatment summary: {e}")
        return jsonify({
            'success': True,
            'data': {
                'total_treatments': 0,
                'by_strategy': {'accept': 0, 'mitigate': 0, 'transfer': 0, 'avoid': 0},
                'by_status': {'draft': 0, 'pending_approval': 0, 'approved': 0, 'implemented': 0},
                'cost_estimate': 0.0
            }
        })


@treatments_bp.route('/api/effectiveness')
@login_required
def get_treatment_effectiveness():
    """Get treatment effectiveness analysis"""
    import requests
    from flask import current_app
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/treatments/effectiveness',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            logger.error(f"Failed to fetch treatment effectiveness: {response.status_code}")
            return jsonify({
                'success': True,
                'data': {
                    'overall_effectiveness': 0.0,
                    'by_strategy': {
                        'accept': {'count': 0, 'avg_effectiveness': 0.0},
                        'mitigate': {'count': 0, 'avg_effectiveness': 0.0},
                        'transfer': {'count': 0, 'avg_effectiveness': 0.0},
                        'avoid': {'count': 0, 'avg_effectiveness': 0.0}
                    },
                    'top_performers': [],
                    'needs_improvement': []
                }
            })
            
    except Exception as e:
        logger.error(f"Exception fetching treatment effectiveness: {e}")
        return jsonify({
            'success': True,
            'data': {
                'overall_effectiveness': 0.0,
                'by_strategy': {
                    'accept': {'count': 0, 'avg_effectiveness': 0.0},
                    'mitigate': {'count': 0, 'avg_effectiveness': 0.0},
                    'transfer': {'count': 0, 'avg_effectiveness': 0.0},
                    'avoid': {'count': 0, 'avg_effectiveness': 0.0}
                },
                'top_performers': [],
                'needs_improvement': []
            }
        })


@treatments_bp.route('/api/users')
@login_required
def get_users_for_dropdown():
    """Get users for treatment owner dropdown"""
    import requests
    from flask import current_app
    
    try:
        # Get auth token from cookies
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/users',
            params={'limit': 1000, 'is_active': True},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            users = []
            
            # Handle different response formats
            if isinstance(data, dict) and 'data' in data:
                users = data['data']
            elif isinstance(data, list):
                users = data
            
            # Format users for dropdown
            formatted_users = []
            for user in users:
                formatted_users.append({
                    'id': user.get('id', ''),
                    'username': user.get('username', ''),
                    'full_name': user.get('full_name', user.get('username', '')),
                    'email': user.get('email', ''),
                    'department': user.get('department', ''),
                    'display_name': f"{user.get('full_name', user.get('username', ''))} ({user.get('department', 'No Dept')})"
                })
            
            return jsonify({
                'success': True,
                'data': formatted_users
            })
        else:
            logger.warning(f"Failed to fetch users: {response.status_code}")
            return jsonify({'success': True, 'data': []})
            
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({'success': True, 'data': []})