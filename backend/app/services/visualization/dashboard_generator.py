"""
Advanced Visualization and Business Intelligence Dashboard Generator
Provides comprehensive BI dashboards, interactive visualizations, and executive reporting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.clickhouse import get_clickhouse_client

logger = logging.getLogger(__name__)

class ChartType(Enum):
    """Supported chart types"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TREEMAP = "treemap"
    SANKEY = "sankey"
    HISTOGRAM = "histogram"
    BOX = "box"
    AREA = "area"
    DONUT = "donut"
    FUNNEL = "funnel"
    WATERFALL = "waterfall"
    BUBBLE = "bubble"

class DashboardType(Enum):
    """Dashboard types"""
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    RISK_MANAGEMENT = "risk_management"
    AML_COMPLIANCE = "aml_compliance"
    CUSTOMER_ANALYTICS = "customer_analytics"
    TRANSACTION_MONITORING = "transaction_monitoring"
    PERFORMANCE = "performance"
    REGULATORY = "regulatory"

@dataclass
class ChartConfiguration:
    """Chart configuration"""
    chart_id: str
    title: str
    chart_type: ChartType
    data_source: str
    x_axis: str
    y_axis: str
    color_scheme: str = "default"
    filters: Dict[str, Any] = None
    aggregation: str = None
    time_period: str = None
    drill_down_enabled: bool = True
    real_time: bool = False

@dataclass
class DashboardWidget:
    """Dashboard widget definition"""
    widget_id: str
    title: str
    widget_type: str  # chart, metric, table, text
    chart_config: Optional[ChartConfiguration] = None
    position: Dict[str, int] = None  # x, y, width, height
    refresh_interval: int = 300  # seconds
    data: Any = None

@dataclass
class Dashboard:
    """Dashboard definition"""
    dashboard_id: str
    title: str
    description: str
    dashboard_type: DashboardType
    widgets: List[DashboardWidget]
    layout: Dict[str, Any]
    access_level: str = "user"  # user, admin, executive
    refresh_interval: int = 300
    created_at: datetime = None
    updated_at: datetime = None

