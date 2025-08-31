"""
Flask Application Factory
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
# Removed Flask-Login - using token-based auth only
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
# Optional imports - comment out if not installed
# from flask_caching import Cache
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# from flask_babel import Babel
# from flask_mail import Mail
# from flask_socketio import SocketIO

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
# cache = Cache()
# limiter = Limiter(key_func=get_remote_address)
# babel = Babel()
# mail = Mail()
# socketio = SocketIO()


def create_app(config_name=None):
    """Create Flask application"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Use Docker config if in Docker environment
    if config_name == 'docker' or os.getenv('FLASK_CONFIG') == 'docker':
        from config_docker import DockerConfig
        app.config.from_object(DockerConfig)
    else:
        from config import config
        app.config.from_object(config[config_name])
    
    # Ensure SECRET_KEY is set
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    # Force template auto-reload to ensure templates are not cached
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    
    # Initialize extensions
    # db.init_app(app)  # Frontend should not access database directly
    # migrate.init_app(app, db)  # Frontend doesn't need migrations
    # login_manager removed - using token-based auth
    
    # Initialize CSRF with exemption for API routes
    csrf.init_app(app)
    
    # Add token validation middleware
    from app.middleware.auth_middleware import validate_token_middleware
    
    @app.before_request
    def validate_auth_token():
        """Validate authentication token before each request"""
        response = validate_token_middleware()
        if response:
            return response
    
    # Exempt API routes from CSRF
    @app.before_request
    def exempt_csrf_for_api():
        from flask import request
        if request.path.startswith('/api/') or '/api/' in request.path:
            csrf._exempt_views.add(request.endpoint)
    # cache.init_app(app)
    # limiter.init_app(app)
    # babel.init_app(app)
    # mail.init_app(app)
    # socketio.init_app(app, 
    #                   async_mode=app.config['SOCKETIO_ASYNC_MODE'],
    #                   message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
    
    # Session timeout handling
    @app.before_request
    def check_session_timeout():
        from flask import session, request, redirect, url_for
        from datetime import datetime, timedelta
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Skip session check for static files and auth endpoints
        if request.endpoint and (
            request.endpoint.startswith('static') or 
            request.endpoint.startswith('auth.') or
            request.endpoint == 'auth.login'
        ):
            return
        
        # Check if user is logged in
        if 'access_token' in session:
            # Check last activity time
            if 'last_activity' in session:
                last_activity = datetime.fromisoformat(session['last_activity'])
                time_since_activity = datetime.utcnow() - last_activity
                
                # If inactive for more than 30 minutes, log out
                if time_since_activity > timedelta(minutes=30):
                    logger.info(f"Session expired due to inactivity: {time_since_activity}")
                    session.clear()
                    if request.is_json:
                        from flask import jsonify
                        return jsonify({'error': 'Session expired', 'redirect': '/auth/login'}), 401
                    return redirect(url_for('auth.login', message='Session expired due to inactivity'))
            
            # Update last activity time
            session['last_activity'] = datetime.utcnow().isoformat()
            session.permanent = True
    
    # Token-based auth - no login manager needed
    # Add context processor for templates
    @app.context_processor
    def inject_user():
        from app.utils.auth import get_current_user, is_authenticated
        import logging
        logger = logging.getLogger(__name__)
        
        user_info = get_current_user()
        if user_info and is_authenticated():
            # Create proper user class with methods for templates
            class User:
                def __init__(self, user_data):
                    self.role = user_data.get('role')
                    self.username = user_data.get('username')
                    self.full_name = user_data.get('full_name')
                    self.email = user_data.get('email')
                    self.department = user_data.get('department')
                    self.is_superuser = user_data.get('is_superuser', False)
                    self.info = user_data
                
                def is_authenticated(self):
                    return True
                
                def is_admin(self):
                    return self.role in ['admin', 'administrator'] or self.is_superuser
                
                def has_role(self, role):
                    return self.role == role
            
            current_user = User(user_info)
        else:
            # Anonymous user class
            class AnonymousUser:
                def __init__(self):
                    self.role = None
                    self.username = None
                    self.full_name = None
                    self.email = None
                    self.department = None
                    self.is_superuser = False
                    self.info = {}
                
                def is_authenticated(self):
                    return False
                
                def is_admin(self):
                    return False
                
                def has_role(self, role):
                    return False
            
            current_user = AnonymousUser()
        
        # Also set g.user for compatibility
        from flask import g
        g.user = current_user
        return dict(current_user=current_user, g=g)
    
    # Setup logging
    setup_logging(app)
    
    # Register security headers
    register_security_headers(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Frontend doesn't need database tables - backend handles all database operations
    
    return app


def register_blueprints(app):
    """Register all blueprints"""
    
    # Authentication
    from app.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Dashboard
    from app.blueprints.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    # Risk Management
    from app.blueprints.risks import risks_bp
    app.register_blueprint(risks_bp, url_prefix='/risks')
    
    # Compliance
    from app.blueprints.compliance import compliance_bp
    app.register_blueprint(compliance_bp, url_prefix='/compliance')
    
    # AML
    from app.blueprints.aml import aml_bp
    app.register_blueprint(aml_bp, url_prefix='/aml')
    
    # Controls
    from app.blueprints.controls import controls_bp
    app.register_blueprint(controls_bp, url_prefix='/controls')
    
    # Incidents
    from app.blueprints.incidents import incidents_bp
    app.register_blueprint(incidents_bp, url_prefix='/incidents')
    
    # Reports
    from app.blueprints.reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Audit
    from app.blueprints.audit import audit_bp
    app.register_blueprint(audit_bp, url_prefix='/audit')
    
    # KRI (Key Risk Indicators)
    from app.blueprints.kri import kri_bp
    app.register_blueprint(kri_bp, url_prefix='/kri')
    
    # Settings
    from app.blueprints.settings import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    # Analytics
    from app.blueprints.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # Policies
    from app.blueprints.policies import policies_bp
    app.register_blueprint(policies_bp, url_prefix='/policies')
    
    # Regulations
    from app.blueprints.regulations import regulations_bp
    app.register_blueprint(regulations_bp, url_prefix='/regulations')
    
    # Assessment Periods
    from app.blueprints.assessment_periods import assessment_periods_bp
    app.register_blueprint(assessment_periods_bp, url_prefix='/assessment-periods')
    
    # Risk Assessments
    from app.blueprints.assessments import assessments_bp
    app.register_blueprint(assessments_bp, url_prefix='/risk-assessments')
    
    # Risk Treatments
    from app.blueprints.treatments import treatments_bp
    app.register_blueprint(treatments_bp, url_prefix='/treatments')
    
    # Vendors
    from app.blueprints.vendors import vendors_bp
    app.register_blueprint(vendors_bp, url_prefix='/vendors')
    
    # Training
    from app.blueprints.training import training_bp
    app.register_blueprint(training_bp, url_prefix='/training')
    
    # Metrics
    from app.blueprints.metrics import metrics_bp
    app.register_blueprint(metrics_bp, url_prefix='/metrics')
    
    # Users
    from app.blueprints.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/users')
    
    # Integrations
    from app.blueprints.integrations import integrations_bp
    app.register_blueprint(integrations_bp, url_prefix='/integrations')
    
    # API Proxy (for frontend API calls)
    from app.blueprints.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Notifications
    from app.blueprints.notifications import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    # RCSA
    from app.blueprints.rcsa import rcsa_bp
    app.register_blueprint(rcsa_bp, url_prefix='/rcsa')
    
    # Departments
    from app.blueprints.departments import departments_bp
    app.register_blueprint(departments_bp, url_prefix='/departments')
    
    # BI Tools
    from app.blueprints.bi_tools import bi_tools
    app.register_blueprint(bi_tools, url_prefix='/bi-tools')
    
    # Matrix Configuration
    from app.blueprints.matrix import matrix_bp
    app.register_blueprint(matrix_bp, url_prefix='/matrix')
    
    # Branches
    from app.blueprints.branches import branches_bp
    app.register_blueprint(branches_bp, url_prefix='/branches')
    
    # Executive Dashboard
    from app.blueprints.executive_dashboard import executive_dashboard_bp
    app.register_blueprint(executive_dashboard_bp, url_prefix='/executive-dashboard')
    
    # Executive Directorate Module
    from app.blueprints.executive import executive_bp
    app.register_blueprint(executive_bp, url_prefix='/executive')
    
    # Organizational Units
    from app.blueprints.organizational_units import organizational_units_bp
    app.register_blueprint(organizational_units_bp, url_prefix='/organizational-units')
    
    # Risk Categories
    from app.blueprints.risk_categories import risk_categories_bp
    app.register_blueprint(risk_categories_bp, url_prefix='/risk-categories')
    
    # Main routes
    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        # No database session to rollback - frontend is stateless
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return render_template('errors/429.html'), 429


def register_security_headers(app):
    """Add security headers to all responses"""
    
    @app.after_request
    def set_security_headers(response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy - Allow CDN resources
        csp = (
            "default-src 'self' https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com "
            "https://cdn.datatables.net https://cdn.socket.io https://ui-avatars.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.datatables.net "
            "https://fonts.googleapis.com; "
            "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data: https: http: blob:; "
            "connect-src 'self' ws: wss: https:; "
            "frame-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response


def register_template_filters(app):
    """Register custom template filters"""
    
    @app.template_filter('datetime')
    def datetime_filter(value, format='%Y-%m-%d %H:%M'):
        """Format datetime"""
        if value is None:
            return ''
        return value.strftime(format)
    
    @app.template_filter('currency')
    def currency_filter(value):
        """Format currency"""
        if value is None:
            return 'ZMW 0.00'
        return f'ZMW {value:,.2f}'
    
    @app.template_filter('percentage')
    def percentage_filter(value):
        """Format percentage"""
        if value is None:
            return '0%'
        return f'{value:.1f}%'
    
    @app.template_filter('risk_color')
    def risk_color_filter(value):
        """Get risk color based on score"""
        if value is None:
            return 'secondary'
        elif value <= 3:
            return 'success'
        elif value <= 6:
            return 'warning'
        elif value <= 8:
            return 'orange'
        else:
            return 'danger'
    
    # Add context processor for auth token
    @app.context_processor
    def inject_auth_token():
        """Inject authentication token into all templates"""
        from flask import session
        return dict(
            auth_token=session.get('access_token', ''),
            token_type=session.get('token_type', 'Bearer')
        )


def setup_logging(app):
    """Setup application logging"""
    
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Setup file handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        # Setup formatter
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        
        # Set log level
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('NAPSA ERM System startup')