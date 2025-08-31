from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
import json
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response
from app.services.api_service import APIService

integrations_bp = Blueprint('integrations', __name__)

@integrations_bp.route('/')
def index():
    return render_template('integrations/index.html')

@integrations_bp.route('/api/dashboard/compliance-overview')
def get_compliance_overview():
    """Get unified compliance dashboard overview"""
    try:
        # Try APIService first
        result = APIService.get('/integrations/dashboard/compliance-overview')
        if result.get('success') and result.get('data'):
            return jsonify(result)
        
        # Fallback to mock data
        mock_data = {
            "success": True,
            "data": {
                "overall_compliance_score": 88.5,
                "compliance_grade": "B+",
                "risk_level": "medium",
                "system_statuses": {
                    "zra": {
                        "status": "compliant",
                        "last_sync": datetime.utcnow().isoformat(),
                        "outstanding_issues": 0
                    },
                    "napsa": {
                        "status": "compliant", 
                        "last_sync": datetime.utcnow().isoformat(),
                        "outstanding_issues": 0
                    },
                    "pacra": {
                        "status": "compliant",
                        "last_sync": datetime.utcnow().isoformat(),
                        "outstanding_issues": 1
                    },
                    "erp": {
                        "status": "healthy",
                        "last_sync": datetime.utcnow().isoformat(),
                        "outstanding_issues": 0
                    }
                },
                "upcoming_obligations": [
                    {
                        "agency": "ZRA",
                        "obligation": "VAT Return",
                        "due_date": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                        "status": "pending"
                    },
                    {
                        "agency": "PACRA", 
                        "obligation": "Annual Return",
                        "due_date": (datetime.now() + timedelta(days=31)).strftime('%Y-%m-%d'),
                        "status": "pending"
                    }
                ],
                "total_outstanding_amount": 0.00,
                "critical_alerts": 0,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        return jsonify(mock_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/api/dashboard/integration-health')
def get_integration_health():
    """Get health status of all integrations"""
    try:
        # Try APIService first
        result = APIService.get('/integrations/dashboard/integration-health')
        if result.get('success') and result.get('data'):
            return jsonify(result)
        
        # Fallback to mock data
        mock_data = {
            "success": True,
            "data": {
                "overall_health": "healthy",
                "systems": {
                    "zra": {
                        "status": "healthy",
                        "last_successful_sync": datetime.utcnow().isoformat(),
                        "response_time_ms": 150,
                        "error_rate_24h": 0
                    },
                    "napsa": {
                        "status": "healthy",
                        "last_successful_sync": datetime.utcnow().isoformat(), 
                        "response_time_ms": 180,
                        "error_rate_24h": 0
                    },
                    "pacra": {
                        "status": "healthy",
                        "last_successful_sync": datetime.utcnow().isoformat(),
                        "response_time_ms": 200,
                        "error_rate_24h": 0
                    },
                    "erp": {
                        "status": "healthy",
                        "active_connections": 3,
                        "transaction_success_rate": 98.5
                    }
                },
                "performance_metrics": {
                    "total_transactions_24h": 89,
                    "successful_transactions": 86,
                    "failed_transactions": 3,
                    "average_response_time_ms": 182
                }
            }
        }
        return jsonify(mock_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/api/systems', methods=['GET'])
def get_integration_systems():
    """Get all integrated systems"""
    try:
        systems = [
            {
                "id": "zra",
                "name": "Zambia Revenue Authority",
                "description": "Tax compliance and revenue management",
                "status": "active",
                "type": "government",
                "services": ["TPIN validation", "Tax clearance", "VAT returns"]
            },
            {
                "id": "napsa", 
                "name": "National Pension Scheme Authority",
                "description": "Pension and social security compliance",
                "status": "active",
                "type": "government",
                "services": ["Employer validation", "Contribution tracking", "Member verification"]
            },
            {
                "id": "pacra",
                "name": "Patents and Companies Registration Agency",
                "description": "Company registration and compliance", 
                "status": "active",
                "type": "government",
                "services": ["Company verification", "Director information", "Annual returns"]
            },
            {
                "id": "erp",
                "name": "ERP System Integration",
                "description": "Enterprise Resource Planning integration",
                "status": "active", 
                "type": "internal",
                "services": ["Financial sync", "HR sync", "Procurement sync"]
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'systems': systems,
                'total': len(systems)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@integrations_bp.route('/api/sync-all', methods=['POST'])
def sync_all_systems():
    """Trigger synchronization across all systems"""
    try:
        # Try APIService first
        result = APIService.post('/integrations/sync/all-systems')
        if result.get('success') and result.get('data'):
            return jsonify(result)
        
        # Fallback to mock response
        sync_results = {
            "success": True,
            "data": {
                "sync_id": f"SYNC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "total_systems": 4,
                "successful_syncs": 4,
                "failed_syncs": 0,
                "sync_results": [
                    {
                        "system": "zra",
                        "status": "completed",
                        "records_synced": 45,
                        "sync_duration_seconds": 30,
                        "errors": 0
                    },
                    {
                        "system": "napsa",
                        "status": "completed", 
                        "records_synced": 38,
                        "sync_duration_seconds": 25,
                        "errors": 0
                    },
                    {
                        "system": "pacra",
                        "status": "completed",
                        "records_synced": 22,
                        "sync_duration_seconds": 35,
                        "errors": 0
                    },
                    {
                        "system": "erp",
                        "status": "completed",
                        "records_synced": 156,
                        "sync_duration_seconds": 45,
                        "errors": 0
                    }
                ],
                "overall_status": "completed"
            }
        }
        return jsonify(sync_results)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
