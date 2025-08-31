"""
Incident Management Blueprint
Handles incident reporting, tracking, investigation, and resolution
"""
from flask import Blueprint, render_template, jsonify, request, session, current_app
from app.utils.auth import login_required
from app.services.api_service import APIService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

incidents_bp = Blueprint('incidents', __name__, template_folder='templates')


@incidents_bp.route('/')
@login_required
def index():
    """Incident management main page"""
    return render_template('incidents/index.html')


@incidents_bp.route('/api/list')
@login_required
def get_incidents():
    """Get incidents list from backend API"""
    params = {
        'skip': request.args.get('skip', 0, type=int),
        'limit': request.args.get('limit', 100, type=int),
        'status': request.args.get('status'),
        'severity': request.args.get('severity'),
        'type': request.args.get('type'),
        'risk_id': request.args.get('risk_id'),
        'search': request.args.get('search')
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        result = APIService.get('/incidents/', params=params)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to fetch incidents')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error fetching incidents: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/risks')
@login_required
def get_available_risks():
    """Get available risks for incident association"""
    try:
        result = APIService.get('/incidents/risks')
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data')
            })
        else:
            # Fallback to general risks endpoint
            result = APIService.get('/risks/')
            if result.get('success'):
                risks_data = result.get('data', {})
                risks = risks_data.get('data', [])
                return jsonify({
                    'success': True,
                    'data': risks
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to fetch risks')
                }), result.get('code', 500)
                
    except Exception as e:
        logger.error(f"Error fetching risks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>')
@login_required
def get_incident(incident_id):
    """Get single incident details"""
    try:
        result = APIService.get(f'/incidents/{incident_id}')
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Incident not found')
            }), result.get('code', 404)
            
    except Exception as e:
        logger.error(f"Error fetching incident: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>/timeline')
@login_required
def get_incident_timeline(incident_id):
    """Get incident timeline"""
    try:
        result = APIService.get(f'/incidents/{incident_id}/timeline')
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to fetch timeline')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error fetching timeline: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>/communications')
@login_required
def get_incident_communications(incident_id):
    """Get incident communications"""
    try:
        result = APIService.get(f'/incidents/{incident_id}/communications')
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to fetch communications')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error fetching communications: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/create', methods=['POST'])
@login_required
def create_incident():
    """Create new incident"""
    data = request.get_json()
    
    # Ensure detected_at is properly formatted
    if 'detected_at' not in data or not data['detected_at']:
        data['detected_at'] = datetime.utcnow().isoformat()
    
    try:
        result = APIService.post('/incidents/', data)
        
        if result.get('success'):
            incident = result.get('data')
            return jsonify({
                'success': True,
                'data': incident,
                'message': f'Incident {incident.get("incident_code")} created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to create incident')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error creating incident: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>/update', methods=['PUT'])
@login_required
def update_incident(incident_id):
    """Update existing incident"""
    data = request.get_json()
    
    try:
        result = APIService.put(f'/incidents/{incident_id}', data)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data'),
                'message': 'Incident updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to update incident')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error updating incident: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>/status', methods=['PATCH'])
@login_required
def update_incident_status(incident_id):
    """Update incident status"""
    data = request.get_json()
    
    try:
        result = APIService.patch(f'/incidents/{incident_id}/status', data)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data'),
                'message': f'Status updated to {data.get("status")}'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to update status')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>/timeline', methods=['POST'])
@login_required
def add_timeline_event(incident_id):
    """Add timeline event to incident"""
    data = request.get_json()
    
    try:
        result = APIService.post(f'/incidents/{incident_id}/timeline', data)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data'),
                'message': 'Timeline event added'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to add timeline event')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error adding timeline event: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>/communications', methods=['POST'])
@login_required
def add_incident_communication(incident_id):
    """Add communication to incident"""
    data = request.get_json()
    
    try:
        result = APIService.post(f'/incidents/{incident_id}/communications', data)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data'),
                'message': 'Communication recorded'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to add communication')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error adding communication: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>/calculate-impact', methods=['POST'])
@login_required
def calculate_impact(incident_id):
    """Calculate incident impact"""
    data = request.get_json()
    
    try:
        result = APIService.post(f'/incidents/{incident_id}/calculate-impact', data)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data'),
                'message': 'Impact calculated'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to calculate impact')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error calculating impact: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/<incident_id>/delete', methods=['DELETE'])
@login_required
def delete_incident(incident_id):
    """Delete incident"""
    try:
        result = APIService.delete(f'/incidents/{incident_id}')
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Incident deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to delete incident')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error deleting incident: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/stats')
@login_required
def get_incident_stats():
    """Get incident statistics"""
    try:
        result = APIService.get('/incidents/stats/summary')
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to fetch statistics')
            }), result.get('code', 500)
            
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@incidents_bp.route('/api/dashboard')
@login_required
def get_incident_dashboard():
    """Get incident dashboard statistics"""
    try:
        # Get all incidents for dashboard stats
        result = APIService.get('/incidents/')
        
        if result.get('success'):
            incidents_data = result.get('data', {})
            incidents = incidents_data.get('data', []) if isinstance(incidents_data, dict) else incidents_data
            
            # Calculate dashboard stats
            total_incidents = len(incidents)
            open_incidents = len([i for i in incidents if i.get('status') in ['open', 'investigating']])
            critical_incidents = len([i for i in incidents if i.get('severity') == 'critical'])
            high_incidents = len([i for i in incidents if i.get('severity') == 'high'])
            
            # Calculate SLA breached (incidents open > 24 hours)
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            sla_breached = 0
            for incident in incidents:
                if incident.get('status') in ['open', 'investigating']:
                    try:
                        created_time = datetime.fromisoformat(incident.get('created_at', '').replace('Z', '+00:00'))
                        if created_time < cutoff_time:
                            sla_breached += 1
                    except:
                        pass
            
            return jsonify({
                'success': True,
                'data': {
                    'total_incidents': total_incidents,
                    'open_incidents': open_incidents,
                    'critical_incidents': critical_incidents + high_incidents,  # Combine critical and high
                    'sla_breached': sla_breached
                }
            })
        else:
            # Fallback if backend fails
            return jsonify({
                'success': True,
                'data': {
                    'total_incidents': 0,
                    'open_incidents': 0,
                    'critical_incidents': 0,
                    'sla_breached': 0
                }
            })
            
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        return jsonify({
            'success': True,
            'data': {
                'total_incidents': 0,
                'open_incidents': 0,
                'critical_incidents': 0,
                'sla_breached': 0
            }
        })