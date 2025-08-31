from flask import Blueprint, render_template, request, jsonify, session, current_app
from app.utils.auth import login_required, get_current_user
import requests
import logging

matrix_bp = Blueprint('matrix', __name__)

@matrix_bp.route('/')
@login_required
def index():
    """Risk Matrix Configuration dashboard"""
    return render_template('matrix/index.html')

@matrix_bp.route('/api/matrices')
@login_required
def get_matrices():
    """Get all risk matrices"""
    try:
        # Return mock data for testing
        mock_matrices = [
            {
                "id": "matrix-1",
                "name": "Standard 5x5 Risk Matrix",
                "description": "Standard organizational risk matrix based on ISO 31000",
                "matrix_type": "standard",
                "likelihood_levels": 5,
                "impact_levels": 5,
                "is_active": True,
                "is_default": True,
                "created_at": "2025-08-15T12:00:00.000000"
            },
            {
                "id": "matrix-2", 
                "name": "Financial Services Matrix",
                "description": "Customized matrix for financial sector",
                "matrix_type": "custom",
                "likelihood_levels": 4,
                "impact_levels": 5,
                "is_active": True,
                "is_default": False,
                "created_at": "2025-08-14T10:00:00.000000"
            },
            {
                "id": "matrix-3",
                "name": "IT Risk Matrix",
                "description": "Specialized matrix for IT risks",
                "matrix_type": "custom", 
                "likelihood_levels": 5,
                "impact_levels": 4,
                "is_active": False,
                "is_default": False,
                "created_at": "2025-08-13T15:00:00.000000"
            }
        ]
        
        return jsonify({
            'success': True,
            'data': mock_matrices,
            'total': len(mock_matrices)
        })
        
        # Get token from session
        token = session.get('access_token')
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        # Get query parameters
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        # Call backend API
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        params = {'active_only': active_only}
        
        response = requests.get(
            f'{backend_url}/risk-matrices/',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            matrices = response.json()
            return jsonify({
                'success': True,
                'data': matrices,
                'total': len(matrices)
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Backend API error: {response.status_code}'
            }), response.status_code
            
    except Exception as e:
        logging.error(f"Error fetching matrices: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch matrices'
        }), 500

@matrix_bp.route('/api/matrices/<matrix_id>')
@login_required
def get_matrix(matrix_id):
    """Get specific risk matrix"""
    try:
        # Return mock data for testing
        mock_matrix = {
            "id": matrix_id,
            "name": "Standard 5x5 Risk Matrix",
            "description": "Standard organizational risk matrix based on ISO 31000",
            "matrix_type": "standard",
            "likelihood_levels": 5,
            "impact_levels": 5,
            "likelihood_labels": ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
            "impact_labels": ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"],
            "likelihood_descriptions": [
                "May occur only in exceptional circumstances (0-5%)",
                "Could occur at some time (5-25%)",
                "Might occur at some time (25-50%)",
                "Will probably occur in most circumstances (50-75%)",
                "Expected to occur in most circumstances (75-100%)"
            ],
            "impact_descriptions": [
                "Minimal impact on operations, reputation, or finances",
                "Minor impact with limited consequences",
                "Moderate impact requiring management attention",
                "Major impact with significant consequences",
                "Catastrophic impact threatening organizational survival"
            ],
            "risk_levels": {
                "low": {
                    "name": "Low",
                    "color": "#28a745",
                    "description": "Acceptable risk level",
                    "treatment_strategy": "Accept"
                },
                "medium": {
                    "name": "Medium",
                    "color": "#ffc107",
                    "description": "Monitor and review",
                    "treatment_strategy": "Monitor"
                },
                "high": {
                    "name": "High",
                    "color": "#fd7e14",
                    "description": "Requires mitigation",
                    "treatment_strategy": "Mitigate"
                },
                "very_high": {
                    "name": "Very High",
                    "color": "#dc3545",
                    "description": "Urgent action required",
                    "treatment_strategy": "Urgent Action"
                },
                "critical": {
                    "name": "Critical",
                    "color": "#6f42c1",
                    "description": "Immediate action required",
                    "treatment_strategy": "Immediate Action"
                }
            },
            "risk_thresholds": {
                "low": {"min": 1, "max": 4},
                "medium": {"min": 5, "max": 9},
                "high": {"min": 10, "max": 14},
                "very_high": {"min": 15, "max": 19},
                "critical": {"min": 20, "max": 25}
            },
            "is_active": True,
            "is_default": True,
            "created_at": "2025-08-15T12:00:00.000000"
        }
        
        return jsonify({
            'success': True,
            'data': mock_matrix
        })
        
    except Exception as e:
        logging.error(f"Error fetching matrix {matrix_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch matrix'
        }), 500

