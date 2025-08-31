from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime, timedelta
import json
import uuid
import io
import csv
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response

# Create blueprint with template folder
reports_bp = Blueprint('reports', __name__, 
                       template_folder='templates',
                       static_folder='static')

# Storage for reports (in production, this would be in a database)
reports_storage = {}
schedules_storage = {}

@reports_bp.route('/')
def index():
    """Main reports page"""
    return render_template('reports/index.html')

@reports_bp.route('/api/reports', methods=['GET'])
def get_reports():
    """Get all reports with filtering"""
    try:
        # Get filter parameters
        report_type = request.args.get('type', 'all')
        status = request.args.get('status', 'all')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search', '')
        
        # Get mock data
        reports = get_empty_paginated_response()
        
        # Apply filters
        filtered = reports['data']['reports']
        
        if report_type != 'all':
            filtered = [r for r in filtered if r['type'].lower() == report_type.lower()]
        
        if status != 'all':
            filtered = [r for r in filtered if r['status'].lower() == status.lower()]
        
        if search:
            search_lower = search.lower()
            filtered = [r for r in filtered if 
                       search_lower in r['name'].lower() or 
                       search_lower in r.get('description', '').lower()]
        
        return jsonify({
            'success': True,
            'data': {
                'reports': filtered,
                'total': len(filtered),
                'stats': reports['data']['stats']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    """Get specific report details"""
    try:
        report = get_empty_response()
        return jsonify(report)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate a new report"""
    try:
        data = request.json
        
        # Generate report ID
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create report object
        report = {
            'id': report_id,
            'name': data.get('name'),
            'type': data.get('type'),
            'description': data.get('description'),
            'format': data.get('format', 'pdf'),
            'parameters': data.get('parameters', {}),
            'filters': data.get('filters', {}),
            'status': 'generating',
            'progress': 0,
            'created_date': datetime.now().isoformat(),
            'created_by': data.get('created_by', 'Current User'),
            'scheduled': data.get('scheduled', False),
            'schedule_config': data.get('schedule_config', {}),
            'recipients': data.get('recipients', []),
            'file_path': None,
            'file_size': None,
            'generation_time': None,
            'error': None
        }
        
        # Store report
        reports_storage[report_id] = report
        
        # Simulate report generation (in production, this would be async)
        report['status'] = 'completed'
        report['progress'] = 100
        report['file_path'] = f'/reports/{report_id}.{report["format"]}'
        report['file_size'] = '2.5 MB'
        report['generation_time'] = '3.2 seconds'
        
        return jsonify({
            'success': True,
            'data': report,
            'message': f'Report {report_id} generated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/<report_id>/download', methods=['GET'])
def download_report(report_id):
    """Download a report"""
    try:
        # Get report format from query params
        format_type = request.args.get('format', 'pdf')
        
        # Create sample report content based on format
        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Risk ID', 'Title', 'Category', 'Status', 'Risk Score', 'Owner'])
            
            # Write sample data
            writer.writerow(['RSK-001', 'Data Security Risk', 'Cyber', 'Active', '15', 'John Doe'])
            writer.writerow(['RSK-002', 'Compliance Risk', 'Regulatory', 'Under Review', '8', 'Jane Smith'])
            writer.writerow(['RSK-003', 'Operational Risk', 'Operational', 'Active', '12', 'Bob Johnson'])
            
            # Create BytesIO object
            mem = io.BytesIO()
            mem.write(output.getvalue().encode('utf-8'))
            mem.seek(0)
            
            return send_file(
                mem,
                mimetype='text/csv',
                download_name=f'report_{report_id}.csv',
                as_attachment=True
            )
        
        elif format_type == 'json':
            data = {
                'report_id': report_id,
                'generated_date': datetime.now().isoformat(),
                'data': {
                    'risks': [
                        {'id': 'RSK-001', 'title': 'Data Security Risk', 'score': 15},
                        {'id': 'RSK-002', 'title': 'Compliance Risk', 'score': 8},
                        {'id': 'RSK-003', 'title': 'Operational Risk', 'score': 12}
                    ]
                }
            }
            
            mem = io.BytesIO()
            mem.write(json.dumps(data, indent=2).encode('utf-8'))
            mem.seek(0)
            
            return send_file(
                mem,
                mimetype='application/json',
                download_name=f'report_{report_id}.json',
                as_attachment=True
            )
        
        else:  # Default PDF
            # Create a simple text file as placeholder for PDF
            content = f"""
NAPSA Enterprise Risk Management Report
Report ID: {report_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Executive Summary
=================
This report provides a comprehensive overview of risk management activities.

Risk Overview
=============
- Total Risks: 45
- High Priority: 12
- Medium Priority: 20
- Low Priority: 13

Key Findings
============
1. Cybersecurity risks have increased by 15%
2. Compliance score improved to 92%
3. Operational efficiency up by 8%

Recommendations
===============
1. Enhance security controls
2. Continue compliance monitoring
3. Implement automation for routine tasks
            """
            
            mem = io.BytesIO()
            mem.write(content.encode('utf-8'))
            mem.seek(0)
            
            return send_file(
                mem,
                mimetype='text/plain',
                download_name=f'report_{report_id}.txt',
                as_attachment=True
            )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/<report_id>/schedule', methods=['POST'])
def schedule_report(report_id):
    """Schedule a report for regular generation"""
    try:
        data = request.json
        
        schedule_id = str(uuid.uuid4())
        
        schedule = {
            'id': schedule_id,
            'report_id': report_id,
            'frequency': data.get('frequency', 'weekly'),
            'day_of_week': data.get('day_of_week'),
            'day_of_month': data.get('day_of_month'),
            'time': data.get('time', '08:00'),
            'timezone': data.get('timezone', 'Africa/Lusaka'),
            'recipients': data.get('recipients', []),
            'enabled': data.get('enabled', True),
            'last_run': None,
            'next_run': datetime.now().isoformat(),
            'created_date': datetime.now().isoformat(),
            'created_by': data.get('created_by', 'Current User')
        }
        
        schedules_storage[schedule_id] = schedule
        
        return jsonify({
            'success': True,
            'data': schedule,
            'message': 'Report scheduled successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/templates', methods=['GET'])
def get_report_templates():
    """Get available report templates"""
    try:
        templates = get_empty_paginated_response()
        return jsonify(templates)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/templates/<template_id>', methods=['GET'])
def get_report_template(template_id):
    """Get specific report template"""
    try:
        template = get_empty_response()
        return jsonify(template)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/dashboard', methods=['GET'])
def get_reports_dashboard():
    """Get reports dashboard data"""
    try:
        dashboard = get_empty_stats_response()
        return jsonify(dashboard)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/schedules', methods=['GET'])
def get_schedules():
    """Get all report schedules"""
    try:
        schedules = get_empty_paginated_response()
        return jsonify(schedules)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/schedules/<schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update report schedule"""
    try:
        data = request.json
        
        if schedule_id in schedules_storage:
            schedule = schedules_storage[schedule_id]
        else:
            schedule = {'id': schedule_id}
        
        # Update schedule
        schedule.update({
            'frequency': data.get('frequency', schedule.get('frequency')),
            'time': data.get('time', schedule.get('time')),
            'recipients': data.get('recipients', schedule.get('recipients')),
            'enabled': data.get('enabled', schedule.get('enabled')),
            'modified_date': datetime.now().isoformat(),
            'modified_by': data.get('modified_by', 'Current User')
        })
        
        schedules_storage[schedule_id] = schedule
        
        return jsonify({
            'success': True,
            'data': schedule,
            'message': 'Schedule updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/schedules/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete report schedule"""
    try:
        if schedule_id in schedules_storage:
            del schedules_storage[schedule_id]
        
        return jsonify({
            'success': True,
            'message': 'Schedule deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/<report_id>/share', methods=['POST'])
def share_report(report_id):
    """Share a report with users"""
    try:
        data = request.json
        
        share_data = {
            'report_id': report_id,
            'shared_by': data.get('shared_by', 'Current User'),
            'shared_with': data.get('recipients', []),
            'message': data.get('message', ''),
            'permissions': data.get('permissions', ['view', 'download']),
            'expiry_date': data.get('expiry_date'),
            'shared_date': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': share_data,
            'message': f'Report shared with {len(share_data["shared_with"])} recipients'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/history', methods=['GET'])
def get_report_history():
    """Get report generation history"""
    try:
        history = get_empty_paginated_response()
        return jsonify(history)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/api/reports/analytics', methods=['GET'])
def get_report_analytics():
    """Get report analytics"""
    try:
        analytics = get_empty_stats_response()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500