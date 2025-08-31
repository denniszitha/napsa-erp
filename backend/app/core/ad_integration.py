"""
Active Directory Integration Module for NAPSA ERM System
Provides LDAP/AD authentication, user synchronization, and group mapping
"""

import ldap3
from ldap3 import Server, Connection, ALL, NTLM, SIMPLE, SYNC, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError
from typing import Optional, Dict, List, Any, Tuple
import logging
from datetime import datetime, timedelta
import re
from dataclasses import dataclass
import json

from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class ADUser:
    """Active Directory User representation"""
    username: str
    email: str
    full_name: str
    department: str
    title: str
    phone: str
    groups: List[str]
    distinguished_name: str
    manager_dn: Optional[str] = None
    employee_id: Optional[str] = None
    office: Optional[str] = None
    enabled: bool = True


class ActiveDirectoryConfig:
    """AD Configuration Settings"""
    def __init__(self):
        self.server_url = settings.AD_SERVER_URL  # e.g., "ldap://dc.napsa.local:389"
        self.domain = settings.AD_DOMAIN  # e.g., "NAPSA.LOCAL"
        self.base_dn = settings.AD_BASE_DN  # e.g., "DC=napsa,DC=local"
        self.bind_user = settings.AD_BIND_USER  # Service account for queries
        self.bind_password = settings.AD_BIND_PASSWORD
        self.use_ssl = settings.AD_USE_SSL
        self.timeout = settings.AD_TIMEOUT or 30
        
        # User search configuration
        self.user_search_base = settings.AD_USER_SEARCH_BASE or self.base_dn
        self.user_filter = settings.AD_USER_FILTER or "(objectClass=user)"
        self.user_attributes = [
            'sAMAccountName', 'mail', 'displayName', 'department',
            'title', 'telephoneNumber', 'memberOf', 'distinguishedName',
            'manager', 'employeeID', 'physicalDeliveryOfficeName',
            'userAccountControl', 'givenName', 'sn', 'cn'
        ]
        
        # Group to Role mapping
        self.group_role_mapping = self._load_group_role_mapping()
        
    def _load_group_role_mapping(self) -> Dict[str, UserRole]:
        """Load AD group to application role mapping"""
        default_mapping = {
            "CN=ERM_Admins,OU=Groups,DC=napsa,DC=local": UserRole.admin,
            "CN=Risk_Managers,OU=Groups,DC=napsa,DC=local": UserRole.risk_manager,
            "CN=Risk_Owners,OU=Groups,DC=napsa,DC=local": UserRole.risk_owner,
            "CN=Auditors,OU=Groups,DC=napsa,DC=local": UserRole.auditor,
            "CN=ERM_Users,OU=Groups,DC=napsa,DC=local": UserRole.viewer,
        }
        
        # Load custom mapping from settings if available
        if hasattr(settings, 'AD_GROUP_ROLE_MAPPING'):
            try:
                custom_mapping = json.loads(settings.AD_GROUP_ROLE_MAPPING)
                return {k: UserRole(v) for k, v in custom_mapping.items()}
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error loading custom group mapping: {e}")
        
        return default_mapping


