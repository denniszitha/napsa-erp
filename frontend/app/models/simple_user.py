"""
Simple User model for authentication without database
"""
from flask_login import UserMixin

class User(UserMixin):
    """Simple user model that doesn't require database"""
    
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.role = user_data.get('role')
        self.access_token = user_data.get('access_token')
        self.full_name = user_data.get('full_name', '')
        self.department = user_data.get('department', '')
        self._is_active = user_data.get('is_active', True)
    
    def get_id(self):
        return str(self.id)
    
    @property
    def is_active(self):
        """Override is_active property from UserMixin"""
        return self._is_active
    
    def get_auth_token(self):
        """Return the access token for API calls"""
        return self.access_token
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin' or self.role == 'administrator'
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def is_authenticated(self):
        """Check if user is authenticated (override UserMixin)"""
        return True  # If we have a User object, they're authenticated
    
    @staticmethod
    def from_api_response(user_data):
        """Create user from API response"""
        return User(user_data)