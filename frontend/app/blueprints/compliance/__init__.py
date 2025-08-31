"""
Compliance Check Management Blueprint
Handles compliance assessments, monitoring, and reporting
"""
from flask import Blueprint, render_template, jsonify, request
from app.utils.auth import login_required
from app.services.api_service import APIService
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response
import logging

logger = logging.getLogger(__name__)

compliance_bp = Blueprint('compliance', __name__, template_folder='templates')


@compliance_bp.route('/')
@login_required
def index():
    """Compliance management main page"""
    return render_template('compliance/index.html')


@compliance_bp.route('/api/checks')
@login_required
def get_compliance_checks():
    """Get compliance checks list"""
    import requests
    from flask import current_app, session
    
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/compliance/status',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
    
    # Fallback to mock data if backend unavailable
    params = {
        'skip': request.args.get('skip', 0, type=int),
        'limit': request.args.get('limit', 100, type=int),
        'framework': request.args.get('framework'),
        'status': request.args.get('status'),
        'category': request.args.get('category'),
        'risk_level': request.args.get('risk_level'),
        'search': request.args.get('search'),
        'sort_by': request.args.get('sort_by', 'created_at'),
        'sort_order': request.args.get('sort_order', 'desc')
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    # Call backend API for compliance checks
    try:
        import requests
        from flask import current_app
        
        token = request.cookies.get('napsa_token')
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/compliance/checks',
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            logger.error(f"Backend returned {response.status_code} for compliance checks")
            return jsonify({
                'success': True,
                'data': {'items': [], 'total': 0}
            })
            
    except Exception as e:
        logger.error(f"Error fetching compliance checks: {e}")
        return jsonify({
            'success': True,
            'data': {'items': [], 'total': 0}
        })


@compliance_bp.route('/api/checks/<check_id>')
@login_required
def get_compliance_check(check_id):
    """Get single compliance check details"""
    response = get_empty_response()
    return jsonify(response)


@compliance_bp.route('/api/checks/create', methods=['POST'])
@login_required
def create_compliance_check():
    """Create new compliance check"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@compliance_bp.route('/api/checks/<check_id>/update', methods=['PUT'])
@login_required
def update_compliance_check(check_id):
    """Update existing compliance check"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@compliance_bp.route('/api/checks/<check_id>/delete', methods=['DELETE'])
@login_required
def delete_compliance_check(check_id):
    """Delete compliance check"""
    response = get_empty_response()
    return jsonify(response)


@compliance_bp.route('/api/checks/<check_id>/assess', methods=['POST'])
@login_required
def assess_compliance(check_id):
    """Perform compliance assessment"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@compliance_bp.route('/api/checks/<check_id>/evidence', methods=['POST'])
@login_required
def upload_evidence(check_id):
    """Upload evidence for compliance check"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@compliance_bp.route('/api/checks/<check_id>/remediate', methods=['POST'])
@login_required
def create_remediation(check_id):
    """Create remediation plan for non-compliance"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@compliance_bp.route('/api/frameworks')
@login_required
def get_compliance_frameworks():
    """Get available compliance frameworks"""
    import requests
    from flask import current_app, session
    
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/compliance/frameworks',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error getting frameworks: {e}")
    
    # Fallback to hardcoded list
    frameworks = [
        {
            'value': 'iso27001',
            'label': 'ISO 27001:2022',
            'description': 'Information Security Management System',
            'categories': ['Information Security', 'Risk Management', 'Access Control']
        },
        {
            'value': 'pci_dss',
            'label': 'PCI DSS v4.0',
            'description': 'Payment Card Industry Data Security Standard',
            'categories': ['Payment Security', 'Data Protection', 'Network Security']
        },
        {
            'value': 'gdpr',
            'label': 'GDPR',
            'description': 'General Data Protection Regulation',
            'categories': ['Data Privacy', 'Personal Data', 'Data Rights']
        },
        {
            'value': 'nist',
            'label': 'NIST Cybersecurity Framework',
            'description': 'Framework for Improving Critical Infrastructure Cybersecurity',
            'categories': ['Identify', 'Protect', 'Detect', 'Respond', 'Recover']
        },
        {
            'value': 'cobit',
            'label': 'COBIT 2019',
            'description': 'Control Objectives for Information Technologies',
            'categories': ['IT Governance', 'Risk Management', 'Compliance']
        },
        {
            'value': 'sox',
            'label': 'SOX',
            'description': 'Sarbanes-Oxley Act',
            'categories': ['Financial Reporting', 'Internal Controls', 'Audit']
        },
        {
            'value': 'basel_iii',
            'label': 'Basel III',
            'description': 'Banking Supervision Framework',
            'categories': ['Capital Requirements', 'Risk Management', 'Liquidity']
        },
        {
            'value': 'local_regulations',
            'label': 'Zambian Regulations',
            'description': 'Local regulatory requirements for pension schemes',
            'categories': ['Pension Act', 'Financial Regulations', 'Data Protection Act']
        }
    ]
    return jsonify({'success': True, 'data': frameworks})


@compliance_bp.route('/api/requirement-categories')
@login_required
def get_requirement_categories():
    """Get compliance requirement categories"""
    categories = [
        'Access Control',
        'Data Protection',
        'Network Security',
        'Incident Response',
        'Business Continuity',
        'Risk Management',
        'Asset Management',
        'Physical Security',
        'Compliance Management',
        'Audit & Logging',
        'Vendor Management',
        'Change Management'
    ]
    return jsonify({'success': True, 'data': categories})


@compliance_bp.route('/api/compliance-status')
@login_required
def get_compliance_status():
    """Get overall compliance status"""
    import requests
    from flask import current_app, session
    
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        response = requests.get(
            f'{backend_url}/compliance/status',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
    
    # Fallback to mock data
    response = get_empty_stats_response()
    return jsonify(response)


@compliance_bp.route('/api/compliance-dashboard')
@login_required
def get_compliance_dashboard():
    """Get compliance dashboard data"""
    import requests
    from flask import current_app, session
    
    try:
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        # Get dashboard data
        dashboard_response = requests.get(
            f'{backend_url}/compliance/dashboard',
            timeout=5
        )
        
        # Get status data
        status_response = requests.get(
            f'{backend_url}/compliance/status',
            timeout=5
        )
        
        if dashboard_response.status_code == 200 and status_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            status_data = status_response.json()
            
            # Combine and format the data for frontend
            formatted_data = {
                'overall_compliance': status_data.get('overall_compliance', 0),
                'total_checks': status_data.get('total_requirements', 0),
                'compliant_count': status_data.get('mapped_requirements', 0),
                'partial_count': 0,  # Would need to calculate from actual assessments
                'non_compliant_count': status_data.get('compliance_gaps', 0),
                'frameworks': dashboard_data.get('frameworks', {}),
                'recent_assessments': status_data.get('recent_assessments', []),
                'by_framework': status_data.get('by_framework', {})
            }
            
            return jsonify({'success': True, 'data': formatted_data})
    except Exception as e:
        logger.error(f"Error getting compliance dashboard: {e}")
    
    # Fallback to mock data
    response = get_empty_stats_response()
    return jsonify(response)


@compliance_bp.route('/api/compliance-report', methods=['POST'])
@login_required
def generate_compliance_report():
    """Generate compliance report"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@compliance_bp.route('/api/compliance-gaps')
@login_required
def get_compliance_gaps():
    """Get compliance gaps analysis"""
    response = get_empty_response()
    return jsonify(response)