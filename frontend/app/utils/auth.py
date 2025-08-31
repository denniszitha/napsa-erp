"""
Simple token-based authentication utilities using cookies
"""
from functools import wraps
from flask import redirect, url_for, request
import json
import logging

logger = logging.getLogger(__name__)

def login_required(f):
    """Simple decorator to require authentication token from cookies"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('napsa_token')
        logger.info(f"Auth check for {request.path} - Token present: {bool(token)}")
        if not token:
            logger.warning(f"No auth token for {request.path} - Cookies: {list(request.cookies.keys())}")
            # Check if this is an API request
            if request.path.startswith('/api/') or '/api/' in request.path or request.is_json:
                # Return JSON error for API requests
                from flask import jsonify
                return jsonify({
                    'success': False,
                    'error': 'Not authenticated - please login first'
                }), 401
            else:
                # Regular web request - redirect to login
                next_url = request.url
                return redirect(url_for('auth.login', next=next_url))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user info from cookies"""
    user_cookie = request.cookies.get('napsa_user')
    if user_cookie:
        try:
            user_data = json.loads(user_cookie)
            return user_data
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse user info from cookie: {e}")
            return None
    return None

def is_authenticated():
    """Check if user is authenticated via cookie token"""
    return request.cookies.get('napsa_token') is not None

def get_auth_token():
    """Get authentication token from cookies"""
    return request.cookies.get('napsa_token')