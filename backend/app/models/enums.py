"""
Centralized Enum Definitions for NAPSA ERM System
Aligned with ermdb.sql schema
"""

from enum import Enum


# User and Role Enums
class UserRole(str, Enum):
    SUPER_ADMIN = "Super Admin"
    ADMIN = "Admin" 
    RISK_MANAGER = "Risk Manager"
    RISK_OWNER = "Risk Owner"
    RISK_CHAMPION = "Risk Champion"
    DEPARTMENT_MANAGER = "Department Manager"
    DIRECTORATE_HEAD = "Directorate Head"
    VIEWER = "Viewer"
    AUDITOR = "Auditor"


# Assessment Enums
class AssessmentStatus(str, Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    COMPLETED = "Completed"


class AssessmentType(str, Enum):
    INITIAL_ASSESSMENT = "Initial Assessment"
    PERIODIC_REVIEW = "Periodic Review"
    TRIGGERED_ASSESSMENT = "Triggered Assessment"
    INTERIM_ASSESSMENT = "Interim Assessment"


class AssessmentMethod(str, Enum):
    QUALITATIVE = "Qualitative"
    QUANTITATIVE = "Quantitative"
    MIXED_METHOD = "Mixed Method"


class AssessmentPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class BusinessCriticality(str, Enum):
    STANDARD = "Standard"
    IMPORTANT = "Important"
    CRITICAL = "Critical"
    BUSINESS_CRITICAL = "Business Critical"


class ValidationStatus(str, Enum):
    PENDING = "Pending"
    IN_REVIEW = "In Review"
    PASSED = "Passed"
    FAILED = "Failed"
    CONDITIONAL = "Conditional"


class DataSource(str, Enum):
    MANUAL_ENTRY = "Manual Entry"
    API_IMPORT = "API Import"
    FILE_IMPORT = "File Import"
    EXTERNAL_SYSTEM = "External System"
    AUTOMATED = "Automated"


# Compliance Enums
class ComplianceStatus(str, Enum):
    COMPLIANT = "Compliant"
    PARTIALLY_COMPLIANT = "Partially Compliant"
    NON_COMPLIANT = "Non-Compliant"
    NOT_ASSESSED = "Not Assessed"


# Control Enums
class ControlType(str, Enum):
    PREVENTIVE = "Preventive"
    DETECTIVE = "Detective"
    CORRECTIVE = "Corrective"
    DIRECTIVE = "Directive"


class ControlNature(str, Enum):
    MANUAL = "Manual"
    AUTOMATED = "Automated"
    SEMI_AUTOMATED = "Semi-Automated"


class ControlFrequency(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    SEMI_ANNUALLY = "Semi-Annually"
    ANNUALLY = "Annually"
    ON_DEMAND = "On-Demand"
    CONTINUOUS = "Continuous"


class ImplementationStatus(str, Enum):
    NOT_IMPLEMENTED = "Not Implemented"
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    IMPLEMENTED = "Implemented"
    TESTING = "Testing"
    EFFECTIVE = "Effective"
    INEFFECTIVE = "Ineffective"
    NEEDS_IMPROVEMENT = "Needs Improvement"


class ControlStatus(str, Enum):
    NOT_TESTED = "Not Tested"
    PASSED = "Passed"
    FAILED = "Failed"
    NEEDS_IMPROVEMENT = "Needs Improvement"


class ControlMaturityLevel(str, Enum):
    INITIAL = "1 - Initial"
    MANAGED = "2 - Managed"
    DEFINED = "3 - Defined"
    QUANTITATIVELY_MANAGED = "4 - Quantitatively Managed"
    OPTIMIZING = "5 - Optimizing"


class AutomationLevel(str, Enum):
    MANUAL = "Manual"
    SEMI_AUTOMATED = "Semi-Automated"
    AUTOMATED = "Automated"
    FULLY_AUTOMATED = "Fully Automated"


class EvidenceQuality(str, Enum):
    POOR = "1 - Poor"
    FAIR = "2 - Fair"
    GOOD = "3 - Good"
    EXCELLENT = "4 - Excellent"
    COMPREHENSIVE = "5 - Comprehensive"


# Incident Enums
class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentType(str, Enum):
    SECURITY_BREACH = "security_breach"
    DATA_LOSS = "data_loss"
    SYSTEM_FAILURE = "system_failure"
    COMPLIANCE_VIOLATION = "compliance_violation"
    OPERATIONAL_ERROR = "operational_error"
    THIRD_PARTY_ISSUE = "third_party_issue"


# KRI Enums
class KRIStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


# Risk Enums
class RiskStatus(str, Enum):
    OPEN = "Open"
    IN_REVIEW = "In Review"
    ACCEPTED = "Accepted"
    TRANSFERRED = "Transferred"
    CLOSED = "Closed"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ReviewFrequency(str, Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    SEMI_ANNUALLY = "Semi-Annually"
    ANNUALLY = "Annually"
    BIENNIAL = "Biennial"


# Treatment Enums
class TreatmentStrategy(str, Enum):
    ACCEPT = "Accept"
    AVOID = "Avoid"
    MITIGATE = "Mitigate"
    TRANSFER = "Transfer"


class TreatmentPlanStatus(str, Enum):
    DRAFT = "Draft"
    APPROVED = "Approved"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"


class TreatmentUpdateStatus(str, Enum):
    ON_TRACK = "On Track"
    AT_RISK = "At Risk"
    DELAYED = "Delayed"
    COMPLETED = "Completed"


# Workflow Enums
class WorkflowType(str, Enum):
    RISK_TREATMENT = "risk_treatment"
    RISK_APPROVAL = "risk_approval"
    CONTROL_CHANGE = "control_change"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Authentication Source
class AuthSource(str, Enum):
    LOCAL = "local"
    AD = "ad"
    LDAP = "ldap"
    SSO = "sso"


# File Access Levels
class FileAccessLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    TOP_SECRET = "top_secret"


# Notification Delivery Methods
class NotificationMethod(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"
    WEBHOOK = "webhook"


# Risk Categories (commonly used)
class RiskCategory(str, Enum):
    STRATEGIC = "Strategic"
    OPERATIONAL = "Operational"
    FINANCIAL = "Financial"
    COMPLIANCE = "Compliance"
    REPUTATIONAL = "Reputational"
    CYBER_SECURITY = "Cyber Security"
    ENVIRONMENTAL = "Environmental"
    HEALTH_SAFETY = "Health & Safety"


# Organization Types
class OrganizationType(str, Enum):
    DIRECTORATE = "directorate"
    DEPARTMENT = "department"
    UNIT = "unit"
    STATION = "station"


# Currency Codes
class Currency(str, Enum):
    ZMW = "ZMW"  # Zambian Kwacha
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound


# Report Types
class ReportType(str, Enum):
    RISK_REGISTER = "risk_register"
    RISK_ASSESSMENT = "risk_assessment"
    INCIDENT_REPORT = "incident_report"
    COMPLIANCE_REPORT = "compliance_report"
    KRI_DASHBOARD = "kri_dashboard"
    AUDIT_REPORT = "audit_report"
    EXECUTIVE_SUMMARY = "executive_summary"


# Audit Actions
class AuditAction(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ASSIGN = "ASSIGN"
    ESCALATE = "ESCALATE"