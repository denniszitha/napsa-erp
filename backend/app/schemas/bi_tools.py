"""
Business Intelligence Tools Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class BiDashboardResponse(BaseModel):
    summary: Dict[str, Any]
    risk_trends: List[Dict[str, Any]]
    category_distribution: List[Dict[str, Any]]
    time_range: str

class BiReportRequest(BaseModel):
    report_type: str = Field(..., description="Type of report to generate")
    filters: Dict[str, Any] = Field(default_factory=dict)
    format: str = Field("pdf", description="Output format: pdf, excel, csv")
    include_charts: bool = Field(True, description="Include charts in report")

class BiQueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    limit: Optional[int] = Field(1000, description="Maximum number of results")

class BiExportRequest(BaseModel):
    data_type: str = Field(..., description="Type of data to export: risks, assessments, controls")
    format: str = Field(..., description="Export format: excel, csv, pdf")
    filters: Dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = Field(True, description="Include metadata in export")

class BiVisualizationData(BaseModel):
    chart_type: str
    title: str
    data: List[Dict[str, Any]]
    options: Dict[str, Any] = Field(default_factory=dict)

class BiMetricsResponse(BaseModel):
    risk_velocity: float = Field(..., description="New risks per day")
    assessment_completion_rate: float = Field(..., description="Percentage of completed assessments")
    control_effectiveness_ratio: float = Field(..., description="Percentage of effective controls")
    risk_mitigation_score: float = Field(..., description="Overall risk mitigation effectiveness")
    compliance_score: float = Field(..., description="Overall compliance score")
    time_range: str

class BiTrendAnalysis(BaseModel):
    metric: str
    period: str
    time_range: str
    trends: List[Dict[str, Any]]
    growth_rate: float
    total_data_points: int

class BiRiskHeatmap(BaseModel):
    risk_id: int
    title: str
    category: str
    probability: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)
    risk_score: int = Field(..., ge=1, le=25)
    department: str

class BiComplianceScore(BaseModel):
    overall_score: float
    department_scores: List[Dict[str, Any]]
    control_effectiveness: float
    policy_adherence: float
    regulatory_compliance: float
    trend: str = Field(..., description="up, down, stable")

class BiAdvancedAnalytics(BaseModel):
    correlation_analysis: Dict[str, Any]
    predictive_insights: List[Dict[str, Any]]
    anomaly_detection: List[Dict[str, Any]]
    risk_scenarios: List[Dict[str, Any]]

class BiCustomDashboard(BaseModel):
    dashboard_id: str
    name: str
    description: Optional[str]
    widgets: List[Dict[str, Any]]
    layout: Dict[str, Any]
    filters: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: Optional[int] = Field(300, description="Refresh interval in seconds")

class BiDataSource(BaseModel):
    source_id: str
    name: str
    type: str = Field(..., description="database, api, file")
    connection_string: Optional[str]
    query: Optional[str]
    update_frequency: str = Field("daily", description="hourly, daily, weekly, monthly")
    last_updated: Optional[datetime]

class BiScheduledReport(BaseModel):
    report_id: str
    name: str
    report_type: str
    schedule: str = Field(..., description="Cron expression for scheduling")
    recipients: List[str]
    format: str = Field("pdf", description="Output format")
    filters: Dict[str, Any] = Field(default_factory=dict)
    active: bool = Field(True)

class BiAlertRule(BaseModel):
    rule_id: str
    name: str
    condition: str = Field(..., description="SQL condition for alert")
    threshold: float
    comparison: str = Field(..., description="gt, lt, eq, gte, lte")
    notification_channels: List[str]
    active: bool = Field(True)
    last_triggered: Optional[datetime]

class BiUserPreferences(BaseModel):
    user_id: int
    default_dashboard: Optional[str]
    default_time_range: str = Field("30d")
    preferred_charts: List[str] = Field(default_factory=list)
    email_notifications: bool = Field(True)
    dashboard_refresh_rate: int = Field(300, description="Refresh rate in seconds")

class BiDrillDownRequest(BaseModel):
    dimension: str = Field(..., description="Dimension to drill down into")
    filters: Dict[str, Any] = Field(default_factory=dict)
    level: int = Field(1, description="Drill down level")
    parent_value: Optional[str] = Field(None, description="Parent value for drill down")

class BiPredictiveModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str
    name: str
    model_type: str = Field(..., description="regression, classification, clustering")
    target_variable: str
    features: List[str]
    accuracy_score: Optional[float]
    last_trained: Optional[datetime]
    predictions: List[Dict[str, Any]] = Field(default_factory=list)

class BiDataQuality(BaseModel):
    table_name: str
    total_records: int
    null_percentage: float
    duplicate_percentage: float
    data_freshness: str = Field(..., description="Age of the most recent data")
    quality_score: float = Field(..., ge=0, le=100)
    issues: List[Dict[str, Any]] = Field(default_factory=list)

class BiPerformanceMetrics(BaseModel):
    query_performance: Dict[str, Any]
    dashboard_load_times: Dict[str, float]
    api_response_times: Dict[str, float]
    data_processing_times: Dict[str, float]
    cache_hit_rates: Dict[str, float]

class BiAuditLog(BaseModel):
    log_id: str
    user_id: int
    action: str
    resource: str
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str]
    user_agent: Optional[str]

class BiConfiguration(BaseModel):
    config_id: str
    name: str
    category: str
    value: Any
    description: Optional[str]
    last_modified: datetime
    modified_by: int