@matrix_bp.route('/api/matrices', methods=['POST'])
@login_required  
def create_matrix():
    """Create new risk matrix"""
    try:
        matrix_data = request.get_json()
        
        # Return mock success response for testing
        import uuid
        new_matrix_id = str(uuid.uuid4())
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_matrix_id,
                **matrix_data,
                'created_at': '2025-08-15T12:30:00.000000',
                'is_active': True,
                'is_default': False
            },
            'message': 'Risk matrix created successfully'
        })
        
    except Exception as e:
        logging.error(f"Error creating matrix: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to create matrix: {str(e)}'
        }), 400

@matrix_bp.route('/api/matrices/<matrix_id>', methods=['PUT'])
@login_required
def update_matrix(matrix_id):
    """Update risk matrix"""
    try:
        matrix_data = request.get_json()
        
        # Return mock success response for testing
        return jsonify({
            'success': True,
            'data': {
                'id': matrix_id,
                **matrix_data,
                'updated_at': '2025-08-15T12:30:00.000000'
            },
            'message': 'Risk matrix updated successfully'
        })
        
    except Exception as e:
        logging.error(f"Error updating matrix {matrix_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to update matrix: {str(e)}'
        }), 400

@matrix_bp.route('/api/matrices/<matrix_id>', methods=['DELETE'])
@login_required
def delete_matrix(matrix_id):
    """Delete risk matrix"""
    try:
        # Return mock success response for testing
        return jsonify({
            'success': True,
            'message': 'Risk matrix deleted successfully'
        })
        
    except Exception as e:
        logging.error(f"Error deleting matrix {matrix_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete matrix: {str(e)}'
        }), 400

@matrix_bp.route('/api/matrices/<matrix_id>/set-default', methods=['POST'])
@login_required
def set_default_matrix(matrix_id):
    """Set matrix as default"""
    try:
        # Return mock success response for testing
        return jsonify({
            'success': True,
            'message': 'Matrix set as default successfully'
        })
        
    except Exception as e:
        logging.error(f"Error setting default matrix {matrix_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to set default matrix: {str(e)}'
        }), 400

@matrix_bp.route('/api/matrices/<matrix_id>/duplicate', methods=['POST'])
@login_required
def duplicate_matrix(matrix_id):
    """Duplicate existing matrix"""
    try:
        data = request.get_json()
        new_name = data.get('name', 'Copy of Matrix')
        
        # Return mock success response for testing
        import uuid
        new_matrix_id = str(uuid.uuid4())
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_matrix_id,
                'name': new_name,
                'matrix_type': 'custom',
                'created_at': '2025-08-15T12:30:00.000000'
            },
            'message': 'Matrix duplicated successfully'
        })
        
    except Exception as e:
        logging.error(f"Error duplicating matrix {matrix_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to duplicate matrix: {str(e)}'
        }), 400

@matrix_bp.route('/api/templates')
@login_required
def get_templates():
    """Get matrix templates"""
    try:
        # Return mock templates for testing
        mock_templates = [
            {
                "id": "template-1",
                "name": "ISO 31000 Standard",
                "description": "Standard 5x5 matrix based on ISO 31000",
                "industry": "General",
                "is_public": True
            },
            {
                "id": "template-2", 
                "name": "Financial Services",
                "description": "Specialized matrix for banking and finance",
                "industry": "Financial Services",
                "is_public": True
            },
            {
                "id": "template-3",
                "name": "Healthcare Risk Matrix",
                "description": "Designed for healthcare organizations",
                "industry": "Healthcare",
                "is_public": True
            },
            {
                "id": "template-4",
                "name": "Manufacturing Safety",
                "description": "Manufacturing and industrial safety focused",
                "industry": "Manufacturing",
                "is_public": True
            }
        ]
        
        return jsonify({
            'success': True,
            'data': mock_templates,
            'total': len(mock_templates)
        })
        
    except Exception as e:
        logging.error(f"Error fetching templates: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch templates'
        }), 500

