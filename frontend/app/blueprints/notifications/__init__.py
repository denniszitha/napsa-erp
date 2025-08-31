from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for, current_app
from datetime import datetime
import requests
from typing import Dict, List, Any
import json
from app.services.api_service import APIService

# Create blueprint
notifications_bp = Blueprint('notifications', __name__, 
                            template_folder='templates',
                            static_folder='static')

@notifications_bp.route('/')
def index():
    """Main notifications management page"""
    return render_template('notifications/index.html')

@notifications_bp.route('/api/send', methods=['POST'])
def send_notification():
    """Send a general notification"""
    try:
        data = request.json
        
        # Prepare request for backend
        notification_data = {
            "recipients": data.get('recipients', {}),
            "subject": data.get('subject', ''),
            "message": data.get('message', ''),
            "notification_type": data.get('notification_type', 'general'),
            "priority": data.get('priority', 'normal'),
            "html_body": data.get('html_body')
        }
        
        # Use APIService to send to backend with auth
        result = APIService.post('/notifications/send', notification_data)
        return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/test', methods=['POST'])
def test_notification():
    """Test notification system"""
    try:
        data = request.json
        
        test_data = {
            "email": data.get('email'),
            "phone": data.get('phone')
        }
        
        # Use APIService with auth
        result = APIService.post('/notifications/test', test_data)
        return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/status')
def get_notification_status():
    """Get notification system status"""
    try:
        # Try with APIService first (handles authentication)
        result = APIService.get('/notifications/status')
        if result.get('success'):
            return jsonify(result)
        
        # If auth fails, try direct connection (for testing)
        import requests
        direct_response = requests.get('http://localhost:58001/api/v1/notifications/status')
        if direct_response.status_code == 200:
            return jsonify(direct_response.json())
        
        return jsonify(result)
    except Exception as e:
        # Fallback to direct connection
        try:
            import requests
            direct_response = requests.get('http://localhost:58001/api/v1/notifications/status')
            if direct_response.status_code == 200:
                return jsonify(direct_response.json())
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/kri-alert', methods=['POST'])
def send_kri_alert():
    """Send KRI breach alert"""
    try:
        data = request.json
        
        kri_data = {
            "kri_name": data.get('kri_name'),
            "current_value": float(data.get('current_value', 0)),
            "threshold": float(data.get('threshold', 0)),
            "status": data.get('status', 'warning'),
            "risk_title": data.get('risk_title'),
            "recipients": data.get('recipients', {})
        }
        
        # Use APIService with auth
        result = APIService.post('/notifications/kri-alert', kri_data)
        return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/incident-alert', methods=['POST'])
def send_incident_alert():
    """Send incident alert"""
    try:
        data = request.json
        
        incident_data = {
            "incident_title": data.get('incident_title'),
            "severity": data.get('severity', 'medium'),
            "description": data.get('description'),
            "recipients": data.get('recipients', {})
        }
        
        # Use APIService with auth
        result = APIService.post('/notifications/incident-alert', incident_data)
        return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/aml-alert', methods=['POST'])
def send_aml_alert():
    """Send AML screening alert"""
    try:
        data = request.json
        
        aml_data = {
            "customer_name": data.get('customer_name'),
            "match_type": data.get('match_type'),
            "risk_score": float(data.get('risk_score', 0)),
            "match_details": data.get('match_details'),
            "recipients": data.get('recipients', {})
        }
        
        # Use APIService with auth
        result = APIService.post('/notifications/aml-alert', aml_data)
        return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/policy-notification', methods=['POST'])
def send_policy_notification():
    """Send policy management notification"""
    try:
        data = request.json
        
        policy_data = {
            "policy_title": data.get('policy_title'),
            "action": data.get('action'),
            "approver": data.get('approver'),
            "recipients": data.get('recipients', {})
        }
        
        # Use APIService with auth
        result = APIService.post('/notifications/policy-notification', policy_data)
        return jsonify(result)
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Utility functions for easy notification sending
def send_automated_kri_alert(kri_name: str, current_value: float, threshold: float, 
                           status: str, risk_title: str, email_list: List[str], 
                           sms_list: List[str] = None):
    """Helper function to send KRI alerts programmatically"""
    try:
        from flask import current_app
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        recipients = {
            'email': email_list,
            'sms': sms_list or []
        }
        
        response = requests.post(
            f"{backend_url}/notifications/kri-alert",
            json={
                "kri_name": kri_name,
                "current_value": current_value,
                "threshold": threshold,
                "status": status,
                "risk_title": risk_title,
                "recipients": recipients
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        return response.json() if response.status_code == 200 else None
        
    except Exception as e:
        print(f"Error sending automated KRI alert: {str(e)}")
        return None

def send_automated_aml_alert(customer_name: str, match_type: str, risk_score: float,
                           match_details: str, email_list: List[str], 
                           sms_list: List[str] = None):
    """Helper function to send AML alerts programmatically"""
    try:
        from flask import current_app
        backend_url = current_app.config.get('API_BASE_URL', 'http://localhost:58001/api/v1')
        recipients = {
            'email': email_list,
            'sms': sms_list or []
        }
        
        response = requests.post(
            f"{backend_url}/notifications/aml-alert",
            json={
                "customer_name": customer_name,
                "match_type": match_type,
                "risk_score": risk_score,
                "match_details": match_details,
                "recipients": recipients
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        return response.json() if response.status_code == 200 else None
        
    except Exception as e:
        print(f"Error sending automated AML alert: {str(e)}")
        return None

@notifications_bp.route('/api/history')
def get_notification_history():
    """Get notification history from backend"""
    try:
        # Try with APIService first
        result = APIService.get('/notifications/history')
        if result.get('success'):
            return jsonify(result)
        
        # Fallback to direct connection
        import requests
        direct_response = requests.get('http://localhost:58001/api/v1/notifications/history?limit=20')
        if direct_response.status_code == 200:
            return jsonify(direct_response.json())
        
        return jsonify(result)
    except Exception as e:
        # Fallback to direct connection
        try:
            import requests
            direct_response = requests.get('http://localhost:58001/api/v1/notifications/history?limit=20')
            if direct_response.status_code == 200:
                return jsonify(direct_response.json())
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500