from typing import Optional
from pydantic_settings import BaseSettings
import secrets
import os


class Settings(BaseSettings):
    # Database - use environment variable or default
    # Docker sets DATABASE_URL with 'postgres' hostname
    # For local development, use localhost:52000
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://napsa_admin:napsa_password@102.23.120.243:58002/napsa_erm"
    )
    
    # Database connection settings
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 300
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NAPSA ERM System"
    VERSION: str = "1.0.0"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Email settings
    SMTP_HOST: Optional[str] = "smtp.titan.email"
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = "no_reply@ontech.co.zm"
    SMTP_PASSWORD: Optional[str] = "TestPass123!"
    EMAILS_FROM_EMAIL: Optional[str] = "no_reply@ontech.co.zm"
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False
    
    # SMS settings
    SMS_USERNAME: Optional[str] = "Chileshe"
    SMS_PASSWORD: Optional[str] = "Chileshe1" 
    SMS_SHORTCODE: Optional[str] = "388"
    SMS_SENDER_ID: Optional[str] = "ONTECH"
    SMS_API_KEY: Optional[str] = "use_preshared"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Active Directory Integration Settings
    AD_ENABLED: bool = os.getenv("AD_ENABLED", "false").lower() == "true"
    AD_SERVER_URL: str = os.getenv("AD_SERVER_URL", "ldap://dc.napsa.local:389")
    AD_DOMAIN: str = os.getenv("AD_DOMAIN", "NAPSA.LOCAL")
    AD_BASE_DN: str = os.getenv("AD_BASE_DN", "DC=napsa,DC=local")
    AD_BIND_USER: str = os.getenv("AD_BIND_USER", "svc_erm_ldap")
    AD_BIND_PASSWORD: str = os.getenv("AD_BIND_PASSWORD", "")
    AD_USE_SSL: bool = os.getenv("AD_USE_SSL", "false").lower() == "true"
    AD_TIMEOUT: int = int(os.getenv("AD_TIMEOUT", "30"))
    AD_USER_SEARCH_BASE: Optional[str] = os.getenv("AD_USER_SEARCH_BASE", "OU=Users,DC=napsa,DC=local")
    AD_USER_FILTER: str = os.getenv("AD_USER_FILTER", "(&(objectClass=user)(objectCategory=person))")
    AD_GROUP_ROLE_MAPPING: Optional[str] = os.getenv("AD_GROUP_ROLE_MAPPING", None)
    AD_SYNC_ENABLED: bool = os.getenv("AD_SYNC_ENABLED", "false").lower() == "true"
    AD_SYNC_INTERVAL_HOURS: int = int(os.getenv("AD_SYNC_INTERVAL_HOURS", "24"))
    
    # Authentication Mode: "local", "ad", or "hybrid"
    AUTH_MODE: str = os.getenv("AUTH_MODE", "hybrid")  # hybrid allows both local and AD auth
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env


settings = Settings()