@matrix_bp.route('/api/matrices/from-template/<template_id>', methods=['POST'])
@login_required
def create_from_template(template_id):
    """Create matrix from template"""
    try:
        data = request.get_json()
        matrix_name = data.get('name', 'New Matrix from Template')
        
        # Return mock success response for testing
        import uuid
        new_matrix_id = str(uuid.uuid4())
        
        return jsonify({
            'success': True,
            'data': {
                'id': new_matrix_id,
                'name': matrix_name,
                'matrix_type': 'custom',
                'template_id': template_id,
                'created_at': '2025-08-15T12:30:00.000000'
            },
            'message': 'Matrix created from template successfully'
        })
        
    except Exception as e:
        logging.error(f"Error creating from template {template_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to create from template: {str(e)}'
        }), 400

@matrix_bp.route('/api/matrices/validate', methods=['POST'])
@login_required
def validate_matrix():
    """Validate matrix configuration"""
    try:
        matrix_config = request.get_json()
        
        # Basic validation
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['name', 'likelihood_levels', 'impact_levels', 'likelihood_labels', 'impact_labels']
        for field in required_fields:
            if field not in matrix_config:
                errors.append(f"Missing required field: {field}")
        
        # Validate dimensions
        if 'likelihood_levels' in matrix_config:
            if not 3 <= matrix_config['likelihood_levels'] <= 7:
                errors.append("Likelihood levels must be between 3 and 7")
        
        if 'impact_levels' in matrix_config:
            if not 3 <= matrix_config['impact_levels'] <= 7:
                errors.append("Impact levels must be between 3 and 7")
        
        # Validate labels match dimensions
        if 'likelihood_labels' in matrix_config and 'likelihood_levels' in matrix_config:
            if len(matrix_config['likelihood_labels']) != matrix_config['likelihood_levels']:
                errors.append("Number of likelihood labels must match likelihood levels")
        
        if 'impact_labels' in matrix_config and 'impact_levels' in matrix_config:
            if len(matrix_config['impact_labels']) != matrix_config['impact_levels']:
                errors.append("Number of impact labels must match impact levels")
        
        return jsonify({
            'success': True,
            'data': {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
        })
        
    except Exception as e:
        logging.error(f"Error validating matrix: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to validate matrix: {str(e)}'
        }), 400

@matrix_bp.route('/api/matrices/calculate-risk', methods=['POST'])
@login_required
def calculate_risk():
    """Calculate risk score and level"""
    try:
        calculation = request.get_json()
        likelihood = calculation.get('likelihood')
        impact = calculation.get('impact')
        
        if not likelihood or not impact:
            return jsonify({
                'success': False,
                'error': 'Likelihood and impact are required'
            }), 400
        
        # Calculate risk score
        risk_score = likelihood * impact
        
        # Determine risk level
        if risk_score <= 4:
            risk_level = "Low"
            risk_color = "#28a745"
            treatment_strategy = "Accept"
        elif risk_score <= 9:
            risk_level = "Medium"
            risk_color = "#ffc107"
            treatment_strategy = "Monitor"
        elif risk_score <= 14:
            risk_level = "High"
            risk_color = "#fd7e14"
            treatment_strategy = "Mitigate"
        elif risk_score <= 19:
            risk_level = "Very High"
            risk_color = "#dc3545"
            treatment_strategy = "Urgent Action"
        else:
            risk_level = "Critical"
            risk_color = "#6f42c1"
            treatment_strategy = "Immediate Action"
        
        return jsonify({
            'success': True,
            'data': {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_color': risk_color,
                'treatment_strategy': treatment_strategy,
                'description': f"{risk_level} risk requiring {treatment_strategy.lower()}"
            }
        })
        
    except Exception as e:
        logging.error(f"Error calculating risk: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to calculate risk: {str(e)}'
        }), 400