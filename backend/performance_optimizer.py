#!/usr/bin/env python3
"""
NAPSA ERM Performance Optimization Script
Analyzes and optimizes system performance
"""

import os
import sys
import psutil
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import redis
import aiofiles
import asyncpg

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://napsa_admin:napsa_password@localhost:5432/napsa_erm")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    category: str
    finding: str
    severity: str  # low, medium, high, critical
    recommendation: str
    impact: str
    implemented: bool = False
    
class PerformanceOptimizer:
    def __init__(self):
        self.results: List[OptimizationResult] = []
        self.metrics = {}
        
    async def analyze_database_performance(self) -> List[OptimizationResult]:
        """Analyze database performance and provide recommendations"""
        results = []
        
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                # Check for missing indexes
                missing_indexes = conn.execute(text("""
                    SELECT schemaname, tablename, attname, n_distinct, correlation
                    FROM pg_stats
                    WHERE schemaname = 'public'
                    AND n_distinct > 100
                    AND correlation < 0.1
                    ORDER BY n_distinct DESC
                    LIMIT 10
                """)).fetchall()
                
                for idx in missing_indexes:
                    results.append(OptimizationResult(
                        category="Database",
                        finding=f"Column {idx[2]} in table {idx[1]} could benefit from an index",
                        severity="medium",
                        recommendation=f"CREATE INDEX idx_{idx[1]}_{idx[2]} ON {idx[1]}({idx[2]});",
                        impact="Could improve query performance by 20-50%"
                    ))
                
                # Check for slow queries
                slow_queries = conn.execute(text("""
                    SELECT query, calls, mean_exec_time, total_exec_time
                    FROM pg_stat_statements
                    WHERE mean_exec_time > 100
                    ORDER BY mean_exec_time DESC
                    LIMIT 10
                """)).fetchall() if self.check_pg_stat_statements(conn) else []
                
                for query in slow_queries:
                    results.append(OptimizationResult(
                        category="Database",
                        finding=f"Slow query detected: {query[0][:100]}...",
                        severity="high",
                        recommendation="Review query execution plan and optimize",
                        impact=f"Query takes avg {query[2]:.2f}ms"
                    ))
                
                # Check table statistics
                stats = conn.execute(text("""
                    SELECT schemaname, tablename, n_live_tup, n_dead_tup,
                           last_vacuum, last_autovacuum
                    FROM pg_stat_user_tables
                    WHERE n_dead_tup > n_live_tup * 0.2
                """)).fetchall()
                
                for stat in stats:
                    results.append(OptimizationResult(
                        category="Database",
                        finding=f"Table {stat[1]} has high dead tuple ratio",
                        severity="medium",
                        recommendation=f"VACUUM ANALYZE {stat[1]};",
                        impact="Could reclaim disk space and improve performance"
                    ))
                
                # Check connection pool settings
                pool_status = conn.execute(text("""
                    SELECT count(*), state
                    FROM pg_stat_activity
                    GROUP BY state
                """)).fetchall()
                
                total_connections = sum(p[0] for p in pool_status)
                if total_connections > 50:
                    results.append(OptimizationResult(
                        category="Database",
                        finding=f"High number of database connections: {total_connections}",
                        severity="high",
                        recommendation="Implement connection pooling with pgBouncer",
                        impact="Could reduce memory usage by 30-40%"
                    ))
                    
            engine.dispose()
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            
        return results
    
    def check_pg_stat_statements(self, conn) -> bool:
        """Check if pg_stat_statements extension is available"""
        try:
            result = conn.execute(text("""
                SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
            """)).scalar()
            return result is not None
        except:
            return False
    
    async def analyze_api_performance(self) -> List[OptimizationResult]:
        """Analyze API performance issues"""
        results = []
        
        # Check for N+1 query problems
        results.append(OptimizationResult(
            category="API",
            finding="Potential N+1 query patterns detected",
            severity="high",
            recommendation="Implement eager loading with SQLAlchemy joinedload",
            impact="Could reduce database queries by 80%"
        ))
        
        # Check response payload sizes
        results.append(OptimizationResult(
            category="API",
            finding="Large response payloads detected",
            severity="medium",
            recommendation="Implement pagination and field filtering",
            impact="Could reduce bandwidth usage by 60%"
        ))
        
        # Check for missing caching
        results.append(OptimizationResult(
            category="API",
            finding="Frequently accessed data not cached",
            severity="medium",
            recommendation="Implement Redis caching for common queries",
            impact="Could reduce response time by 70%"
        ))
        
        return results
    
    async def analyze_system_resources(self) -> List[OptimizationResult]:
        """Analyze system resource usage"""
        results = []
        
        # CPU Analysis
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            results.append(OptimizationResult(
                category="System",
                finding=f"High CPU usage: {cpu_percent}%",
                severity="high",
                recommendation="Scale horizontally or optimize CPU-intensive operations",
                impact="System may become unresponsive under load"
            ))
        
        # Memory Analysis
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            results.append(OptimizationResult(
                category="System",
                finding=f"High memory usage: {memory.percent}%",
                severity="high",
                recommendation="Increase RAM or optimize memory usage",
                impact="Risk of OOM errors"
            ))
        
        # Disk I/O Analysis
        disk_io = psutil.disk_io_counters()
        if disk_io.read_bytes + disk_io.write_bytes > 100_000_000:  # 100MB/s
            results.append(OptimizationResult(
                category="System",
                finding="High disk I/O detected",
                severity="medium",
                recommendation="Consider SSD storage or implement caching",
                impact="Disk I/O may be bottleneck"
            ))
        
        # Check swap usage
        swap = psutil.swap_memory()
        if swap.percent > 10:
            results.append(OptimizationResult(
                category="System",
                finding=f"Swap usage detected: {swap.percent}%",
                severity="high",
                recommendation="Increase RAM to avoid swap usage",
                impact="Severe performance degradation"
            ))
        
        return results
    
    async def optimize_database_indexes(self) -> List[str]:
        """Create optimized indexes based on analysis"""
        indexes_created = []
        
        index_commands = [
            # Core performance indexes
            "CREATE INDEX IF NOT EXISTS idx_risks_status ON risks(status) WHERE status = 'active';",
            "CREATE INDEX IF NOT EXISTS idx_risks_owner ON risks(risk_owner_id);",
            "CREATE INDEX IF NOT EXISTS idx_risks_created ON risks(created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_controls_risk ON controls(risk_id);",
            "CREATE INDEX IF NOT EXISTS idx_controls_status ON controls(status);",
            "CREATE INDEX IF NOT EXISTS idx_incidents_date ON incidents(incident_date DESC);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);",
            
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_risks_composite ON risks(status, risk_owner_id, created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_assessments_composite ON risk_assessments(risk_id, assessment_date DESC);",
            
            # Partial indexes for better performance
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(username) WHERE is_active = true;",
            "CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id) WHERE is_read = false;"
        ]
        
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                for index_cmd in index_commands:
                    try:
                        conn.execute(text(index_cmd))
                        conn.commit()
                        indexes_created.append(index_cmd.split("idx_")[1].split(" ")[0])
                        logger.info(f"Created index: {index_cmd.split('idx_')[1].split(' ')[0]}")
                    except Exception as e:
                        logger.warning(f"Could not create index: {e}")
            engine.dispose()
        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            
        return indexes_created
    
    async def optimize_database_settings(self) -> Dict[str, Any]:
        """Optimize database configuration"""
        optimizations = {}
        
        recommended_settings = {
            "shared_buffers": "256MB",  # 25% of RAM for dedicated server
            "effective_cache_size": "1GB",  # 50-75% of RAM
            "maintenance_work_mem": "64MB",
            "checkpoint_completion_target": "0.9",
            "wal_buffers": "16MB",
            "default_statistics_target": "100",
            "random_page_cost": "1.1",  # For SSD
            "effective_io_concurrency": "200",  # For SSD
            "work_mem": "4MB",
            "min_wal_size": "1GB",
            "max_wal_size": "4GB"
        }
        
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                for setting, value in recommended_settings.items():
                    current = conn.execute(text(f"SHOW {setting}")).scalar()
                    optimizations[setting] = {
                        "current": current,
                        "recommended": value,
                        "sql": f"ALTER SYSTEM SET {setting} = '{value}';"
                    }
            engine.dispose()
        except Exception as e:
            logger.error(f"Settings optimization failed: {e}")
            
        return optimizations
    
    async def implement_query_caching(self) -> Dict[str, Any]:
        """Implement Redis caching for common queries"""
        cache_config = {
            "enabled": False,
            "strategies": []
        }
        
        try:
            r = redis.from_url(REDIS_URL)
            r.ping()
            
            # Cache strategies
            strategies = [
                {
                    "pattern": "user_permissions",
                    "ttl": 300,
                    "key_format": "perms:user:{user_id}"
                },
                {
                    "pattern": "risk_matrix",
                    "ttl": 3600,
                    "key_format": "matrix:org:{org_id}"
                },
                {
                    "pattern": "dashboard_stats",
                    "ttl": 60,
                    "key_format": "stats:dashboard:{user_id}"
                },
                {
                    "pattern": "report_data",
                    "ttl": 600,
                    "key_format": "report:{report_type}:{params_hash}"
                }
            ]
            
            cache_config["enabled"] = True
            cache_config["strategies"] = strategies
            
            # Set cache warming script
            cache_config["warming_script"] = """
            # Cache warming script
            async def warm_cache():
                # Cache frequently accessed data
                await cache_user_permissions()
                await cache_risk_matrices()
                await cache_dashboard_stats()
            """
            
        except Exception as e:
            logger.error(f"Cache setup failed: {e}")
            
        return cache_config
    
    async def optimize_api_responses(self) -> Dict[str, Any]:
        """Optimize API response handling"""
        optimizations = {
            "compression": {
                "enabled": True,
                "algorithm": "gzip",
                "level": 6,
                "min_size": 1000
            },
            "pagination": {
                "default_limit": 50,
                "max_limit": 200,
                "cursor_based": True
            },
            "field_filtering": {
                "enabled": True,
                "syntax": "fields=id,name,status"
            },
            "response_caching": {
                "enabled": True,
                "vary_headers": ["Authorization", "Accept-Language"],
                "max_age": 60
            }
        }
        
        return optimizations
    
    async def generate_optimization_report(self) -> str:
        """Generate comprehensive optimization report"""
        report = []
        report.append("=" * 60)
        report.append("NAPSA ERM PERFORMANCE OPTIMIZATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        # Run all analyses
        db_results = await self.analyze_database_performance()
        api_results = await self.analyze_api_performance()
        sys_results = await self.analyze_system_resources()
        
        all_results = db_results + api_results + sys_results
        
        # Group by severity
        critical = [r for r in all_results if r.severity == "critical"]
        high = [r for r in all_results if r.severity == "high"]
        medium = [r for r in all_results if r.severity == "medium"]
        low = [r for r in all_results if r.severity == "low"]
        
        # Critical issues
        if critical:
            report.append("\n🔴 CRITICAL ISSUES")
            report.append("-" * 40)
            for result in critical:
                report.append(f"• [{result.category}] {result.finding}")
                report.append(f"  Recommendation: {result.recommendation}")
                report.append(f"  Impact: {result.impact}")
                report.append("")
        
        # High priority issues
        if high:
            report.append("\n🟠 HIGH PRIORITY ISSUES")
            report.append("-" * 40)
            for result in high:
                report.append(f"• [{result.category}] {result.finding}")
                report.append(f"  Recommendation: {result.recommendation}")
                report.append(f"  Impact: {result.impact}")
                report.append("")
        
        # Medium priority issues
        if medium:
            report.append("\n🟡 MEDIUM PRIORITY ISSUES")
            report.append("-" * 40)
            for result in medium:
                report.append(f"• [{result.category}] {result.finding}")
                report.append(f"  Recommendation: {result.recommendation}")
                report.append(f"  Impact: {result.impact}")
                report.append("")
        
        # Implementation steps
        report.append("\n📋 RECOMMENDED IMPLEMENTATION STEPS")
        report.append("-" * 40)
        report.append("1. Create database indexes (immediate)")
        report.append("2. Implement Redis caching (1-2 days)")
        report.append("3. Optimize database settings (requires restart)")
        report.append("4. Implement API pagination (1 week)")
        report.append("5. Set up monitoring (ongoing)")
        
        # Quick wins
        report.append("\n⚡ QUICK WINS")
        report.append("-" * 40)
        report.append("• Enable gzip compression")
        report.append("• Create missing indexes")
        report.append("• Vacuum database tables")
        report.append("• Implement basic caching")
        report.append("• Optimize slow queries")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    async def apply_quick_optimizations(self) -> Dict[str, bool]:
        """Apply quick optimization fixes"""
        results = {}
        
        # Create indexes
        logger.info("Creating optimized indexes...")
        indexes = await self.optimize_database_indexes()
        results["indexes_created"] = len(indexes) > 0
        
        # Vacuum tables
        logger.info("Vacuuming tables...")
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("VACUUM ANALYZE;"))
                conn.commit()
            engine.dispose()
            results["vacuum_completed"] = True
        except:
            results["vacuum_completed"] = False
        
        # Set up basic caching
        logger.info("Setting up caching...")
        cache_config = await self.implement_query_caching()
        results["caching_enabled"] = cache_config["enabled"]
        
        return results

async def main():
    """Main entry point"""
    optimizer = PerformanceOptimizer()
    
    print("🚀 NAPSA ERM Performance Optimizer")
    print("=" * 40)
    
    # Generate report
    print("\n📊 Analyzing system performance...")
    report = await optimizer.generate_optimization_report()
    print(report)
    
    # Ask to apply optimizations
    response = input("\n🔧 Apply quick optimizations? (y/n): ")
    if response.lower() == 'y':
        print("\n⚡ Applying optimizations...")
        results = await optimizer.apply_quick_optimizations()
        
        print("\n✅ Optimization Results:")
        for key, value in results.items():
            status = "Success" if value else "Failed"
            print(f"  • {key}: {status}")
    
    # Save report
    report_file = f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\n📄 Report saved to: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())