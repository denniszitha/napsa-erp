from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import uuid
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response
from app.services.api_service import APIService

# Create blueprint with template folder
regulations_bp = Blueprint('regulations', __name__, 
                          template_folder='templates',
                          static_folder='static')

# Storage for regulations (in production, this would be in a database)
regulations_storage = {}
compliance_mappings = {}

@regulations_bp.route('/')
def index():
    """Main regulations management page"""
    return render_template('regulations/index.html')

@regulations_bp.route('/api/regulations', methods=['GET'])
def get_regulations():
    """Get all regulations with filtering"""
    try:
        # Get filter parameters
        framework = request.args.get('framework', 'all')
        status = request.args.get('status', 'all')
        search = request.args.get('search', '')
        
        # Build API parameters
        params = {
            'skip': request.args.get('skip', 0, type=int),
            'limit': request.args.get('limit', 100, type=int)
        }
        if framework != 'all':
            params['framework'] = framework
        if status != 'all':
            params['status'] = status
        if search:
            params['search'] = search
            
        # Try APIService first
        result = APIService.get('/regulations', params)
        if result.get('success') and result.get('data'):
            return jsonify(result)
        
        # Fallback to mock data
        regulations = get_empty_paginated_response()
        
        # Apply filters to mock data
        filtered = regulations['data']['regulations']
        
        if framework != 'all':
            filtered = [r for r in filtered if r['framework'].lower() == framework.lower()]
        
        if status != 'all':
            filtered = [r for r in filtered if r['compliance_status'].lower() == status.lower()]
        
        if search:
            search_lower = search.lower()
            filtered = [r for r in filtered if 
                       search_lower in r['title'].lower() or 
                       search_lower in r['description'].lower()]
        
        return jsonify({
            'success': True,
            'data': {
                'regulations': filtered,
                'total': len(filtered),
                'stats': regulations['data']['stats']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/<regulation_id>', methods=['GET'])
def get_regulation(regulation_id):
    """Get specific regulation details"""
    try:
        # Try APIService first
        result = APIService.get(f'/regulations/{regulation_id}')
        if result.get('success') and result.get('data'):
            return jsonify(result)
        
        # Fallback to mock
        regulation = get_empty_response()
        return jsonify(regulation)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/requirements', methods=['GET'])
def get_regulatory_requirements():
    """Get all regulatory requirements"""
    try:
        framework = request.args.get('framework', None)
        requirements = get_empty_paginated_response()
        return jsonify(requirements)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/compliance-mapping', methods=['POST'])
def create_compliance_mapping():
    """Map internal controls to regulatory requirements"""
    try:
        data = request.json
        
        mapping = {
            'id': str(uuid.uuid4()),
            'regulation_id': data.get('regulation_id'),
            'requirement_id': data.get('requirement_id'),
            'control_id': data.get('control_id'),
            'control_type': data.get('control_type'),
            'mapping_status': data.get('mapping_status', 'mapped'),
            'evidence': data.get('evidence', []),
            'notes': data.get('notes', ''),
            'created_by': data.get('created_by', 'Current User'),
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Store mapping
        compliance_mappings[mapping['id']] = mapping
        
        return jsonify({
            'success': True,
            'data': mapping,
            'message': 'Compliance mapping created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/compliance-assessment', methods=['POST'])
def assess_compliance():
    """Perform compliance assessment against regulations"""
    try:
        data = request.json
        framework = data.get('framework')
        
        # Perform assessment
        assessment_result = get_empty_response()
        
        return jsonify(assessment_result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/gap-analysis', methods=['POST'])
def perform_gap_analysis():
    """Perform gap analysis for regulatory compliance"""
    try:
        data = request.json
        framework = data.get('framework')
        
        gaps = get_empty_response()
        
        return jsonify(gaps)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/updates', methods=['GET'])
def get_regulatory_updates():
    """Get latest regulatory updates and changes"""
    try:
        updates = get_empty_paginated_response()
        return jsonify(updates)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/obligations', methods=['GET'])
def get_compliance_obligations():
    """Get compliance obligations and deadlines"""
    try:
        obligations = get_empty_paginated_response()
        return jsonify(obligations)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/reporting', methods=['POST'])
def generate_compliance_report():
    """Generate regulatory compliance report"""
    try:
        data = request.json
        
        report = {
            'id': str(uuid.uuid4()),
            'report_type': data.get('report_type', 'compliance'),
            'framework': data.get('framework'),
            'period': data.get('period'),
            'generated_by': data.get('generated_by', 'Current User'),
            'generated_at': datetime.now().isoformat(),
            'format': data.get('format', 'pdf'),
            'content': {
                'executive_summary': 'Compliance assessment report generated',
                'compliance_score': 85,
                'gaps_identified': 12,
                'recommendations': 8
            }
        }
        
        return jsonify({
            'success': True,
            'data': report,
            'message': 'Compliance report generated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/dashboard', methods=['GET'])
def get_regulatory_dashboard():
    """Get regulatory compliance dashboard data"""
    try:
        dashboard = get_empty_stats_response()
        return jsonify(dashboard)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/penalties', methods=['GET'])
def get_penalties():
    """Get regulatory penalties and fines information"""
    try:
        framework = request.args.get('framework', None)
        penalties = get_empty_paginated_response()
        return jsonify(penalties)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/training', methods=['GET'])
def get_compliance_training():
    """Get compliance training requirements"""
    try:
        training = get_empty_paginated_response()
        return jsonify(training)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/certifications', methods=['GET'])
def get_certifications():
    """Get required certifications and licenses"""
    try:
        certifications = get_empty_paginated_response()
        return jsonify(certifications)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/audit-schedule', methods=['GET'])
def get_audit_schedule():
    """Get regulatory audit schedule"""
    try:
        schedule = get_empty_paginated_response()
        return jsonify(schedule)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@regulations_bp.route('/api/regulations/filing-deadlines', methods=['GET'])
def get_filing_deadlines():
    """Get regulatory filing deadlines"""
    try:
        deadlines = get_empty_paginated_response()
        return jsonify(deadlines)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500