class VisualizationEngine:
    """Core visualization engine"""
    
    def __init__(self):
        self.clickhouse_client = None
        try:
            self.clickhouse_client = get_clickhouse_client()
        except Exception as e:
            logger.warning(f"ClickHouse not available: {e}")
    
    def generate_chart_data(self, config: ChartConfiguration, db: Session) -> Dict[str, Any]:
        """Generate data for a chart based on configuration"""
        try:
            if config.data_source.startswith("clickhouse:"):
                return self._query_clickhouse(config)
            else:
                return self._query_postgresql(config, db)
        except Exception as e:
            logger.error(f"Error generating chart data: {e}")
            return {"error": str(e), "data": []}
    
    def _query_clickhouse(self, config: ChartConfiguration) -> Dict[str, Any]:
        """Query ClickHouse for chart data"""
        if not self.clickhouse_client:
            return {"error": "ClickHouse not available", "data": []}
        
        try:
            query = self._build_clickhouse_query(config)
            result = self.clickhouse_client.execute(query)
            
            # Convert to chart-friendly format
            if config.chart_type == ChartType.PIE:
                return self._format_pie_data(result, config)
            elif config.chart_type == ChartType.LINE:
                return self._format_line_data(result, config)
            elif config.chart_type == ChartType.BAR:
                return self._format_bar_data(result, config)
            elif config.chart_type == ChartType.HEATMAP:
                return self._format_heatmap_data(result, config)
            else:
                return self._format_generic_data(result, config)
                
        except Exception as e:
            logger.error(f"ClickHouse query error: {e}")
            return {"error": str(e), "data": []}
    
    def _query_postgresql(self, config: ChartConfiguration, db: Session) -> Dict[str, Any]:
        """Query PostgreSQL for chart data"""
        try:
            query = self._build_postgresql_query(config)
            result = db.execute(text(query))
            rows = result.fetchall()
            
            # Convert to DataFrame for easier manipulation
            columns = result.keys()
            df = pd.DataFrame(rows, columns=columns)
            
            return self._format_dataframe_to_chart(df, config)
            
        except Exception as e:
            logger.error(f"PostgreSQL query error: {e}")
            return {"error": str(e), "data": []}
    
    def _build_clickhouse_query(self, config: ChartConfiguration) -> str:
        """Build ClickHouse query based on chart configuration"""
        table = config.data_source.replace("clickhouse:", "")
        
        base_query = f"SELECT {config.x_axis}, {config.y_axis}"
        
        if config.aggregation:
            if config.aggregation == "sum":
                base_query = f"SELECT {config.x_axis}, sum({config.y_axis}) as {config.y_axis}"
            elif config.aggregation == "avg":
                base_query = f"SELECT {config.x_axis}, avg({config.y_axis}) as {config.y_axis}"
            elif config.aggregation == "count":
                base_query = f"SELECT {config.x_axis}, count() as {config.y_axis}"
        
        base_query += f" FROM {table}"
        
        # Add time filtering
        if config.time_period:
            if config.time_period == "24h":
                base_query += " WHERE timestamp >= now() - INTERVAL 24 HOUR"
            elif config.time_period == "7d":
                base_query += " WHERE timestamp >= now() - INTERVAL 7 DAY"
            elif config.time_period == "30d":
                base_query += " WHERE timestamp >= now() - INTERVAL 30 DAY"
        
        # Add custom filters
        if config.filters:
            for key, value in config.filters.items():
                if isinstance(value, str):
                    base_query += f" AND {key} = '{value}'"
                else:
                    base_query += f" AND {key} = {value}"
        
        if config.aggregation:
            base_query += f" GROUP BY {config.x_axis}"
        
        base_query += f" ORDER BY {config.x_axis}"
        
        return base_query
    
    def _build_postgresql_query(self, config: ChartConfiguration) -> str:
        """Build PostgreSQL query based on chart configuration"""
        # Simplified PostgreSQL query builder
        table = config.data_source
        
        if config.aggregation == "count":
            query = f"SELECT {config.x_axis}, COUNT(*) as {config.y_axis} FROM {table}"
        else:
            query = f"SELECT {config.x_axis}, {config.y_axis} FROM {table}"
        
        # Add basic filtering and grouping
        if config.time_period:
            query += f" WHERE created_at >= NOW() - INTERVAL '{config.time_period}'"
        
        if config.aggregation:
            query += f" GROUP BY {config.x_axis}"
            
        query += f" ORDER BY {config.x_axis}"
        
        return query
    
    def _format_pie_data(self, result: List, config: ChartConfiguration) -> Dict[str, Any]:
        """Format data for pie chart"""
        data = []
        for row in result:
            data.append({
                "label": str(row[0]),
                "value": float(row[1])
            })
        
        return {
            "chart_type": "pie",
            "title": config.title,
            "data": data
        }
    
    def _format_line_data(self, result: List, config: ChartConfiguration) -> Dict[str, Any]:
        """Format data for line chart"""
        labels = []
        values = []
        
        for row in result:
            labels.append(str(row[0]))
            values.append(float(row[1]))
        
        return {
            "chart_type": "line",
            "title": config.title,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": config.y_axis,
                    "data": values,
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                }]
            }
        }
    
    def _format_bar_data(self, result: List, config: ChartConfiguration) -> Dict[str, Any]:
        """Format data for bar chart"""
        labels = []
        values = []
        
        for row in result:
            labels.append(str(row[0]))
            values.append(float(row[1]))
        
        return {
            "chart_type": "bar",
            "title": config.title,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": config.y_axis,
                    "data": values,
                    "backgroundColor": "rgba(54, 162, 235, 0.5)"
                }]
            }
        }
    
    def _format_heatmap_data(self, result: List, config: ChartConfiguration) -> Dict[str, Any]:
        """Format data for heatmap"""
        # Assuming result has x, y, value format
        data = []
        for i, row in enumerate(result):
            data.append({
                "x": str(row[0]),
                "y": str(row[1]) if len(row) > 2 else str(i),
                "v": float(row[-1])
            })
        
        return {
            "chart_type": "heatmap",
            "title": config.title,
            "data": data
        }
    
    def _format_generic_data(self, result: List, config: ChartConfiguration) -> Dict[str, Any]:
        """Format data for generic charts"""
        data = []
        for row in result:
            data.append({
                "x": str(row[0]),
                "y": float(row[1])
            })
        
        return {
            "chart_type": config.chart_type.value,
            "title": config.title,
            "data": data
        }
    
    def _format_dataframe_to_chart(self, df: pd.DataFrame, config: ChartConfiguration) -> Dict[str, Any]:
        """Format DataFrame to chart data"""
        if config.chart_type == ChartType.PIE:
            data = []
            for _, row in df.iterrows():
                data.append({
                    "label": str(row[config.x_axis]),
                    "value": float(row[config.y_axis])
                })
            return {"chart_type": "pie", "title": config.title, "data": data}
        
        elif config.chart_type in [ChartType.LINE, ChartType.BAR]:
            labels = df[config.x_axis].astype(str).tolist()
            values = df[config.y_axis].astype(float).tolist()
            
            return {
                "chart_type": config.chart_type.value,
                "title": config.title,
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": config.y_axis,
                        "data": values
                    }]
                }
            }
        
        else:
            # Generic format
            data = []
            for _, row in df.iterrows():
                data.append({
                    "x": str(row[config.x_axis]),
                    "y": float(row[config.y_axis])
                })
            
            return {
                "chart_type": config.chart_type.value,
                "title": config.title,
                "data": data
            }

