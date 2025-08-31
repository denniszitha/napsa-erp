"""
Authentication Blueprint
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from app.forms.auth import LoginForm, ChangePasswordForm, ProfileForm
from app.services.api_service import AuthService, APIService
from app.utils.auth import login_required, get_current_user
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, template_folder='templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # Check if already logged in via token
    if session.get('access_token'):
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Attempt login via API
        result = AuthService.login(form.username.data, form.password.data)
        
        if result['success']:
            # Store token and user info using cookies instead of sessions
            # Backend will validate token on each request
            data = result.get('data', {})
            access_token = data.get('access_token') or result.get('access_token')
            
            # Get user data using the new token
            try:
                import requests
                api_url = f"{current_app.config['API_BASE_URL']}/users/me"
                
                user_response = requests.get(
                    api_url,
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=10
                )
                
                if user_response.status_code == 200:
                    user_info = user_response.json()
                else:
                    logger.error(f"Failed to fetch user info: {user_response.status_code}")
                    user_info = None
            except Exception as e:
                logger.error(f"Error fetching user info: {e}")
                user_info = None
            
            flash('Successfully logged in!', 'success')
            
            # Create response and set cookies
            next_page = request.args.get('next')
            response = redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
            
            # Set secure HTTP-only cookies with shorter lifespan (30 minutes to match backend token)
            # Use max_age=1800 (30 minutes) to match backend token expiry
            response.set_cookie('napsa_token', access_token, httponly=True, secure=False, samesite='Lax', max_age=1800)
            response.set_cookie('napsa_token_type', data.get('token_type', 'bearer'), httponly=True, secure=False, samesite='Lax', max_age=1800)
            if user_info:
                import json
                response.set_cookie('napsa_user', json.dumps(user_info), httponly=True, secure=False, samesite='Lax', max_age=1800)
            
            return response
        else:
            flash(result.get('error', 'Login failed'), 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    """Logout"""
    # Clear session data
    session.clear()
    flash('Successfully logged out!', 'success')
    
    # Create response and clear cookies
    response = redirect(url_for('auth.login'))
    response.set_cookie('napsa_token', '', expires=0)
    response.set_cookie('napsa_token_type', '', expires=0)
    response.set_cookie('napsa_user', '', expires=0)
    
    return response


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    # Get current user info from cookies
    user_info = get_current_user() or {}
    form = ProfileForm()
    
    # Populate form with current user data
    if request.method == 'GET':
        form.full_name.data = user_info.get('full_name')
        form.department.data = user_info.get('department')
        form.theme.data = user_info.get('theme')
        form.language.data = user_info.get('language')
        form.timezone.data = user_info.get('timezone')
        form.notifications_enabled.data = user_info.get('notifications_enabled')
    
    if form.validate_on_submit():
        # Update user profile via API
        profile_data = {
            'full_name': form.full_name.data,
            'department': form.department.data,
            'theme': form.theme.data,
            'language': form.language.data,
            'timezone': form.timezone.data,
            'notifications_enabled': form.notifications_enabled.data
        }
        
        result = APIService.put('/users/me', profile_data)
        
        if result['success']:
            # Update user cookie with new data
            updated_user = result.get('data', {})
            if updated_user:
                import json
                response = redirect(url_for('auth.profile'))
                response.set_cookie('napsa_user', json.dumps(updated_user), httponly=True, secure=False, samesite='Lax', max_age=86400)
                flash('Profile updated successfully!', 'success')
                return response
            else:
                flash('Profile updated successfully!', 'success')
        else:
            flash(result.get('error', 'Failed to update profile'), 'error')
        
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password page"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Call API to change password
        result = APIService.post('/auth/change-password', {
            'old_password': form.old_password.data,
            'new_password': form.new_password.data
        })
        
        if result['success']:
            # Backend handles logging - no need to log here
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash(result.get('error', 'Failed to change password'), 'error')
    
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/session-expired')
def session_expired():
    """Session expired page"""
    return render_template('auth/session_expired.html')


# Removed before_request - no user activity tracking needed with token auth