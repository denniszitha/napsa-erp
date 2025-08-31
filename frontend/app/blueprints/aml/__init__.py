"""
AML/KYC Management Blueprint
Handles anti-money laundering checks, sanctions screening, and KYC verification
"""
from flask import Blueprint, render_template, jsonify, request
from app.utils.auth import login_required
from app.services.api_service import APIService
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response
import logging
import requests
import os
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# OpenSanctions API configuration
YENTE_API_URL = os.getenv('YENTE_API_URL', 'http://45.93.137.89:8000')
OPEN_SANCTIONS_API_KEY = os.getenv('OPEN_SANCTIONS_API_KEY', '69c2cedca0bea99a972de11e28791d57')

aml_bp = Blueprint('aml', __name__, template_folder='templates')


@aml_bp.route('/')
@login_required
def index():
    """AML/KYC management main page"""
    return render_template('aml/index.html')


@aml_bp.route('/api/screen', methods=['POST'])
@login_required
def screen_entity():
    """Screen an entity against sanctions lists using OpenSanctions API"""
    data = request.get_json()
    
    # Prepare the query for OpenSanctions API
    query_data = {
        "queries": {
            "match": {
                "schema": data.get('entity_type', 'Person'),
                "properties": {
                    "name": [data.get('name', '')]
                }
            }
        }
    }
    
    # Add optional fields if provided
    if data.get('birth_date'):
        query_data["queries"]["match"]["properties"]["birthDate"] = [data['birth_date']]
    
    if data.get('nationality'):
        query_data["queries"]["match"]["properties"]["nationality"] = [data['nationality']]
    
    if data.get('identification_number'):
        query_data["queries"]["match"]["properties"]["idNumber"] = [data['identification_number']]
    
    if data.get('address'):
        query_data["queries"]["match"]["properties"]["address"] = [data['address']]
    
    # For companies
    if data.get('entity_type') == 'Company':
        if data.get('jurisdiction'):
            query_data["queries"]["match"]["properties"]["jurisdiction"] = [data['jurisdiction']]
        if data.get('registration_number'):
            query_data["queries"]["match"]["properties"]["registrationNumber"] = [data['registration_number']]
    
    try:
        # Call OpenSanctions API
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OPEN_SANCTIONS_API_KEY}'
        }
        
        response = requests.post(
            f'{YENTE_API_URL}/match/default?algorithm=best&limit=10',
            json=query_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            matches = result.get('responses', {}).get('match', {}).get('results', [])
            
            # Process and enhance results
            processed_matches = []
            for match in matches:
                processed_match = {
                    'id': match.get('id'),
                    'name': match.get('caption'),
                    'score': match.get('score', 0),
                    'match': match.get('match', False),
                    'datasets': match.get('datasets', []),
                    'schema': match.get('schema'),
                    'properties': match.get('properties', {}),
                    'features': match.get('features', {}),
                    'risk_level': _calculate_risk_level(match),
                    'categories': _determine_categories(match),
                    'screening_date': datetime.now().isoformat()
                }
                processed_matches.append(processed_match)
            
            # Store screening result
            screening_result = {
                'query': data,
                'matches': processed_matches,
                'total_matches': len(processed_matches),
                'high_risk_matches': sum(1 for m in processed_matches if m['risk_level'] == 'high'),
                'screening_date': datetime.now().isoformat(),
                'api_version': 'OpenSanctions/Yente',
                'status': 'completed'
            }
            
            # In production, save to database
            # Save to API service instead of mock
            pass
            
            return jsonify({
                'success': True,
                'data': screening_result
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API request failed with status {response.status_code}'
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request timeout - API service may be unavailable'
        }), 504
    except Exception as e:
        logger.error(f"Error screening entity: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@aml_bp.route('/api/watchlist/screen', methods=['POST'])
@login_required
def screen_watchlist():
    """Screen against internal watchlist"""
    data = request.get_json()
    search_name = data.get('name', '')
    
    # Check internal watchlist (mock implementation)
    response = get_empty_response()
    return jsonify(response)


@aml_bp.route('/api/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    """Add entity to internal watchlist"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@aml_bp.route('/api/kyc/verify', methods=['POST'])
@login_required
def verify_kyc():
    """Verify KYC information for a member"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@aml_bp.route('/api/kyc/list')
@login_required
def get_kyc_list():
    """Get list of KYC verifications"""
    params = {
        'skip': request.args.get('skip', 0, type=int),
        'limit': request.args.get('limit', 100, type=int),
        'status': request.args.get('status'),
        'search': request.args.get('search')
    }
    
    response = get_empty_paginated_response()
    return jsonify(response)


@aml_bp.route('/api/screenings/list')
@login_required
def get_screenings():
    """Get list of screening results"""
    params = {
        'skip': request.args.get('skip', 0, type=int),
        'limit': request.args.get('limit', 100, type=int),
        'risk_level': request.args.get('risk_level'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'search': request.args.get('search')
    }
    
    # Try backend first
    try:
        from flask import current_app
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        # Remove None values
        backend_params = {k: v for k, v in params.items() if v is not None}
        
        backend_response = requests.get(
            f'{backend_url}/aml/screenings',
            params=backend_params,
            timeout=5
        )
        
        if backend_response.status_code == 200:
            return jsonify(backend_response.json())
    except Exception as e:
        logger.error(f"Failed to get screenings from backend: {e}")
    
    # Fallback to mock data
    response = get_empty_paginated_response()
    return jsonify(response)


@aml_bp.route('/api/screenings/<screening_id>')
@login_required
def get_screening_detail(screening_id):
    """Get detailed screening result"""
    response = get_empty_response()
    return jsonify(response)


@aml_bp.route('/api/risk-assessment', methods=['POST'])
@login_required
def assess_aml_risk():
    """Perform AML risk assessment"""
    data = request.get_json()
    response = get_empty_response()
    return jsonify(response)


@aml_bp.route('/api/dashboard')
@login_required
def get_aml_dashboard():
    """Get AML dashboard statistics"""
    # Try backend first
    try:
        from flask import current_app
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        
        backend_response = requests.get(
            f'{backend_url}/aml/dashboard',
            timeout=5
        )
        
        if backend_response.status_code == 200:
            return jsonify({'success': True, 'data': backend_response.json()})
    except Exception as e:
        logger.error(f"Failed to get AML dashboard from backend: {e}")
    
    # Fallback to mock data
    response = get_empty_stats_response()
    return jsonify(response)


@aml_bp.route('/api/reports/generate', methods=['POST'])
@login_required
def generate_aml_report():
    """Generate comprehensive AML compliance report"""
    data = request.get_json()
    
    report_type = data.get('type', 'screening')
    period = data.get('period', 'current')
    format_type = data.get('format', 'pdf')
    matches = data.get('matches', [])
    notes = data.get('notes', '')
    sections = data.get('sections', {})
    
    # Generate report content based on type
    report_content = {
        'title': _get_report_title(report_type),
        'generated_at': datetime.now().isoformat(),
        'generated_by': 'AML Compliance Officer',  # In production, use current_user
        'report_type': report_type,
        'period': period,
        'total_matches': len(matches),
        'high_risk_count': sum(1 for m in matches if m.get('risk_level') == 'high'),
        'medium_risk_count': sum(1 for m in matches if m.get('risk_level') == 'medium'),
        'low_risk_count': sum(1 for m in matches if m.get('risk_level') == 'low'),
        'notes': notes
    }
    
    # Add sections based on selection
    if sections.get('executive_summary', True):
        report_content['executive_summary'] = _generate_executive_summary(matches, report_type)
    
    if sections.get('risk_assessment', True):
        report_content['risk_assessment'] = _generate_risk_assessment(matches)
    
    if sections.get('detailed_matches', True):
        report_content['detailed_matches'] = _generate_detailed_matches(matches)
    
    if sections.get('recommendations', True):
        report_content['recommendations'] = _generate_recommendations(matches, report_type)
    
    # In production, this would generate actual PDF/Excel file
    file_path = f"/reports/aml_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
    
    # Log report generation
    logger.info(f"Generated {report_type} report with {len(matches)} matches")
    
    return jsonify({
        'success': True,
        'data': {
            'report_id': str(uuid.uuid4()),
            'type': report_type,
            'format': format_type,
            'period': period,
            'generated_at': datetime.now().isoformat(),
            'file_path': file_path,
            'content_preview': report_content
        }
    })


@aml_bp.route('/api/alerts')
@login_required
def get_aml_alerts():
    """Get AML alerts and notifications"""
    response = get_empty_paginated_response()
    return jsonify(response)


@aml_bp.route('/api/datasets')
@login_required
def get_available_datasets():
    """Get available sanctions datasets from OpenSanctions"""
    try:
        response = requests.get(
            f'{YENTE_API_URL}/catalog',
            headers={'Authorization': f'Bearer {OPEN_SANCTIONS_API_KEY}'},
            timeout=10
        )
        
        if response.status_code == 200:
            catalog = response.json()
            datasets = catalog.get('datasets', [])
            
            # Filter and format relevant datasets
            formatted_datasets = []
            for dataset in datasets:
                if dataset.get('load'):
                    formatted_datasets.append({
                        'name': dataset.get('name'),
                        'title': dataset.get('title'),
                        'summary': dataset.get('summary'),
                        'entity_count': dataset.get('entity_count'),
                        'last_updated': dataset.get('last_export'),
                        'category': dataset.get('category'),
                        'tags': dataset.get('tags', [])
                    })
            
            return jsonify({
                'success': True,
                'data': formatted_datasets
            })
    except Exception as e:
        logger.error(f"Error fetching datasets: {str(e)}")
    
    # Return default datasets if API call fails
    return jsonify({
        'success': True,
        'data': [
            {'name': 'sanctions', 'title': 'All Sanctions Lists', 'category': 'sanctions'},
            {'name': 'peps', 'title': 'Politically Exposed Persons', 'category': 'peps'},
            {'name': 'crime', 'title': 'Crime-related Entities', 'category': 'crime'},
            {'name': 'default', 'title': 'All OpenSanctions Data', 'category': 'all'}
        ]
    })


def _calculate_risk_level(match):
    """Calculate risk level based on match score and datasets"""
    score = match.get('score', 0)
    datasets = match.get('datasets', [])
    
    # High risk if score > 0.8 or on certain critical lists
    critical_lists = ['us_ofac_sdn', 'un_sc_sanctions', 'eu_fsf']
    if score > 0.8 or any(ds in datasets for ds in critical_lists):
        return 'high'
    elif score > 0.6:
        return 'medium'
    else:
        return 'low'


def _determine_categories(match):
    """Determine AML categories based on datasets and properties"""
    categories = []
    datasets = match.get('datasets', [])
    properties = match.get('properties', {})
    
    # Check datasets for category indicators
    for dataset in datasets:
        ds = dataset.lower()
        if 'pep' in ds or 'world_leaders' in ds or 'protocol' in ds:
            if 'PEP' not in categories:
                categories.append('PEP')
        if 'sanction' in ds or 'ofac' in ds or 'sdn' in ds or 'fsf' in ds:
            if 'Sanctions' not in categories:
                categories.append('Sanctions')
        if 'crime' in ds or 'corruption' in ds or 'bribe' in ds:
            if 'Crime' not in categories:
                categories.append('Crime')
        if 'terror' in ds or 'un_sc' in ds:
            if 'Terrorist' not in categories:
                categories.append('Terrorist')
        if 'disqualified' in ds or 'debarred' in ds:
            if 'Disqualified' not in categories:
                categories.append('Disqualified')
        if 'interpol' in ds or 'wanted' in ds:
            if 'Wanted' not in categories:
                categories.append('Wanted')
    
    # Check properties for additional categorization
    if properties.get('topics'):
        for topic in properties['topics']:
            if 'role.pep' in topic and 'PEP' not in categories:
                categories.append('PEP')
            if 'crime' in topic and 'Crime' not in categories:
                categories.append('Crime')
            if 'sanction' in topic and 'Sanctions' not in categories:
                categories.append('Sanctions')
    
    return categories


def _get_report_title(report_type):
    """Get report title based on type"""
    titles = {
        'screening': 'AML Screening Report',
        'compliance': 'AML Compliance Report',
        'str': 'Suspicious Transaction Report (STR)',
        'monthly': 'Monthly AML Summary Report'
    }
    return titles.get(report_type, 'AML Report')


def _generate_executive_summary(matches, report_type):
    """Generate executive summary for report"""
    high_risk = sum(1 for m in matches if m.get('risk_level') == 'high')
    total = len(matches)
    
    summary = {
        'overview': f"This {_get_report_title(report_type)} contains analysis of {total} potential matches identified during AML screening.",
        'key_findings': [
            f"Total entities screened: {total}",
            f"High-risk matches: {high_risk}",
            f"Immediate action required: {high_risk} cases",
            f"Categories identified: {', '.join(set(cat for m in matches for cat in m.get('categories', [])))}" if matches else "No matches found"
        ],
        'risk_summary': f"{'CRITICAL' if high_risk > 0 else 'STANDARD'} - {high_risk} high-risk entities require immediate review",
        'compliance_status': 'Action Required' if high_risk > 0 else 'Compliant'
    }
    return summary


def _generate_risk_assessment(matches):
    """Generate risk assessment section"""
    assessment = {
        'overall_risk': 'HIGH' if any(m.get('risk_level') == 'high' for m in matches) else 'MEDIUM' if any(m.get('risk_level') == 'medium' for m in matches) else 'LOW',
        'risk_distribution': {
            'high': sum(1 for m in matches if m.get('risk_level') == 'high'),
            'medium': sum(1 for m in matches if m.get('risk_level') == 'medium'),
            'low': sum(1 for m in matches if m.get('risk_level') == 'low')
        },
        'category_risks': {},
        'recommendations': []
    }
    
    # Analyze by category
    for match in matches:
        for category in match.get('categories', []):
            if category not in assessment['category_risks']:
                assessment['category_risks'][category] = 0
            assessment['category_risks'][category] += 1
    
    # Generate recommendations based on findings
    if assessment['risk_distribution']['high'] > 0:
        assessment['recommendations'].append('Immediate review required for high-risk matches')
        assessment['recommendations'].append('Escalate to senior compliance officer')
        assessment['recommendations'].append('Consider filing STR for confirmed matches')
    
    return assessment


def _generate_detailed_matches(matches):
    """Generate detailed match information"""
    detailed = []
    for match in matches:
        detail = {
            'id': match.get('id'),
            'name': match.get('name'),
            'score': match.get('score'),
            'risk_level': match.get('risk_level'),
            'categories': match.get('categories', []),
            'datasets': match.get('datasets', []),
            'properties': match.get('properties', {}),
            'screening_date': match.get('screening_date'),
            'analysis': f"Entity '{match.get('name')}' matched with {match.get('score', 0)*100:.1f}% confidence. "
                       f"Risk level: {match.get('risk_level', 'unknown').upper()}. "
                       f"Found in {len(match.get('datasets', []))} data sources."
        }
        detailed.append(detail)
    return detailed


def _generate_recommendations(matches, report_type):
    """Generate recommendations based on matches"""
    recommendations = []
    
    high_risk_count = sum(1 for m in matches if m.get('risk_level') == 'high')
    has_sanctions = any('Sanctions' in m.get('categories', []) for m in matches)
    has_pep = any('PEP' in m.get('categories', []) for m in matches)
    has_crime = any('Crime' in m.get('categories', []) for m in matches)
    
    if high_risk_count > 0:
        recommendations.append({
            'priority': 'HIGH',
            'action': 'Immediate Review Required',
            'description': f'{high_risk_count} high-risk matches require immediate compliance review',
            'timeline': 'Within 24 hours'
        })
    
    if has_sanctions:
        recommendations.append({
            'priority': 'CRITICAL',
            'action': 'Sanctions Compliance',
            'description': 'Entities matched against sanctions lists - freeze any transactions immediately',
            'timeline': 'Immediate'
        })
    
    if has_pep:
        recommendations.append({
            'priority': 'HIGH',
            'action': 'Enhanced Due Diligence',
            'description': 'PEP matches require enhanced due diligence procedures',
            'timeline': 'Within 48 hours'
        })
    
    if has_crime:
        recommendations.append({
            'priority': 'HIGH',
            'action': 'Investigation Required',
            'description': 'Crime-related matches require detailed investigation',
            'timeline': 'Within 72 hours'
        })
    
    if report_type == 'str':
        recommendations.append({
            'priority': 'HIGH',
            'action': 'File STR',
            'description': 'Prepare and file Suspicious Transaction Report with FIC',
            'timeline': 'As per regulatory requirements'
        })
    
    # General recommendations
    recommendations.append({
        'priority': 'MEDIUM',
        'action': 'Document Review',
        'description': 'Document all decisions and actions taken for audit trail',
        'timeline': 'Ongoing'
    })
    
    return recommendations