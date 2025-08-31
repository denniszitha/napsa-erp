"""
Branches Blueprint - Manage NAPSA branch offices
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.utils.auth import login_required, get_current_user
import requests
from config import Config

branches_bp = Blueprint('branches', __name__)

API_BASE_URL = Config.API_BASE_URL

@branches_bp.route('/')
@login_required
def index():
    """List all branches"""
    try:
        # Get auth token from session or user
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/branches', headers=headers)
        branches = response.json() if response.status_code == 200 else []
        
        return render_template('branches/index.html', branches=branches)
    except Exception as e:
        flash(f'Error loading branches: {str(e)}', 'danger')
        return render_template('branches/index.html', branches=[])

@branches_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint to get branches list"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/branches', headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@branches_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new branch"""
    if request.method == 'POST':
        try:
            headers = {'Content-Type': 'application/json'}
            if hasattr(current_user, 'get_auth_token'):
                headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
            
            data = request.get_json() if request.is_json else request.form.to_dict()
            response = requests.post(f'{API_BASE_URL}/branches', json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                flash('Branch created successfully', 'success')
                return jsonify({'success': True})
            else:
                return jsonify({'error': response.text}), response.status_code
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('branches/create.html')

@branches_bp.route('/<int:branch_id>')
@login_required
def view(branch_id):
    """View branch details"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.get(f'{API_BASE_URL}/branches/{branch_id}', headers=headers)
        if response.status_code == 200:
            branch = response.json()
            return render_template('branches/view.html', branch=branch)
        else:
            flash('Branch not found', 'warning')
            return redirect(url_for('branches.index'))
    except Exception as e:
        flash(f'Error loading branch: {str(e)}', 'danger')
        return redirect(url_for('branches.index'))

@branches_bp.route('/<int:branch_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(branch_id):
    """Edit branch"""
    if request.method == 'POST':
        try:
            headers = {'Content-Type': 'application/json'}
            if hasattr(current_user, 'get_auth_token'):
                headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
            
            data = request.get_json() if request.is_json else request.form.to_dict()
            response = requests.put(f'{API_BASE_URL}/branches/{branch_id}', json=data, headers=headers)
            
            if response.status_code == 200:
                flash('Branch updated successfully', 'success')
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
        
        response = requests.get(f'{API_BASE_URL}/branches/{branch_id}', headers=headers)
        if response.status_code == 200:
            branch = response.json()
            return render_template('branches/edit.html', branch=branch)
        else:
            flash('Branch not found', 'warning')
            return redirect(url_for('branches.index'))
    except Exception as e:
        flash(f'Error loading branch: {str(e)}', 'danger')
        return redirect(url_for('branches.index'))

@branches_bp.route('/<int:branch_id>/delete', methods=['POST'])
@login_required
def delete(branch_id):
    """Delete branch"""
    try:
        headers = {}
        if hasattr(current_user, 'get_auth_token'):
            headers['Authorization'] = f'Bearer {current_user.get_auth_token()}'
        
        response = requests.delete(f'{API_BASE_URL}/branches/{branch_id}', headers=headers)
        
        if response.status_code in [200, 204]:
            flash('Branch deleted successfully', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'error': response.text}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500