"""
Organizational Units Blueprint - Manage NAPSA organizational structure
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.utils.auth import login_required, get_current_user
import requests
from config import Config

organizational_units_bp = Blueprint('organizational_units', __name__)

API_BASE_URL = Config.API_BASE_URL

@organizational_units_bp.route('/')
@login_required
def index():
    """List all organizational units"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/organizational-units', headers=headers)
        units = response.json() if response.status_code == 200 else []
        
        return render_template('organizational_units/index.html', units=units)
    except Exception as e:
        flash(f'Error loading organizational units: {str(e)}', 'danger')
        return render_template('organizational_units/index.html', units=[])

@organizational_units_bp.route('/tree')
@login_required
def tree_view():
    """Display organizational units in tree structure"""
    return render_template('organizational_units/tree.html')

@organizational_units_bp.route('/api/tree')
@login_required
def api_tree():
    """Get organizational units tree structure"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/organizational-units/tree', headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({'error': 'Failed to fetch tree structure'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organizational_units_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new organizational unit"""
    if request.method == 'POST':
        try:
            headers = {'Content-Type': 'application/json'}
            if hasattr(current_user, 'get_auth_token'):
                headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
            
            data = request.get_json() if request.is_json else request.form.to_dict()
            response = requests.post(f'{API_BASE_URL}/organizational-units', json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                flash('Organizational unit created successfully', 'success')
                return jsonify({'success': True})
            else:
                return jsonify({'error': response.text}), response.status_code
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET request - show create form
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        # Get parent units for dropdown
        response = requests.get(f'{API_BASE_URL}/organizational-units', headers=headers)
        parent_units = response.json() if response.status_code == 200 else []
        
        return render_template('organizational_units/create.html', parent_units=parent_units)
    except:
        return render_template('organizational_units/create.html', parent_units=[])

@organizational_units_bp.route('/<int:unit_id>')
@login_required
def view(unit_id):
    """View organizational unit details"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/organizational-units/{unit_id}', headers=headers)
        if response.status_code == 200:
            unit = response.json()
            
            # Get child units
            children_response = requests.get(
                f'{API_BASE_URL}/organizational-units/{unit_id}/children',
                headers=headers
            )
            children = children_response.json() if children_response.status_code == 200 else []
            
            return render_template('organizational_units/view.html', unit=unit, children=children)
        else:
            flash('Organizational unit not found', 'warning')
            return redirect(url_for('organizational_units.index'))
    except Exception as e:
        flash(f'Error loading organizational unit: {str(e)}', 'danger')
        return redirect(url_for('organizational_units.index'))

@organizational_units_bp.route('/<int:unit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(unit_id):
    """Edit organizational unit"""
    if request.method == 'POST':
        try:
            headers = {'Content-Type': 'application/json'}
            if hasattr(current_user, 'get_auth_token'):
                headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
            
            data = request.get_json() if request.is_json else request.form.to_dict()
            response = requests.put(f'{API_BASE_URL}/organizational-units/{unit_id}', json=data, headers=headers)
            
            if response.status_code == 200:
                flash('Organizational unit updated successfully', 'success')
                return jsonify({'success': True})
            else:
                return jsonify({'error': response.text}), response.status_code
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET request - show edit form
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/organizational-units/{unit_id}', headers=headers)
        if response.status_code == 200:
            unit = response.json()
            
            # Get all units for parent dropdown
            units_response = requests.get(f'{API_BASE_URL}/organizational-units', headers=headers)
            all_units = units_response.json() if units_response.status_code == 200 else []
            
            # Filter out current unit and its children from parent options
            parent_units = [u for u in all_units if u['id'] != unit_id]
            
            return render_template('organizational_units/edit.html', unit=unit, parent_units=parent_units)
        else:
            flash('Organizational unit not found', 'warning')
            return redirect(url_for('organizational_units.index'))
    except Exception as e:
        flash(f'Error loading organizational unit: {str(e)}', 'danger')
        return redirect(url_for('organizational_units.index'))

@organizational_units_bp.route('/<int:unit_id>/delete', methods=['POST'])
@login_required
def delete(unit_id):
    """Delete organizational unit"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.delete(f'{API_BASE_URL}/organizational-units/{unit_id}', headers=headers)
        
        if response.status_code in [200, 204]:
            flash('Organizational unit deleted successfully', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'error': response.text}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@organizational_units_bp.route('/<int:unit_id>/staff')
@login_required
def staff(unit_id):
    """View staff members in organizational unit"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        # Get unit details
        unit_response = requests.get(f'{API_BASE_URL}/organizational-units/{unit_id}', headers=headers)
        if unit_response.status_code != 200:
            flash('Organizational unit not found', 'warning')
            return redirect(url_for('organizational_units.index'))
        
        unit = unit_response.json()
        
        # Get staff members
        staff_response = requests.get(
            f'{API_BASE_URL}/organizational-units/{unit_id}/staff',
            headers=headers
        )
        staff_members = staff_response.json() if staff_response.status_code == 200 else []
        
        return render_template('organizational_units/staff.html', unit=unit, staff=staff_members)
    except Exception as e:
        flash(f'Error loading staff: {str(e)}', 'danger')
        return redirect(url_for('organizational_units.index'))