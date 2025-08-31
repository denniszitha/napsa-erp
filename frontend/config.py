"""
Flask Application Configuration
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    
    # Application
    APP_NAME = os.getenv('APP_NAME', 'NAPSA ERM System')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Flask
    FLASK_APP = 'run.py'
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = False
    TESTING = False
    
    # API Backend
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:58001/api/v1')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
    
    # Database (shared with backend)  
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://napsa_admin:napsa_secure_password@localhost:58002/napsa_erm'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Session configuration for storing auth token
    SESSION_TYPE = None  # Use Flask's default cookie-based sessions
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to False for development
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'napsa_session'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # 30 minutes timeout
    # Ensure session data persists across requests
    SESSION_PERMANENT = True
    
    # Additional session security
    SESSION_REFRESH_EACH_REQUEST = True  # Refresh session on each request
    SESSION_COOKIE_MAX_AGE = 1800  # 30 minutes in seconds
    
    # Security
    WTF_CSRF_ENABLED = False  # Disabled for now since sessions are managed by backend
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False
    
    # Cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = 'napsa_cache:'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URL', 'redis://localhost:6379/2')
    RATELIMIT_KEY_PREFIX = 'napsa_rate:'
    RATELIMIT_DEFAULT = '100 per hour'
    RATELIMIT_HEADERS_ENABLED = True
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'csv'}
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@napsa.co.zm')
    
    # SocketIO
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_MESSAGE_QUEUE = os.getenv('REDIS_URL', 'redis://localhost:6379/3')
    
    # Babel (i18n)
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'Africa/Lusaka'
    LANGUAGES = {
        'en': 'English',
        'bem': 'Bemba',
        'ny': 'Nyanja'
    }
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Theme Colors
    PRIMARY_COLOR = '#6cbace'
    SECONDARY_COLOR = '#cce7e8'
    
    # Features
    ENABLE_REGISTRATION = os.getenv('ENABLE_REGISTRATION', 'false').lower() == 'true'
    ENABLE_2FA = os.getenv('ENABLE_2FA', 'true').lower() == 'true'
    ENABLE_AUDIT_LOG = os.getenv('ENABLE_AUDIT_LOG', 'true').lower() == 'true'
    

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Stricter security in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Performance
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year
    

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}