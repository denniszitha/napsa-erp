"""
Authentication middleware to validate JWT tokens
"""
from flask import request, redirect, url_for, g
from functools import wraps
import jwt
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_token_middleware():
    """Middleware to validate JWT tokens on each request"""
    # Skip validation for auth routes and static files
    if request.path.startswith('/auth/') or request.path.startswith('/static/'):
        return None
    
    # Get token from cookie
    token = request.cookies.get('napsa_token')
    
    if token:
        try:
            # Decode token without verification (just to check expiry)
            payload = jwt.decode(token, options={'verify_signature': False})
            exp = payload.get('exp')
            
            if exp:
                # Check if token is expired
                if datetime.utcnow().timestamp() > exp:
                    logger.info(f"Token expired for user {payload.get('username')}")
                    # Clear the invalid token
                    response = redirect(url_for('auth.login'))
                    response.set_cookie('napsa_token', '', expires=0)
                    response.set_cookie('napsa_token_type', '', expires=0)
                    response.set_cookie('napsa_user', '', expires=0)
                    return response
                    
            # Store user info in g for use in views
            user_info = {
                'username': payload.get('username'),
                'user_id': payload.get('user_id'),
                'role': payload.get('role'),
                'email': payload.get('sub'),
                'full_name': payload.get('full_name', payload.get('username')),
                'is_authenticated': True
            }
            g.current_user = user_info
            g.user = user_info  # For compatibility with templates
            
        except jwt.DecodeError:
            logger.error("Invalid token format")
            # Clear invalid token
            response = redirect(url_for('auth.login'))
            response.set_cookie('napsa_token', '', expires=0)
            response.set_cookie('napsa_token_type', '', expires=0)
            response.set_cookie('napsa_user', '', expires=0)
            return response
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
    
    return None

def check_token_expiry():
    """Check if the current token is about to expire and refresh if needed"""
    token = request.cookies.get('napsa_token')
    
    if token:
        try:
            payload = jwt.decode(token, options={'verify_signature': False})
            exp = payload.get('exp')
            
            if exp:
                # Check if token expires in less than 5 minutes
                time_until_expiry = exp - datetime.utcnow().timestamp()
                if time_until_expiry < 300:  # 5 minutes
                    logger.info("Token expiring soon, should refresh")
                    # TODO: Implement token refresh logic
                    
        except Exception as e:
            logger.error(f"Error checking token expiry: {str(e)}")