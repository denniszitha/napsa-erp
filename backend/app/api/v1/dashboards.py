"""
Advanced Dashboards and Visualization API
Provides endpoints for business intelligence dashboards and interactive visualizations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.visualization import (
    get_dashboard_generator,
    ChartConfiguration,
    ChartType,
    DashboardWidget,
    DashboardType
)

router = APIRouter()

# Pydantic models for API
class ChartConfigRequest(BaseModel):
    chart_id: str
    title: str
    chart_type: str
    data_source: str
    x_axis: str
    y_axis: str
    color_scheme: str = "default"
    filters: Optional[Dict[str, Any]] = None
    aggregation: Optional[str] = None
    time_period: Optional[str] = None

class DashboardWidgetRequest(BaseModel):
    widget_id: str
    title: str
    widget_type: str
    chart_config: Optional[ChartConfigRequest] = None
    position: Dict[str, int]
    refresh_interval: int = 300

class CreateDashboardRequest(BaseModel):
    title: str
    description: str
    widgets: List[DashboardWidgetRequest]
    layout: Dict[str, Any]

class DashboardResponse(BaseModel):
    dashboard_id: str
    title: str
    description: str
    dashboard_type: str
    layout: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    updated_at: str

@router.get("/available")
def get_available_dashboards(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available dashboards
    """
    try:
        dashboard_gen = get_dashboard_generator()
        dashboards = dashboard_gen.get_available_dashboards()
        
        # Filter by user access level
        user_access = "executive" if current_user.is_superuser else "user"
        accessible_dashboards = [
            d for d in dashboards 
            if d["access_level"] == "user" or 
               (d["access_level"] == "executive" and user_access == "executive")
        ]
        
        return {
            "dashboards": accessible_dashboards,
            "user_access_level": user_access
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboards: {str(e)}")

@router.get("/{dashboard_id}")
def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific dashboard with data
    """
    try:
        dashboard_gen = get_dashboard_generator()
        user_access = "executive" if current_user.is_superuser else "user"
        
        dashboard = dashboard_gen.generate_dashboard(dashboard_id, db, user_access)
        
        # Convert to response format
        widgets_data = []
        for widget in dashboard.widgets:
            widget_data = {
                "widget_id": widget.widget_id,
                "title": widget.title,
                "widget_type": widget.widget_type,
                "position": widget.position,
                "refresh_interval": widget.refresh_interval,
                "data": widget.data
            }
            
            if widget.chart_config:
                widget_data["chart_config"] = {
                    "chart_id": widget.chart_config.chart_id,
                    "title": widget.chart_config.title,
                    "chart_type": widget.chart_config.chart_type.value,
                    "data_source": widget.chart_config.data_source,
                    "x_axis": widget.chart_config.x_axis,
                    "y_axis": widget.chart_config.y_axis
                }
            
            widgets_data.append(widget_data)
        
        return {
            "dashboard_id": dashboard.dashboard_id,
            "title": dashboard.title,
            "description": dashboard.description,
            "dashboard_type": dashboard.dashboard_type.value,
            "layout": dashboard.layout,
            "access_level": dashboard.access_level,
            "widgets": widgets_data,
            "updated_at": dashboard.updated_at.isoformat() if dashboard.updated_at else None,
            "refresh_interval": dashboard.refresh_interval
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")

@router.post("/create")
def create_custom_dashboard(
    request: CreateDashboardRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a custom dashboard
    """
    try:
        dashboard_gen = get_dashboard_generator()
        
        # Convert request to widgets
        widgets = []
        for widget_req in request.widgets:
            chart_config = None
            if widget_req.chart_config:
                chart_config = ChartConfiguration(
                    chart_id=widget_req.chart_config.chart_id,
                    title=widget_req.chart_config.title,
                    chart_type=ChartType(widget_req.chart_config.chart_type),
                    data_source=widget_req.chart_config.data_source,
                    x_axis=widget_req.chart_config.x_axis,
                    y_axis=widget_req.chart_config.y_axis,
                    color_scheme=widget_req.chart_config.color_scheme,
                    filters=widget_req.chart_config.filters,
                    aggregation=widget_req.chart_config.aggregation,
                    time_period=widget_req.chart_config.time_period
                )
            
            widget = DashboardWidget(
                widget_id=widget_req.widget_id,
                title=widget_req.title,
                widget_type=widget_req.widget_type,
                chart_config=chart_config,
                position=widget_req.position,
                refresh_interval=widget_req.refresh_interval
            )
            widgets.append(widget)
        
        dashboard = dashboard_gen.create_custom_dashboard(
            title=request.title,
            description=request.description,
            widgets=widgets,
            layout=request.layout
        )
        
        return {
            "status": "success",
            "dashboard_id": dashboard.dashboard_id,
            "message": "Custom dashboard created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard: {str(e)}")

@router.get("/{dashboard_id}/export")
def export_dashboard_config(
    dashboard_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Export dashboard configuration as JSON
    """
    try:
        dashboard_gen = get_dashboard_generator()
        config = dashboard_gen.export_dashboard_config(dashboard_id)
        
        return {
            "dashboard_config": config,
            "exported_at": datetime.now().isoformat(),
            "exported_by": current_user.email
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export dashboard: {str(e)}")

@router.get("/{dashboard_id}/widget/{widget_id}/refresh")
def refresh_widget_data(
    dashboard_id: str,
    widget_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Refresh data for a specific widget
    """
    try:
        dashboard_gen = get_dashboard_generator()
        user_access = "executive" if current_user.is_superuser else "user"
        
        dashboard = dashboard_gen.generate_dashboard(dashboard_id, db, user_access)
        
        # Find the specific widget
        target_widget = None
        for widget in dashboard.widgets:
            if widget.widget_id == widget_id:
                target_widget = widget
                break
        
        if not target_widget:
            raise HTTPException(status_code=404, detail=f"Widget {widget_id} not found")
        
        return {
            "widget_id": widget_id,
            "title": target_widget.title,
            "widget_type": target_widget.widget_type,
            "data": target_widget.data,
            "refreshed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh widget: {str(e)}")

@router.get("/chart-types")
def get_available_chart_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available chart types for dashboard creation
    """
    chart_types = []
    for chart_type in ChartType:
        chart_types.append({
            "value": chart_type.value,
            "label": chart_type.value.title().replace("_", " "),
            "description": f"{chart_type.value.title()} chart visualization"
        })
    
    return {
        "chart_types": chart_types,
        "total_types": len(chart_types)
    }

@router.get("/data-sources")
def get_available_data_sources(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available data sources for dashboard widgets
    """
    data_sources = [
        {
            "id": "clickhouse:transactions_analytics",
            "name": "Transaction Analytics",
            "description": "High-performance transaction analytics data",
            "type": "clickhouse",
            "fields": ["date", "amount", "customer_id", "country", "transaction_count"]
        },
        {
            "id": "clickhouse:customer_risk_analytics", 
            "name": "Customer Risk Analytics",
            "description": "Customer risk assessment data",
            "type": "clickhouse",
            "fields": ["customer_id", "risk_score", "date", "transaction_count"]
        },
        {
            "id": "clickhouse:alert_analytics",
            "name": "Alert Analytics",
            "description": "Alert and monitoring data",
            "type": "clickhouse", 
            "fields": ["date", "severity", "alert_type", "count", "resolution_time"]
        },
        {
            "id": "customers",
            "name": "Customers",
            "description": "Customer master data",
            "type": "postgresql",
            "fields": ["id", "first_name", "last_name", "risk_score", "created_at"]
        },
        {
            "id": "transactions",
            "name": "Transactions",
            "description": "Transaction records",
            "type": "postgresql",
            "fields": ["id", "amount", "customer_id", "transaction_date", "country"]
        },
        {
            "id": "alerts",
            "name": "Alerts",
            "description": "System alerts and notifications",
            "type": "postgresql",
            "fields": ["id", "title", "severity", "created_at", "resolved_at"]
        }
    ]
    
    return {
        "data_sources": data_sources,
        "total_sources": len(data_sources)
    }

@router.post("/analyze/data")
def analyze_data_for_visualization(
    data_source: str,
    fields: List[str] = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze data source to suggest optimal visualizations
    """
    try:
        # Simple analysis based on field types and data characteristics
        suggestions = []
        
        # Check for time-series data
        time_fields = [f for f in fields if 'date' in f.lower() or 'time' in f.lower()]
        numeric_fields = [f for f in fields if f in ['amount', 'count', 'score', 'risk_score']]
        categorical_fields = [f for f in fields if f in ['country', 'type', 'severity', 'category']]
        
        if time_fields and numeric_fields:
            suggestions.append({
                "chart_type": "line",
                "title": f"{numeric_fields[0].title()} Over Time",
                "x_axis": time_fields[0],
                "y_axis": numeric_fields[0],
                "reasoning": "Time series data is best visualized with line charts"
            })
            
            suggestions.append({
                "chart_type": "area",
                "title": f"Cumulative {numeric_fields[0].title()}",
                "x_axis": time_fields[0],
                "y_axis": numeric_fields[0],
                "reasoning": "Area charts show trends and cumulative values well"
            })
        
        if categorical_fields and numeric_fields:
            suggestions.append({
                "chart_type": "bar",
                "title": f"{numeric_fields[0].title()} by {categorical_fields[0].title()}",
                "x_axis": categorical_fields[0],
                "y_axis": numeric_fields[0],
                "reasoning": "Bar charts are ideal for comparing values across categories"
            })
            
            suggestions.append({
                "chart_type": "pie",
                "title": f"Distribution by {categorical_fields[0].title()}",
                "x_axis": categorical_fields[0],
                "y_axis": numeric_fields[0],
                "reasoning": "Pie charts show proportion of total for categorical data"
            })
        
        if len(numeric_fields) >= 2:
            suggestions.append({
                "chart_type": "scatter",
                "title": f"{numeric_fields[0].title()} vs {numeric_fields[1].title()}",
                "x_axis": numeric_fields[0],
                "y_axis": numeric_fields[1],
                "reasoning": "Scatter plots reveal correlations between numeric variables"
            })
        
        # Default suggestions if no specific patterns found
        if not suggestions:
            suggestions.append({
                "chart_type": "table",
                "title": f"{data_source.title()} Data Table",
                "reasoning": "Tabular format is suitable for detailed data examination"
            })
        
        return {
            "data_source": data_source,
            "analyzed_fields": fields,
            "field_analysis": {
                "time_fields": time_fields,
                "numeric_fields": numeric_fields,
                "categorical_fields": categorical_fields
            },
            "visualization_suggestions": suggestions,
            "total_suggestions": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze data: {str(e)}")

@router.get("/templates")
def get_dashboard_templates(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available dashboard templates
    """
    templates = [
        {
            "id": "executive",
            "name": "Executive Dashboard",
            "description": "High-level KPIs and metrics for executives",
            "category": "Executive",
            "widgets": ["system_overview", "risk_trends", "alert_distribution", "transaction_volume"],
            "preview_image": "/templates/executive.png"
        },
        {
            "id": "aml_compliance", 
            "name": "AML Compliance",
            "description": "Anti-Money Laundering monitoring and compliance",
            "category": "Compliance",
            "widgets": ["aml_alerts", "suspicious_patterns", "high_risk_customers"],
            "preview_image": "/templates/aml.png"
        },
        {
            "id": "risk_management",
            "name": "Risk Management", 
            "description": "Comprehensive risk assessment and monitoring",
            "category": "Risk",
            "widgets": ["risk_heatmap", "risk_metrics", "trend_analysis"],
            "preview_image": "/templates/risk.png"
        },
        {
            "id": "operational",
            "name": "Operational Dashboard",
            "description": "Day-to-day operational metrics and monitoring",
            "category": "Operations",
            "widgets": ["system_health", "performance_metrics", "user_activity"],
            "preview_image": "/templates/operational.png"
        }
    ]
    
    return {
        "templates": templates,
        "categories": list(set(t["category"] for t in templates))
    }