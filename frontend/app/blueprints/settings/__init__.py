from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
import json
import os
from app.services.empty_service import get_empty_response, get_empty_paginated_response, get_empty_stats_response

# Create blueprint with template folder
settings_bp = Blueprint('settings', __name__, 
                        template_folder='templates',
                        static_folder='static')

# Settings storage (in production, this would be in a database)
SETTINGS_FILE = '/tmp/napsa_erm_settings.json'
settings_storage = {}

def load_settings():
    """Load settings from file"""
    global settings_storage
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings_storage = json.load(f)
        else:
            settings_storage = {}
    except Exception as e:
        print(f"Error loading settings: {e}")
        settings_storage = {}

def save_settings():
    """Save settings to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_storage, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# Load settings on module import
load_settings()

@settings_bp.route('/')
def index():
    """Main settings page"""
    return render_template('settings/index.html')

@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all settings"""
    try:
        category = request.args.get('category', 'all')
        
        if category == 'all':
            return jsonify({
                'success': True,
                'data': settings_storage
            })
        else:
            category_settings = settings_storage.get(category, {})
            return jsonify({
                'success': True,
                'data': {category: category_settings}
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/settings/<category>', methods=['PUT'])
def update_category_settings(category):
    """Update settings for specific category"""
    try:
        data = request.json
        
        # Update settings
        if category not in settings_storage:
            settings_storage[category] = {}
        
        settings_storage[category].update(data)
        settings_storage[category]['last_modified'] = datetime.now().isoformat()
        settings_storage[category]['modified_by'] = data.get('modified_by', 'Current User')
        
        # Save to file
        if save_settings():
            return jsonify({
                'success': True,
                'data': settings_storage[category],
                'message': f'Settings for {category} updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save settings'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/settings/reset', methods=['POST'])
def reset_settings():
    """Reset settings to default values"""
    try:
        data = request.json
        category = data.get('category', 'all')
        
        if category == 'all':
            # Reset all settings
            global settings_storage
            settings_storage = {}
        else:
            # Reset specific category
            if category in settings_storage:
                settings_storage[category] = {}
        
        # Save to file
        if save_settings():
            return jsonify({
                'success': True,
                'data': settings_storage if category == 'all' else settings_storage.get(category, {}),
                'message': f'Settings {"" if category == "all" else "for " + category} reset to defaults'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save settings'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/settings/export', methods=['POST'])
def export_settings():
    """Export settings to file"""
    try:
        data = request.json
        format_type = data.get('format', 'json')
        category = data.get('category', 'all')
        
        export_data = settings_storage if category == 'all' else {category: settings_storage.get(category, {})}
        
        if format_type == 'json':
            return jsonify({
                'success': True,
                'data': {
                    'content': json.dumps(export_data, indent=2, default=str),
                    'filename': f'napsa_erm_settings_{category}_{datetime.now().strftime("%Y%m%d")}.json',
                    'content_type': 'application/json'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported format'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/settings/backup', methods=['POST'])
def backup_settings():
    """Create settings backup"""
    try:
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'settings': settings_storage,
            'version': '1.0',
            'system': 'NAPSA ERM'
        }
        
        backup_filename = f'napsa_erm_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return jsonify({
            'success': True,
            'data': {
                'backup_id': f'BKP-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
                'filename': backup_filename,
                'content': json.dumps(backup_data, indent=2, default=str),
                'size': len(json.dumps(backup_data)),
                'created_date': datetime.now().isoformat()
            },
            'message': 'Settings backup created successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500