class ActiveDirectoryClient:
    """Main AD Integration Client"""
    
    def __init__(self, config: Optional[ActiveDirectoryConfig] = None):
        self.config = config or ActiveDirectoryConfig()
        self._connection: Optional[Connection] = None
        
    def _get_server(self) -> Server:
        """Create LDAP server object"""
        return Server(
            self.config.server_url,
            use_ssl=self.config.use_ssl,
            get_info=ALL,
            connect_timeout=self.config.timeout
        )
    
    def _get_connection(self, user_dn: Optional[str] = None, 
                       password: Optional[str] = None) -> Connection:
        """Create LDAP connection"""
        server = self._get_server()
        
        if user_dn and password:
            # User authentication
            auth_type = NTLM if '\\' in user_dn else SIMPLE
            conn = Connection(
                server,
                user=user_dn,
                password=password,
                authentication=auth_type,
                auto_bind=True,
                raise_exceptions=True
            )
        else:
            # Service account for queries
            conn = Connection(
                server,
                user=f"{self.config.domain}\\{self.config.bind_user}",
                password=self.config.bind_password,
                authentication=NTLM,
                auto_bind=True,
                raise_exceptions=True
            )
        
        return conn
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[ADUser]]:
        """
        Authenticate user against Active Directory
        Returns: (success, ad_user_object)
        """
        try:
            # Format username for authentication
            if '@' not in username and '\\' not in username:
                user_principal = f"{username}@{self.config.domain}"
                domain_user = f"{self.config.domain}\\{username}"
            else:
                user_principal = username
                domain_user = username
            
            # Try authentication
            try:
                # Try UPN authentication first
                conn = self._get_connection(user_principal, password)
            except LDAPBindError:
                # Try domain\username format
                conn = self._get_connection(domain_user, password)
            
            # If we get here, authentication succeeded
            # Now fetch user details using service account
            ad_user = self.get_user_details(username)
            
            conn.unbind()
            
            return True, ad_user
            
        except LDAPBindError as e:
            logger.warning(f"AD authentication failed for {username}: {e}")
            return False, None
        except LDAPException as e:
            logger.error(f"LDAP error during authentication: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error during AD authentication: {e}")
            return False, None
    
    def get_user_details(self, username: str) -> Optional[ADUser]:
        """Fetch user details from AD"""
        try:
            conn = self._get_connection()
            
            # Search for user
            search_filter = f"(&{self.config.user_filter}(sAMAccountName={username}))"
            
            conn.search(
                search_base=self.config.user_search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=self.config.user_attributes
            )
            
            if not conn.entries:
                logger.warning(f"User {username} not found in AD")
                return None
            
            entry = conn.entries[0]
            
            # Parse user attributes
            ad_user = ADUser(
                username=str(entry.sAMAccountName),
                email=str(entry.mail) if entry.mail else f"{username}@{self.config.domain}",
                full_name=str(entry.displayName) if entry.displayName else str(entry.cn),
                department=str(entry.department) if entry.department else "Not Specified",
                title=str(entry.title) if entry.title else "Not Specified",
                phone=str(entry.telephoneNumber) if entry.telephoneNumber else "",
                groups=self._parse_groups(entry.memberOf) if entry.memberOf else [],
                distinguished_name=str(entry.distinguishedName),
                manager_dn=str(entry.manager) if entry.manager else None,
                employee_id=str(entry.employeeID) if entry.employeeID else None,
                office=str(entry.physicalDeliveryOfficeName) if entry.physicalDeliveryOfficeName else None,
                enabled=self._is_account_enabled(entry.userAccountControl)
            )
            
            conn.unbind()
            return ad_user
            
        except Exception as e:
            logger.error(f"Error fetching user details for {username}: {e}")
            return None
    
    def _parse_groups(self, member_of) -> List[str]:
        """Parse memberOf attribute to get group DNs"""
        if not member_of:
            return []
        
        if isinstance(member_of, list):
            return [str(group) for group in member_of]
        else:
            return [str(member_of)]
    
    def _is_account_enabled(self, user_account_control) -> bool:
        """Check if AD account is enabled"""
        if not user_account_control:
            return True
        
        try:
            uac = int(str(user_account_control))
            # Bit 1 (0x2) indicates account is disabled
            return not (uac & 0x2)
        except (ValueError, TypeError):
            return True
    
    def sync_users(self, db: Session, department_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronize AD users with database
        Returns sync statistics
        """
        stats = {
            "total_ad_users": 0,
            "created": 0,
            "updated": 0,
            "disabled": 0,
            "errors": 0,
            "synced_at": datetime.utcnow()
        }
        
        try:
            conn = self._get_connection()
            
            # Build search filter
            search_filter = self.config.user_filter
            if department_filter:
                search_filter = f"(&{search_filter}(department={department_filter}))"
            
            # Search for all users
            conn.search(
                search_base=self.config.user_search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=self.config.user_attributes,
                paged_size=500  # Handle large directories
            )
            
            stats["total_ad_users"] = len(conn.entries)
            
            for entry in conn.entries:
                try:
                    ad_user = self._entry_to_ad_user(entry)
                    if ad_user:
                        result = self._sync_single_user(db, ad_user)
                        stats[result] += 1
                except Exception as e:
                    logger.error(f"Error syncing user {entry.sAMAccountName}: {e}")
                    stats["errors"] += 1
            
            conn.unbind()
            
        except Exception as e:
            logger.error(f"Error during user synchronization: {e}")
            stats["error_message"] = str(e)
        
        return stats
    
    def _entry_to_ad_user(self, entry) -> Optional[ADUser]:
        """Convert LDAP entry to ADUser object"""
        try:
            return ADUser(
                username=str(entry.sAMAccountName),
                email=str(entry.mail) if entry.mail else f"{entry.sAMAccountName}@{self.config.domain}",
                full_name=str(entry.displayName) if entry.displayName else str(entry.cn),
                department=str(entry.department) if entry.department else "Not Specified",
                title=str(entry.title) if entry.title else "",
                phone=str(entry.telephoneNumber) if entry.telephoneNumber else "",
                groups=self._parse_groups(entry.memberOf) if entry.memberOf else [],
                distinguished_name=str(entry.distinguishedName),
                manager_dn=str(entry.manager) if entry.manager else None,
                employee_id=str(entry.employeeID) if entry.employeeID else None,
                office=str(entry.physicalDeliveryOfficeName) if entry.physicalDeliveryOfficeName else None,
                enabled=self._is_account_enabled(entry.userAccountControl)
            )
        except Exception as e:
            logger.error(f"Error parsing AD entry: {e}")
            return None
    
    def _sync_single_user(self, db: Session, ad_user: ADUser) -> str:
        """Sync single AD user with database"""
        # Check if user exists
        db_user = db.query(User).filter(
            User.username == ad_user.username
        ).first()
        
        # Determine role from AD groups
        user_role = self._determine_user_role(ad_user.groups)
        
        if db_user:
            # Update existing user
            db_user.email = ad_user.email
            db_user.full_name = ad_user.full_name
            db_user.department = ad_user.department
            db_user.position = ad_user.title
            db_user.phone = ad_user.phone
            db_user.is_active = ad_user.enabled
            db_user.role = user_role
            db_user.updated_at = datetime.utcnow()
            
            db.commit()
            return "updated"
        else:
            # Create new user
            new_user = User(
                username=ad_user.username,
                email=ad_user.email,
                full_name=ad_user.full_name,
                department=ad_user.department,
                position=ad_user.title,
                phone=ad_user.phone,
                is_active=ad_user.enabled,
                role=user_role,
                # Set a random password - AD auth will be used
                hashed_password=get_password_hash(f"AD_{ad_user.username}_{datetime.now()}")
            )
            
            db.add(new_user)
            db.commit()
            return "created"
    
    def _determine_user_role(self, groups: List[str]) -> UserRole:
        """Determine application role based on AD group membership"""
        # Check groups in priority order (admin > risk_manager > risk_owner > auditor > viewer)
        role_priority = [
            UserRole.admin,
            UserRole.risk_manager,
            UserRole.risk_owner,
            UserRole.auditor,
            UserRole.viewer
        ]
        
        for role in role_priority:
            for group_dn, mapped_role in self.config.group_role_mapping.items():
                if mapped_role == role and group_dn in groups:
                    return role
        
        # Default to viewer if no matching group
        return UserRole.viewer
    
    def search_users(self, search_term: str, max_results: int = 50) -> List[ADUser]:
        """Search for AD users by name, email, or username"""
        try:
            conn = self._get_connection()
            
            # Build search filter
            search_filter = f"""(&{self.config.user_filter}
                (|(sAMAccountName=*{search_term}*)
                  (displayName=*{search_term}*)
                  (mail=*{search_term}*)
                  (givenName=*{search_term}*)
                  (sn=*{search_term}*)))"""
            
            conn.search(
                search_base=self.config.user_search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=self.config.user_attributes,
                size_limit=max_results
            )
            
            users = []
            for entry in conn.entries:
                ad_user = self._entry_to_ad_user(entry)
                if ad_user:
                    users.append(ad_user)
            
            conn.unbind()
            return users
            
        except Exception as e:
            logger.error(f"Error searching AD users: {e}")
            return []
    
    def get_user_groups(self, username: str) -> List[Dict[str, str]]:
        """Get all groups for a specific user with details"""
        try:
            ad_user = self.get_user_details(username)
            if not ad_user:
                return []
            
            conn = self._get_connection()
            groups = []
            
            for group_dn in ad_user.groups:
                # Extract CN from DN
                cn_match = re.match(r'CN=([^,]+)', group_dn)
                if cn_match:
                    group_name = cn_match.group(1)
                    
                    # Check if this group maps to a role
                    mapped_role = None
                    for mapped_dn, role in self.config.group_role_mapping.items():
                        if group_dn == mapped_dn:
                            mapped_role = role.value
                            break
                    
                    groups.append({
                        "dn": group_dn,
                        "name": group_name,
                        "mapped_role": mapped_role
                    })
            
            conn.unbind()
            return groups
            
        except Exception as e:
            logger.error(f"Error fetching user groups: {e}")
            return []
    
    def test_connection(self) -> Dict[str, Any]:
        """Test AD connection and return diagnostic info"""
        result = {
            "connected": False,
            "server": self.config.server_url,
            "bind_user": self.config.bind_user,
            "base_dn": self.config.base_dn,
            "error": None,
            "server_info": None
        }
        
        try:
            conn = self._get_connection()
            result["connected"] = conn.bound
            result["server_info"] = {
                "server_name": str(conn.server.name),
                "ssl_enabled": self.config.use_ssl
            }
            
            # Try a simple search to verify permissions
            conn.search(
                search_base=self.config.base_dn,
                search_filter="(objectClass=user)",
                search_scope=SUBTREE,
                attributes=['cn'],
                size_limit=1
            )
            
            result["search_permission"] = True
            conn.unbind()
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"AD connection test failed: {e}")
        
        return result


# Global AD client instance
_ad_client: Optional[ActiveDirectoryClient] = None


def get_ad_client() -> ActiveDirectoryClient:
    """Get or create AD client instance"""
    global _ad_client
    if _ad_client is None:
        _ad_client = ActiveDirectoryClient()
    return _ad_client


def authenticate_with_ad(username: str, password: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with AD and create/update local user record
    Returns JWT token data on success
    """
    ad_client = get_ad_client()
    
    # Authenticate with AD
    success, ad_user = ad_client.authenticate_user(username, password)
    
    if not success or not ad_user:
        return None
    
    # Check if account is enabled
    if not ad_user.enabled:
        logger.warning(f"AD account {username} is disabled")
        return None
    
    # Sync user data with local database
    db_user = db.query(User).filter(User.username == ad_user.username).first()
    
    # Determine role from AD groups
    user_role = ad_client._determine_user_role(ad_user.groups)
    
    if db_user:
        # Update existing user
        db_user.email = ad_user.email
        db_user.full_name = ad_user.full_name
        db_user.department = ad_user.department
        db_user.position = ad_user.title
        db_user.phone = ad_user.phone
        db_user.role = user_role
        db_user.last_login = datetime.utcnow()
        db_user.failed_login_attempts = 0
        db_user.locked_until = None
    else:
        # Create new user from AD
        db_user = User(
            username=ad_user.username,
            email=ad_user.email,
            full_name=ad_user.full_name,
            department=ad_user.department,
            position=ad_user.title,
            phone=ad_user.phone,
            role=user_role,
            is_active=True,
            hashed_password=get_password_hash(f"AD_{ad_user.username}"),
            last_login=datetime.utcnow()
        )
        db.add(db_user)
    
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": db_user.username,
            "user_id": str(db_user.id),
            "role": db_user.role.value,
            "department": db_user.department
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user.id),
            "username": db_user.username,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "role": db_user.role.value,
            "department": db_user.department
        }
    }