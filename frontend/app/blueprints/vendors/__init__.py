from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime, timedelta
import json
import uuid
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response

# Create blueprint with template folder
vendors_bp = Blueprint('vendors', __name__, 
                      template_folder='templates',
                      static_folder='static')

# Storage for vendors (in production, this would be in a database)
vendors_storage = {}
contracts_storage = {}
evaluations_storage = {}

@vendors_bp.route('/')
def index():
    """Main vendor management page"""
    return render_template('vendors/index.html')

@vendors_bp.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Get all vendors with filtering"""
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        category = request.args.get('category', 'all')
        risk_level = request.args.get('risk_level', 'all')
        search = request.args.get('search', '')
        
        # Get mock data
        vendors = get_empty_paginated_response()
        
        # Apply filters
        filtered = vendors['data']['vendors']
        
        if status != 'all':
            filtered = [v for v in filtered if v['status'].lower() == status.lower()]
        
        if category != 'all':
            filtered = [v for v in filtered if v['category'].lower() == category.lower()]
        
        if risk_level != 'all':
            filtered = [v for v in filtered if v['risk_level'].lower() == risk_level.lower()]
        
        if search:
            search_lower = search.lower()
            filtered = [v for v in filtered if 
                       search_lower in v['name'].lower() or 
                       search_lower in v.get('description', '').lower()]
        
        return jsonify({
            'success': True,
            'data': {
                'vendors': filtered,
                'total': len(filtered),
                'stats': vendors['data']['stats']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    """Get specific vendor details"""
    try:
        vendor = get_empty_response()
        return jsonify(vendor)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors', methods=['POST'])
def create_vendor():
    """Create new vendor"""
    try:
        data = request.json
        
        # Generate vendor ID
        vendor_id = f"VEN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create vendor object
        vendor = {
            'id': vendor_id,
            'name': data.get('name'),
            'category': data.get('category'),
            'description': data.get('description'),
            'contact_person': data.get('contact_person'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'address': data.get('address'),
            'country': data.get('country', 'Zambia'),
            'tax_id': data.get('tax_id'),
            'registration_number': data.get('registration_number'),
            'status': 'pending_approval',
            'risk_level': data.get('risk_level', 'medium'),
            'payment_terms': data.get('payment_terms', 'Net 30'),
            'bank_details': data.get('bank_details', {}),
            'certifications': data.get('certifications', []),
            'insurance_coverage': data.get('insurance_coverage', {}),
            'created_date': datetime.now().isoformat(),
            'created_by': data.get('created_by', 'Current User'),
            'last_modified': datetime.now().isoformat(),
            'compliance_status': 'pending',
            'performance_score': None,
            'contracts': [],
            'evaluations': [],
            'documents': []
        }
        
        # Store vendor
        vendors_storage[vendor_id] = vendor
        
        return jsonify({
            'success': True,
            'data': vendor,
            'message': f'Vendor {vendor_id} created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>', methods=['PUT'])
def update_vendor(vendor_id):
    """Update existing vendor"""
    try:
        data = request.json
        
        # Get existing vendor or create mock
        if vendor_id in vendors_storage:
            vendor = vendors_storage[vendor_id]
        else:
            vendor = get_empty_response()['data']
        
        # Update fields
        vendor.update({
            'name': data.get('name', vendor.get('name')),
            'category': data.get('category', vendor.get('category')),
            'description': data.get('description', vendor.get('description')),
            'contact_person': data.get('contact_person', vendor.get('contact_person')),
            'email': data.get('email', vendor.get('email')),
            'phone': data.get('phone', vendor.get('phone')),
            'address': data.get('address', vendor.get('address')),
            'status': data.get('status', vendor.get('status')),
            'risk_level': data.get('risk_level', vendor.get('risk_level')),
            'last_modified': datetime.now().isoformat(),
            'modified_by': data.get('modified_by', 'Current User')
        })
        
        # Store updated vendor
        vendors_storage[vendor_id] = vendor
        
        return jsonify({
            'success': True,
            'data': vendor,
            'message': f'Vendor {vendor_id} updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/approve', methods=['POST'])
def approve_vendor(vendor_id):
    """Approve a vendor"""
    try:
        data = request.json
        approver = data.get('approver', 'Current User')
        comments = data.get('comments', '')
        
        approval = {
            'vendor_id': vendor_id,
            'approver': approver,
            'date': datetime.now().isoformat(),
            'action': 'approved',
            'comments': comments,
            'status': 'active'
        }
        
        return jsonify({
            'success': True,
            'data': approval,
            'message': f'Vendor {vendor_id} approved successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/suspend', methods=['POST'])
def suspend_vendor(vendor_id):
    """Suspend a vendor"""
    try:
        data = request.json
        reason = data.get('reason', '')
        
        suspension = {
            'vendor_id': vendor_id,
            'suspended_by': data.get('suspended_by', 'Current User'),
            'date': datetime.now().isoformat(),
            'reason': reason,
            'status': 'suspended'
        }
        
        return jsonify({
            'success': True,
            'data': suspension,
            'message': f'Vendor {vendor_id} suspended'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/risk-assessment', methods=['POST'])
def assess_vendor_risk(vendor_id):
    """Perform vendor risk assessment"""
    try:
        data = request.json
        
        assessment = get_empty_response()
        
        return jsonify(assessment)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/performance', methods=['GET'])
def get_vendor_performance(vendor_id):
    """Get vendor performance metrics"""
    try:
        performance = get_empty_stats_response()
        return jsonify(performance)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/contracts', methods=['GET'])
def get_vendor_contracts(vendor_id):
    """Get vendor contracts"""
    try:
        contracts = get_empty_paginated_response()
        return jsonify(contracts)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/contracts', methods=['POST'])
def create_contract(vendor_id):
    """Create new contract for vendor"""
    try:
        data = request.json
        
        contract_id = f"CON-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        contract = {
            'id': contract_id,
            'vendor_id': vendor_id,
            'contract_number': data.get('contract_number', contract_id),
            'title': data.get('title'),
            'description': data.get('description'),
            'type': data.get('type', 'service'),
            'value': data.get('value'),
            'currency': data.get('currency', 'ZMW'),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
            'renewal_terms': data.get('renewal_terms'),
            'payment_terms': data.get('payment_terms'),
            'deliverables': data.get('deliverables', []),
            'sla_terms': data.get('sla_terms', []),
            'penalties': data.get('penalties', []),
            'status': 'draft',
            'created_date': datetime.now().isoformat(),
            'created_by': data.get('created_by', 'Current User')
        }
        
        contracts_storage[contract_id] = contract
        
        return jsonify({
            'success': True,
            'data': contract,
            'message': f'Contract {contract_id} created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/evaluation', methods=['POST'])
def evaluate_vendor(vendor_id):
    """Perform vendor evaluation"""
    try:
        data = request.json
        
        evaluation_id = str(uuid.uuid4())
        
        evaluation = {
            'id': evaluation_id,
            'vendor_id': vendor_id,
            'evaluation_date': datetime.now().isoformat(),
            'evaluator': data.get('evaluator', 'Current User'),
            'period': data.get('period'),
            'criteria': data.get('criteria', {}),
            'scores': {
                'quality': data.get('quality_score', 0),
                'delivery': data.get('delivery_score', 0),
                'cost': data.get('cost_score', 0),
                'communication': data.get('communication_score', 0),
                'compliance': data.get('compliance_score', 0)
            },
            'overall_score': data.get('overall_score', 0),
            'rating': data.get('rating'),
            'strengths': data.get('strengths', []),
            'improvements': data.get('improvements', []),
            'recommendations': data.get('recommendations', ''),
            'action_items': data.get('action_items', [])
        }
        
        evaluations_storage[evaluation_id] = evaluation
        
        return jsonify({
            'success': True,
            'data': evaluation,
            'message': 'Vendor evaluation completed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/compliance', methods=['GET'])
def get_vendor_compliance(vendor_id):
    """Get vendor compliance status"""
    try:
        compliance = get_empty_response()
        return jsonify(compliance)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/documents', methods=['GET'])
def get_vendor_documents(vendor_id):
    """Get vendor documents"""
    try:
        documents = get_empty_paginated_response()
        return jsonify(documents)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/<vendor_id>/documents', methods=['POST'])
def upload_vendor_document(vendor_id):
    """Upload vendor document"""
    try:
        data = request.json
        
        document = {
            'id': str(uuid.uuid4()),
            'vendor_id': vendor_id,
            'name': data.get('name'),
            'type': data.get('type'),
            'description': data.get('description'),
            'file_name': data.get('file_name'),
            'file_size': data.get('file_size'),
            'uploaded_date': datetime.now().isoformat(),
            'uploaded_by': data.get('uploaded_by', 'Current User'),
            'expiry_date': data.get('expiry_date'),
            'status': 'active'
        }
        
        return jsonify({
            'success': True,
            'data': document,
            'message': 'Document uploaded successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/stats', methods=['GET'])
def get_vendor_stats():
    """Get vendor statistics"""
    try:
        stats = get_empty_stats_response()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/dashboard', methods=['GET'])
def get_vendor_dashboard():
    """Get vendor dashboard data"""
    try:
        dashboard = get_empty_stats_response()
        return jsonify(dashboard)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/due-diligence/<vendor_id>', methods=['POST'])
def perform_due_diligence(vendor_id):
    """Perform vendor due diligence"""
    try:
        data = request.json
        
        due_diligence = get_empty_response()
        
        return jsonify(due_diligence)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendors_bp.route('/api/vendors/spend-analysis', methods=['GET'])
def get_spend_analysis():
    """Get vendor spend analysis"""
    try:
        analysis = get_empty_stats_response()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500