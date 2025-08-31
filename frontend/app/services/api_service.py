"""
API Service for communicating with FastAPI backend
"""
import requests
import logging
import json
from typing import Optional, Dict, Any, List
from flask import current_app, session
from functools import wraps
import time

logger = logging.getLogger(__name__)


def safe_json_parse(response: requests.Response) -> Optional[Dict[str, Any]]:
    """Safely parse JSON response with proper error handling"""
    if not response.text:
        return None
    
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse JSON response: {e}. Status: {response.status_code}, Response text: {response.text[:200]}")
        return None


class APIService:
    """Service for making API calls to the FastAPI backend"""
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Get request headers with authentication token"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add authentication token if available from cookies
        from flask import request
        token = request.cookies.get('napsa_token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        return headers
    
    @staticmethod
    def handle_response(response: requests.Response) -> Dict[str, Any]:
        """Handle API response"""
        try:
            if response.status_code == 401:
                # Token expired or invalid - cookies will be cleared by logout redirect
                return {
                    'success': False,
                    'error': 'Authentication required',
                    'code': 401
                }
            
            if response.status_code == 204:
                # No content
                return {'success': True, 'data': None}
            
            if response.status_code >= 200 and response.status_code < 300:
                # Success
                data = safe_json_parse(response)
                if data is None and response.text:
                    # If JSON parsing failed but we have text, return the raw text
                    data = response.text
                return {
                    'success': True,
                    'data': data
                }
            else:
                # Error
                error_data = safe_json_parse(response)
                if error_data is None:
                    error_data = {'detail': response.text if response.text else f'HTTP {response.status_code}'}
                return {
                    'success': False,
                    'error': error_data.get('detail', f'Error {response.status_code}'),
                    'code': response.status_code,
                    'data': error_data
                }
        except Exception as e:
            logger.error(f"Error handling response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 500
            }
    
    @classmethod
    def get(cls, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request"""
        try:
            url = f"{current_app.config['API_BASE_URL']}{endpoint}"
            response = requests.get(
                url,
                headers=cls.get_headers(),
                params=params,
                timeout=current_app.config['API_TIMEOUT']
            )
            return cls.handle_response(response)
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout', 'code': 408}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error - Backend unavailable', 'code': 503}
        except Exception as e:
            logger.error(f"GET request error: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}
    
    @classmethod
    def post(cls, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request"""
        try:
            url = f"{current_app.config['API_BASE_URL']}{endpoint}"
            
            if files:
                # Multipart form data
                headers = {'Authorization': cls.get_headers().get('Authorization', '')}
                response = requests.post(
                    url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=current_app.config['API_TIMEOUT']
                )
            else:
                # JSON data
                response = requests.post(
                    url,
                    headers=cls.get_headers(),
                    json=data,
                    timeout=current_app.config['API_TIMEOUT']
                )
            
            return cls.handle_response(response)
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout', 'code': 408}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error - Backend unavailable', 'code': 503}
        except Exception as e:
            logger.error(f"POST request error: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}
    
    @classmethod
    def put(cls, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PUT request"""
        try:
            url = f"{current_app.config['API_BASE_URL']}{endpoint}"
            response = requests.put(
                url,
                headers=cls.get_headers(),
                json=data,
                timeout=current_app.config['API_TIMEOUT']
            )
            return cls.handle_response(response)
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout', 'code': 408}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error - Backend unavailable', 'code': 503}
        except Exception as e:
            logger.error(f"PUT request error: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}
    
    @classmethod
    def delete(cls, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request"""
        try:
            url = f"{current_app.config['API_BASE_URL']}{endpoint}"
            response = requests.delete(
                url,
                headers=cls.get_headers(),
                timeout=current_app.config['API_TIMEOUT']
            )
            return cls.handle_response(response)
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout', 'code': 408}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error - Backend unavailable', 'code': 503}
        except Exception as e:
            logger.error(f"DELETE request error: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}
    
    @classmethod
    def patch(cls, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PATCH request"""
        try:
            url = f"{current_app.config['API_BASE_URL']}{endpoint}"
            response = requests.patch(
                url,
                headers=cls.get_headers(),
                json=data,
                timeout=current_app.config['API_TIMEOUT']
            )
            return cls.handle_response(response)
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout', 'code': 408}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error', 'code': 503}
        except Exception as e:
            logger.error(f"PATCH request error: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}


class AuthService:
    """Authentication service"""
    
    @staticmethod
    def login(username: str, password: str) -> Dict[str, Any]:
        """Login user"""
        try:
            url = f"{current_app.config['API_BASE_URL']}/auth/login"
            # Send as form data with proper headers
            response = requests.post(
                url,
                data={'username': username, 'password': password},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=current_app.config['API_TIMEOUT']
            )
            
            if response.status_code == 200:
                # Check if response has content
                if response.text:
                    data = safe_json_parse(response)
                    if data is None:
                        logger.error("Failed to parse login response as JSON")
                        return {'success': False, 'error': 'Invalid response format from server', 'code': 500}
                    
                    # Store token in session
                    session['access_token'] = data.get('access_token')
                    session['token_type'] = data.get('token_type', 'bearer')
                    
                    # Set session as permanent and record activity time
                    from datetime import datetime
                    session.permanent = True
                    session['last_activity'] = datetime.utcnow().isoformat()
                    
                    # Get user info
                    user_info = AuthService.get_current_user()
                    if user_info['success']:
                        session['user'] = user_info['data']
                    
                    return {'success': True, 'data': data}
                else:
                    logger.error("Empty response from login endpoint")
                    return {'success': False, 'error': 'Empty response from server', 'code': 500}
            else:
                error_data = safe_json_parse(response)
                if error_data is None:
                    error_data = {'detail': response.text if response.text else 'Login failed'}
                return {
                    'success': False,
                    'error': error_data.get('detail', 'Login failed'),
                    'code': response.status_code
                }
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection error - Backend unavailable', 'code': 503}
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 500}
    
    @staticmethod
    def logout() -> Dict[str, Any]:
        """Logout user"""
        try:
            # Call logout endpoint
            result = APIService.post('/auth/logout')
            
            # Clear session
            session.pop('access_token', None)
            session.pop('token_type', None)
            session.pop('user', None)
            
            return {'success': True}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_current_user() -> Dict[str, Any]:
        """Get current user information"""
        return APIService.get('/users/me')
    
    @staticmethod
    def refresh_token() -> Dict[str, Any]:
        """Refresh access token"""
        return APIService.post('/auth/refresh')


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry API calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                result = func(*args, **kwargs)
                if result.get('success') or result.get('code') in [400, 401, 403, 404]:
                    # Don't retry on client errors
                    return result
                
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
            
            return result
        return wrapper
    return decorator