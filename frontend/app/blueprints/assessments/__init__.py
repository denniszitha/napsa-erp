"""
Risk Assessments Blueprint - Production Version
No mock data - Direct backend integration only
"""
from flask import Blueprint, render_template, jsonify, request, session
from functools import wraps
import requests
import logging
import os
import socket
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
assessments_bp = Blueprint(
    'risk_assessments', 
    __name__,
    template_folder='templates',
    url_prefix='/risk-assessments'
)

# Backend API configuration
# Use the backend container name for Docker networking
# Or use the host IP with the exposed port
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://napsa-backend:8000')
# Fallback to host network if container name doesn't resolve
try:
    socket.gethostbyname('napsa-backend')
except:
    BACKEND_URL = 'http://102.23.120.243:58001'

API_BASE = f"{BACKEND_URL}/api/v1"


def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers from session"""
    headers = {'Content-Type': 'application/json'}
    
    # Get token from session if available
    if 'access_token' in session:
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


@assessments_bp.route('/')
def index():
    """Render assessments page"""
    # Force reload template to ensure no caching
    from flask import current_app
    current_app.jinja_env.cache = {}
    return render_template('assessments/index.html')


@assessments_bp.route('/api/list')
def list_assessments():
    """Get all risk assessments from backend"""
    try:
        # Get query parameters
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        risk_id = request.args.get('risk_id')
        
        # Build query parameters
        params = {'skip': skip, 'limit': limit}
        if risk_id:
            params['risk_id'] = risk_id
        
        # Call backend API
        response = requests.get(
            f"{API_BASE}/assessments/",
            headers=get_auth_headers(),
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'assessments': data.get('data', []),
                'total': data.get('total', 0),
                'skip': data.get('skip', 0),
                'limit': data.get('limit', 100)
            })
        else:
            return jsonify(handle_backend_error(response, "Fetch assessments"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error fetching assessments: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessments_bp.route('/api/create', methods=['POST'])
def create_assessment():
    """Create new risk assessment"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['risk_id', 'likelihood_score', 'impact_score', 'control_effectiveness']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Format next_review_date if provided
        if 'next_review_date' in data and data['next_review_date']:
            # Ensure date is in ISO format
            if 'T' not in data['next_review_date']:
                data['next_review_date'] = f"{data['next_review_date']}T00:00:00"
        
        # Call backend API
        response = requests.post(
            f"{API_BASE}/assessments/",
            headers=get_auth_headers(),
            json=data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            assessment_data = response.json()
            return jsonify({
                'success': True,
                'message': 'Assessment created successfully',
                'data': assessment_data
            })
        else:
            return jsonify(handle_backend_error(response, "Create assessment"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error creating assessment: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessments_bp.route('/api/get/<assessment_id>')
def get_assessment(assessment_id):
    """Get single assessment by ID"""
    try:
        response = requests.get(
            f"{API_BASE}/assessments/{assessment_id}",
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
                'error': 'Assessment not found'
            }), 404
        else:
            return jsonify(handle_backend_error(response, "Get assessment"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error fetching assessment: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessments_bp.route('/api/update/<assessment_id>', methods=['PUT'])
def update_assessment(assessment_id):
    """Update existing assessment"""
    try:
        data = request.json
        
        # Format next_review_date if provided
        if 'next_review_date' in data and data['next_review_date']:
            if 'T' not in data['next_review_date']:
                data['next_review_date'] = f"{data['next_review_date']}T00:00:00"
        
        response = requests.put(
            f"{API_BASE}/assessments/{assessment_id}",
            headers=get_auth_headers(),
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Assessment updated successfully',
                'data': response.json()
            })
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Assessment not found'
            }), 404
        else:
            return jsonify(handle_backend_error(response, "Update assessment"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error updating assessment: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessments_bp.route('/api/delete/<assessment_id>', methods=['DELETE'])
def delete_assessment(assessment_id):
    """Delete assessment"""
    try:
        response = requests.delete(
            f"{API_BASE}/assessments/{assessment_id}",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            return jsonify({
                'success': True,
                'message': 'Assessment deleted successfully'
            })
        elif response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'Assessment not found'
            }), 404
        elif response.status_code == 403:
            return jsonify({
                'success': False,
                'error': 'Not authorized to delete this assessment'
            }), 403
        else:
            return jsonify(handle_backend_error(response, "Delete assessment"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error deleting assessment: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessments_bp.route('/api/risks')
def get_risks_for_assessment():
    """Get available risks for assessment from backend"""
    try:
        # Get query parameters
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Call backend API for risks
        response = requests.get(
            f"{API_BASE}/risks/",
            headers=get_auth_headers(),
            params={'skip': skip, 'limit': limit},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            risks = data.get('data', [])
            
            # Filter for active risks only
            active_risks = [r for r in risks if r.get('status') in ['active', 'under_review']]
            
            return jsonify({
                'success': True,
                'risks': active_risks,
                'total': len(active_risks)
            })
        else:
            return jsonify(handle_backend_error(response, "Fetch risks"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error fetching risks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessments_bp.route('/api/statistics')
def get_assessment_statistics():
    """Get assessment statistics from backend"""
    try:
        # Get all assessments for statistics
        response = requests.get(
            f"{API_BASE}/assessments/",
            headers=get_auth_headers(),
            params={'limit': 1000},  # Get all for statistics
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            assessments = data.get('data', [])
            
            # Calculate statistics
            total = len(assessments)
            within = len([a for a in assessments if a.get('risk_appetite_status') == 'within'])
            exceeds = total - within
            
            # Calculate average residual risk
            avg_residual = 0
            if total > 0:
                total_residual = sum(float(a.get('residual_risk', 0)) for a in assessments)
                avg_residual = round(total_residual / total, 2)
            
            return jsonify({
                'success': True,
                'statistics': {
                    'total': total,
                    'within_appetite': within,
                    'exceeds_appetite': exceeds,
                    'average_residual_risk': avg_residual
                }
            })
        else:
            return jsonify(handle_backend_error(response, "Fetch statistics"))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Backend service unavailable'
        }), 503
    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@assessments_bp.route('/api/export')
def export_assessments():
    """Export assessments to CSV"""
    try:
        import csv
        from io import StringIO
        from flask import Response
        
        # Get all assessments
        response = requests.get(
            f"{API_BASE}/assessments/",
            headers=get_auth_headers(),
            params={'limit': 10000},
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify(handle_backend_error(response, "Export assessments"))
        
        data = response.json()
        assessments = data.get('data', [])
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Assessment ID', 'Risk ID', 'Risk Title', 'Assessment Date',
            'Assessor', 'Likelihood', 'Impact', 'Inherent Risk',
            'Control Effectiveness', 'Residual Risk', 'Status', 'Notes'
        ])
        
        # Write data
        for assessment in assessments:
            writer.writerow([
                assessment.get('id', ''),
                assessment.get('risk_id', ''),
                assessment.get('risk_title', ''),
                assessment.get('assessment_date', ''),
                assessment.get('assessor_name', ''),
                assessment.get('likelihood_score', ''),
                assessment.get('impact_score', ''),
                assessment.get('inherent_risk', ''),
                assessment.get('control_effectiveness', ''),
                assessment.get('residual_risk', ''),
                assessment.get('risk_appetite_status', ''),
                assessment.get('notes', '')
            ])
        
        # Create response
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=assessments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting assessments: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Error handlers
@assessments_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Resource not found'}), 404


@assessments_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500