class DashboardGenerator:
    """Dashboard generation and management"""
    
    def __init__(self):
        self.viz_engine = VisualizationEngine()
        self.predefined_dashboards = self._initialize_predefined_dashboards()
    
    def _initialize_predefined_dashboards(self) -> Dict[str, Dashboard]:
        """Initialize predefined dashboard templates"""
        dashboards = {}
        
        # Executive Dashboard
        executive_widgets = [
            DashboardWidget(
                widget_id="exec_overview",
                title="System Overview",
                widget_type="metrics",
                position={"x": 0, "y": 0, "width": 12, "height": 4}
            ),
            DashboardWidget(
                widget_id="risk_trends",
                title="Risk Trends (30 days)",
                widget_type="chart",
                chart_config=ChartConfiguration(
                    chart_id="risk_trends",
                    title="Risk Trends",
                    chart_type=ChartType.LINE,
                    data_source="clickhouse:risk_metrics_timeseries",
                    x_axis="date",
                    y_axis="avg_risk_score",
                    time_period="30d",
                    aggregation="avg"
                ),
                position={"x": 0, "y": 4, "width": 6, "height": 6}
            ),
            DashboardWidget(
                widget_id="alert_distribution",
                title="Alert Distribution by Severity",
                widget_type="chart",
                chart_config=ChartConfiguration(
                    chart_id="alert_dist",
                    title="Alert Distribution",
                    chart_type=ChartType.PIE,
                    data_source="clickhouse:alert_analytics",
                    x_axis="severity",
                    y_axis="count",
                    aggregation="count"
                ),
                position={"x": 6, "y": 4, "width": 6, "height": 6}
            ),
            DashboardWidget(
                widget_id="transaction_volume",
                title="Daily Transaction Volume",
                widget_type="chart",
                chart_config=ChartConfiguration(
                    chart_id="tx_volume",
                    title="Transaction Volume",
                    chart_type=ChartType.AREA,
                    data_source="clickhouse:transactions_analytics",
                    x_axis="date",
                    y_axis="transaction_count",
                    time_period="30d",
                    aggregation="sum"
                ),
                position={"x": 0, "y": 10, "width": 12, "height": 6}
            )
        ]
        
        dashboards["executive"] = Dashboard(
            dashboard_id="executive",
            title="Executive Dashboard",
            description="High-level overview for executives",
            dashboard_type=DashboardType.EXECUTIVE,
            widgets=executive_widgets,
            layout={"columns": 12, "rows": 16},
            access_level="executive"
        )
        
        # AML Compliance Dashboard
        aml_widgets = [
            DashboardWidget(
                widget_id="aml_alerts",
                title="AML Alerts Today",
                widget_type="metric",
                position={"x": 0, "y": 0, "width": 3, "height": 2}
            ),
            DashboardWidget(
                widget_id="suspicious_patterns",
                title="Suspicious Pattern Detection",
                widget_type="chart",
                chart_config=ChartConfiguration(
                    chart_id="patterns",
                    title="Pattern Detection",
                    chart_type=ChartType.BAR,
                    data_source="clickhouse:transactions_analytics",
                    x_axis="pattern_type",
                    y_axis="count",
                    time_period="7d",
                    aggregation="count"
                ),
                position={"x": 3, "y": 0, "width": 9, "height": 8}
            ),
            DashboardWidget(
                widget_id="high_risk_customers",
                title="High Risk Customers",
                widget_type="table",
                position={"x": 0, "y": 8, "width": 12, "height": 6}
            )
        ]
        
        dashboards["aml_compliance"] = Dashboard(
            dashboard_id="aml_compliance",
            title="AML Compliance Dashboard",
            description="Anti-Money Laundering compliance monitoring",
            dashboard_type=DashboardType.AML_COMPLIANCE,
            widgets=aml_widgets,
            layout={"columns": 12, "rows": 14},
            access_level="user"
        )
        
        # Risk Management Dashboard
        risk_widgets = [
            DashboardWidget(
                widget_id="risk_heatmap",
                title="Risk Heatmap",
                widget_type="chart",
                chart_config=ChartConfiguration(
                    chart_id="risk_heatmap",
                    title="Risk Distribution",
                    chart_type=ChartType.HEATMAP,
                    data_source="risks",
                    x_axis="category",
                    y_axis="impact_level"
                ),
                position={"x": 0, "y": 0, "width": 8, "height": 8}
            ),
            DashboardWidget(
                widget_id="risk_metrics",
                title="Key Risk Indicators",
                widget_type="gauge",
                position={"x": 8, "y": 0, "width": 4, "height": 8}
            )
        ]
        
        dashboards["risk_management"] = Dashboard(
            dashboard_id="risk_management",
            title="Risk Management Dashboard",
            description="Comprehensive risk monitoring and analysis",
            dashboard_type=DashboardType.RISK_MANAGEMENT,
            widgets=risk_widgets,
            layout={"columns": 12, "rows": 12},
            access_level="user"
        )
        
        return dashboards
    
    def generate_dashboard(self, dashboard_id: str, db: Session, 
                         user_access_level: str = "user") -> Dashboard:
        """Generate a complete dashboard with data"""
        try:
            if dashboard_id not in self.predefined_dashboards:
                raise ValueError(f"Dashboard {dashboard_id} not found")
            
            dashboard = self.predefined_dashboards[dashboard_id]
            
            # Check access level
            if dashboard.access_level == "executive" and user_access_level != "executive":
                raise PermissionError("Insufficient access level")
            
            # Generate data for each widget
            for widget in dashboard.widgets:
                if widget.chart_config:
                    widget.data = self.viz_engine.generate_chart_data(widget.chart_config, db)
                elif widget.widget_type == "metric":
                    widget.data = self._generate_metric_data(widget.widget_id, db)
                elif widget.widget_type == "table":
                    widget.data = self._generate_table_data(widget.widget_id, db)
            
            dashboard.updated_at = datetime.now()
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            raise
    
    def _generate_metric_data(self, widget_id: str, db: Session) -> Dict[str, Any]:
        """Generate data for metric widgets"""
        try:
            if widget_id == "aml_alerts":
                # Count alerts for today
                query = """
                SELECT COUNT(*) as count
                FROM alerts 
                WHERE DATE(created_at) = CURRENT_DATE
                """
                result = db.execute(text(query)).fetchone()
                return {
                    "value": result[0] if result else 0,
                    "label": "Today's Alerts",
                    "trend": "stable",
                    "color": "blue"
                }
            
            elif widget_id == "exec_overview":
                # Multiple metrics for executive overview
                return {
                    "metrics": [
                        {"label": "Total Customers", "value": 1250, "change": "+5.2%"},
                        {"label": "Monthly Transactions", "value": "2.4M", "change": "+12.1%"},
                        {"label": "Risk Score", "value": "7.2", "change": "-2.1%"},
                        {"label": "Compliance Rate", "value": "98.7%", "change": "+0.3%"}
                    ]
                }
            
            return {"value": 0, "label": "No Data"}
            
        except Exception as e:
            logger.error(f"Error generating metric data: {e}")
            return {"value": 0, "label": "Error", "error": str(e)}
    
    def _generate_table_data(self, widget_id: str, db: Session) -> Dict[str, Any]:
        """Generate data for table widgets"""
        try:
            if widget_id == "high_risk_customers":
                query = """
                SELECT 
                    c.id,
                    c.first_name || ' ' || c.last_name as name,
                    c.risk_score,
                    COUNT(t.id) as transaction_count,
                    SUM(t.amount) as total_amount
                FROM customers c
                LEFT JOIN transactions t ON c.id = t.customer_id
                WHERE c.risk_score > 70
                GROUP BY c.id, c.first_name, c.last_name, c.risk_score
                ORDER BY c.risk_score DESC
                LIMIT 10
                """
                
                result = db.execute(text(query)).fetchall()
                
                columns = ["ID", "Name", "Risk Score", "Transactions", "Total Amount"]
                rows = []
                
                for row in result:
                    rows.append([
                        row[0],
                        row[1],
                        f"{row[2]:.1f}",
                        row[3],
                        f"${row[4]:,.2f}" if row[4] else "$0.00"
                    ])
                
                return {
                    "columns": columns,
                    "rows": rows
                }
            
            return {"columns": [], "rows": []}
            
        except Exception as e:
            logger.error(f"Error generating table data: {e}")
            return {"columns": ["Error"], "rows": [[str(e)]]}
    
    def get_available_dashboards(self) -> List[Dict[str, Any]]:
        """Get list of available dashboards"""
        dashboards = []
        for dashboard_id, dashboard in self.predefined_dashboards.items():
            dashboards.append({
                "id": dashboard_id,
                "title": dashboard.title,
                "description": dashboard.description,
                "type": dashboard.dashboard_type.value,
                "access_level": dashboard.access_level,
                "widget_count": len(dashboard.widgets)
            })
        
        return dashboards
    
    def create_custom_dashboard(self, title: str, description: str, 
                              widgets: List[DashboardWidget], 
                              layout: Dict[str, Any]) -> Dashboard:
        """Create a custom dashboard"""
        dashboard_id = f"custom_{int(datetime.now().timestamp())}"
        
        dashboard = Dashboard(
            dashboard_id=dashboard_id,
            title=title,
            description=description,
            dashboard_type=DashboardType.OPERATIONAL,
            widgets=widgets,
            layout=layout,
            created_at=datetime.now()
        )
        
        # Store in predefined dashboards (in production, this would be in database)
        self.predefined_dashboards[dashboard_id] = dashboard
        
        return dashboard
    
    def export_dashboard_config(self, dashboard_id: str) -> Dict[str, Any]:
        """Export dashboard configuration as JSON"""
        if dashboard_id not in self.predefined_dashboards:
            raise ValueError(f"Dashboard {dashboard_id} not found")
        
        dashboard = self.predefined_dashboards[dashboard_id]
        
        # Convert to serializable format
        config = {
            "dashboard_id": dashboard.dashboard_id,
            "title": dashboard.title,
            "description": dashboard.description,
            "dashboard_type": dashboard.dashboard_type.value,
            "layout": dashboard.layout,
            "access_level": dashboard.access_level,
            "widgets": []
        }
        
        for widget in dashboard.widgets:
            widget_config = {
                "widget_id": widget.widget_id,
                "title": widget.title,
                "widget_type": widget.widget_type,
                "position": widget.position,
                "refresh_interval": widget.refresh_interval
            }
            
            if widget.chart_config:
                widget_config["chart_config"] = {
                    "chart_id": widget.chart_config.chart_id,
                    "title": widget.chart_config.title,
                    "chart_type": widget.chart_config.chart_type.value,
                    "data_source": widget.chart_config.data_source,
                    "x_axis": widget.chart_config.x_axis,
                    "y_axis": widget.chart_config.y_axis,
                    "color_scheme": widget.chart_config.color_scheme,
                    "filters": widget.chart_config.filters,
                    "aggregation": widget.chart_config.aggregation,
                    "time_period": widget.chart_config.time_period
                }
            
            config["widgets"].append(widget_config)
        
        return config

# Global dashboard generator instance
dashboard_generator = None

def get_dashboard_generator() -> DashboardGenerator:
    """Get the global dashboard generator instance"""
    global dashboard_generator
    if dashboard_generator is None:
        dashboard_generator = DashboardGenerator()
    return dashboard_generator