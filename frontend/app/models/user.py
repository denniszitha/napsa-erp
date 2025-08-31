"""
User model for session management
"""
from flask_login import UserMixin
from app import db
from datetime import datetime


class User(UserMixin, db.Model):
    """User model for session management"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID from API
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(50))
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_superuser = db.Column(db.Boolean, default=False)
    
    # Session management
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    session_token = db.Column(db.String(255))
    
    # Preferences
    theme = db.Column(db.String(20), default='light')
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='Africa/Lusaka')
    notifications_enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_id(self):
        """Return user id for Flask-Login"""
        return str(self.id)
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin' or self.is_superuser
    
    def is_risk_manager(self):
        """Check if user is risk manager"""
        return self.role in ['admin', 'risk_manager']
    
    def is_auditor(self):
        """Check if user is auditor"""
        return self.role in ['admin', 'auditor']
    
    def can_edit_risks(self):
        """Check if user can edit risks"""
        return self.role in ['admin', 'risk_manager', 'risk_owner']
    
    def can_view_reports(self):
        """Check if user can view reports"""
        return self.role != 'viewer'
    
    @staticmethod
    def from_api_response(user_data):
        """Create or update user from API response"""
        user = User.query.get(user_data['id'])
        
        if not user:
            user = User(id=user_data['id'])
        
        user.email = user_data.get('email')
        user.username = user_data.get('username')
        user.full_name = user_data.get('full_name')
        user.role = user_data.get('role')
        user.department = user_data.get('department')
        user.is_active = user_data.get('is_active', True)
        user.is_superuser = user_data.get('is_superuser', False)
        user.last_login = datetime.utcnow()
        user.last_activity = datetime.utcnow()
        
        return user


class AuditLog(db.Model):
    """Audit log model"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.String(36))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')
    
    @staticmethod
    def log(action, resource_type=None, resource_id=None, details=None, user_id=None, ip_address=None, user_agent=None):
        """Create audit log entry"""
        from flask import request
        from flask_login import current_user
        
        log = AuditLog(
            user_id=user_id or (current_user.id if current_user.is_authenticated else None),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address or request.remote_addr,
            user_agent=user_agent or request.user_agent.string
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log