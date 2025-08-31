"""
Custom decorators for the Flask application
"""
from functools import wraps
from flask import jsonify, request, g
from app.utils.auth import get_current_user, is_authenticated
# from app import cache
import hashlib


def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_authenticated():
                return jsonify({'error': 'Authentication required'}), 401
            
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
                
            user_role = user.get('role', '')
            is_superuser = user.get('is_superuser', False)
            
            if user_role not in roles and not is_superuser:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return jsonify({'error': 'Authentication required'}), 401
        
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
            
        user_role = user.get('role', '')
        is_superuser = user.get('is_superuser', False)
        
        if user_role not in ['admin', 'administrator'] and not is_superuser:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def cache_response(timeout=300, key_prefix='view'):
    """Decorator to cache response (disabled for now)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Cache disabled - just return the function result
            return f(*args, **kwargs)
        return decorated_function
    return decorator