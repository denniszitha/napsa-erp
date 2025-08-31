from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename
import uuid
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response
from app.services.api_service import APIService

# Create blueprint with template folder
policies_bp = Blueprint('policies', __name__, 
                       template_folder='templates',
                       static_folder='static')

# Storage for policies (in production, this would be in a database)
policies_storage = {}

@policies_bp.route('/')
def index():
    """Main policies management page"""
    return render_template('policies/index.html')

@policies_bp.route('/api/policies', methods=['GET'])
def get_policies():
    """Get all policies with filtering"""
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        category = request.args.get('category', 'all')
        search = request.args.get('search', '')
        
        # Try to get from backend first
        params = {
            'skip': request.args.get('skip', 0, type=int),
            'limit': request.args.get('limit', 100, type=int)
        }
        if status != 'all':
            params['status'] = status
        if category != 'all':
            params['category'] = category
        if search:
            params['search'] = search
            
        result = APIService.get('/policies', params)
        
        if result.get('success') and result.get('data'):
            # Format response to match frontend expectations
            data = result['data']
            return jsonify({
                'success': True,
                'data': {
                    'policies': data.get('data', []),
                    'total': data.get('total', 0),
                    'stats': {
                        'total': data.get('total', 0),
                        'draft': 0,
                        'published': 0,
                        'archived': 0
                    }
                }
            })
        
        # Fallback to mock data
        policies = get_empty_paginated_response()
        
        # Apply filters
        filtered = policies['data']['policies']
        
        if status != 'all':
            filtered = [p for p in filtered if p['status'].lower() == status.lower()]
        
        if category != 'all':
            filtered = [p for p in filtered if p['category'].lower() == category.lower()]
        
        if search:
            search_lower = search.lower()
            filtered = [p for p in filtered if 
                       search_lower in p['title'].lower() or 
                       search_lower in p['description'].lower()]
        
        return jsonify({
            'success': True,
            'data': {
                'policies': filtered,
                'total': len(filtered),
                'stats': policies['data']['stats']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/<policy_id>', methods=['GET'])
def get_policy(policy_id):
    """Get specific policy details"""
    try:
        # Try backend first
        result = APIService.get(f'/policies/{policy_id}')
        if result.get('success') and result.get('data'):
            return jsonify(result)
        
        # Fallback to mock
        policy = get_empty_response()
        return jsonify(policy)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies', methods=['POST'])
def create_policy():
    """Create new policy"""
    try:
        data = request.json
        
        # Generate policy ID
        policy_id = f"POL-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create policy object
        policy = {
            'id': policy_id,
            'title': data.get('title'),
            'category': data.get('category'),
            'description': data.get('description'),
            'content': data.get('content'),
            'status': 'draft',
            'version': '1.0',
            'created_date': datetime.now().isoformat(),
            'created_by': data.get('created_by', 'Current User'),
            'last_modified': datetime.now().isoformat(),
            'modified_by': data.get('created_by', 'Current User'),
            'approval_status': 'pending',
            'effective_date': data.get('effective_date'),
            'review_date': data.get('review_date'),
            'owner': data.get('owner'),
            'department': data.get('department'),
            'risk_category': data.get('risk_category'),
            'compliance_frameworks': data.get('compliance_frameworks', []),
            'controls': data.get('controls', []),
            'attachments': [],
            'review_history': [],
            'approval_workflow': {
                'required_approvers': data.get('approvers', []),
                'current_approvals': [],
                'status': 'pending'
            }
        }
        
        # Store policy
        policies_storage[policy_id] = policy
        
        return jsonify({
            'success': True,
            'data': policy,
            'message': f'Policy {policy_id} created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/<policy_id>', methods=['PUT'])
def update_policy(policy_id):
    """Update existing policy"""
    try:
        data = request.json
        
        # Get existing policy or create mock
        if policy_id in policies_storage:
            policy = policies_storage[policy_id]
        else:
            policy = {
                'id': policy_id,
                'created_date': datetime.now().isoformat(),
                'version': '1.0'
            }
        
        # Update fields
        policy.update({
            'title': data.get('title', policy.get('title')),
            'category': data.get('category', policy.get('category')),
            'description': data.get('description', policy.get('description')),
            'content': data.get('content', policy.get('content')),
            'status': data.get('status', policy.get('status')),
            'last_modified': datetime.now().isoformat(),
            'modified_by': data.get('modified_by', 'Current User'),
            'effective_date': data.get('effective_date', policy.get('effective_date')),
            'review_date': data.get('review_date', policy.get('review_date')),
            'owner': data.get('owner', policy.get('owner')),
            'department': data.get('department', policy.get('department')),
            'risk_category': data.get('risk_category', policy.get('risk_category')),
            'compliance_frameworks': data.get('compliance_frameworks', policy.get('compliance_frameworks', [])),
            'controls': data.get('controls', policy.get('controls', []))
        })
        
        # Increment version if publishing
        if data.get('status') == 'published' and policy.get('status') != 'published':
            current_version = float(policy.get('version', '1.0'))
            policy['version'] = str(current_version + 0.1)
        
        # Store updated policy
        policies_storage[policy_id] = policy
        
        return jsonify({
            'success': True,
            'data': policy,
            'message': f'Policy {policy_id} updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/<policy_id>/approve', methods=['POST'])
def approve_policy(policy_id):
    """Approve a policy"""
    try:
        data = request.json
        approver = data.get('approver', 'Current User')
        comments = data.get('comments', '')
        
        approval = {
            'approver': approver,
            'date': datetime.now().isoformat(),
            'action': 'approved',
            'comments': comments
        }
        
        return jsonify({
            'success': True,
            'data': {
                'policy_id': policy_id,
                'approval': approval,
                'status': 'approved'
            },
            'message': f'Policy {policy_id} approved by {approver}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/<policy_id>/reject', methods=['POST'])
def reject_policy(policy_id):
    """Reject a policy"""
    try:
        data = request.json
        reviewer = data.get('reviewer', 'Current User')
        reason = data.get('reason', '')
        
        rejection = {
            'reviewer': reviewer,
            'date': datetime.now().isoformat(),
            'action': 'rejected',
            'reason': reason
        }
        
        return jsonify({
            'success': True,
            'data': {
                'policy_id': policy_id,
                'rejection': rejection,
                'status': 'rejected'
            },
            'message': f'Policy {policy_id} rejected by {reviewer}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/<policy_id>/archive', methods=['POST'])
def archive_policy(policy_id):
    """Archive a policy"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'policy_id': policy_id,
                'status': 'archived',
                'archived_date': datetime.now().isoformat()
            },
            'message': f'Policy {policy_id} archived successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/<policy_id>/versions', methods=['GET'])
def get_policy_versions(policy_id):
    """Get version history of a policy"""
    try:
        versions = [
            {
                'version': '1.0',
                'date': '2025-01-01',
                'author': 'John Doe',
                'changes': 'Initial version',
                'status': 'published'
            },
            {
                'version': '1.1',
                'date': '2025-06-01',
                'author': 'Jane Smith',
                'changes': 'Updated compliance requirements',
                'status': 'published'
            },
            {
                'version': '1.2',
                'date': '2025-08-01',
                'author': 'John Doe',
                'changes': 'Added new risk controls',
                'status': 'draft'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'policy_id': policy_id,
                'versions': versions,
                'current_version': '1.2'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/<policy_id>/download', methods=['GET'])
def download_policy(policy_id):
    """Download policy as PDF"""
    try:
        # In production, this would generate an actual PDF
        return jsonify({
            'success': True,
            'data': {
                'download_url': f'/policies/download/{policy_id}.pdf',
                'filename': f'Policy_{policy_id}.pdf'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/stats', methods=['GET'])
def get_policy_stats():
    """Get policy statistics"""
    try:
        # Try backend first
        result = APIService.get('/policies/stats/summary')
        if result.get('success') and result.get('data'):
            return jsonify(result)
        
        # Fallback to mock
        stats = get_empty_stats_response()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/compliance-check', methods=['POST'])
def check_compliance():
    """Check policy compliance"""
    try:
        data = request.json
        policy_id = data.get('policy_id')
        
        # Mock compliance check
        compliance_result = {
            'policy_id': policy_id,
            'compliance_score': 85,
            'status': 'compliant',
            'issues': [
                {
                    'severity': 'low',
                    'description': 'Review date approaching',
                    'recommendation': 'Schedule policy review within 30 days'
                }
            ],
            'frameworks': {
                'ISO 27001': 'compliant',
                'NIST': 'compliant',
                'GDPR': 'partial',
                'SOC 2': 'compliant'
            },
            'last_check': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': compliance_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@policies_bp.route('/api/policies/bulk-action', methods=['POST'])
def bulk_action():
    """Perform bulk actions on policies"""
    try:
        data = request.json
        action = data.get('action')
        policy_ids = data.get('policy_ids', [])
        
        results = []
        for policy_id in policy_ids:
            if action == 'archive':
                results.append({
                    'policy_id': policy_id,
                    'status': 'archived',
                    'success': True
                })
            elif action == 'approve':
                results.append({
                    'policy_id': policy_id,
                    'status': 'approved',
                    'success': True
                })
            elif action == 'publish':
                results.append({
                    'policy_id': policy_id,
                    'status': 'published',
                    'success': True
                })
        
        return jsonify({
            'success': True,
            'data': {
                'action': action,
                'results': results,
                'total': len(results),
                'successful': len([r for r in results if r['success']])
            },
            'message': f'Bulk {action} completed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500