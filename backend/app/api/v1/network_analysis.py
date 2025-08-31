"""
Network Analysis API
Provides endpoints for graph-based network analysis and relationship mapping
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.graph import (
    get_network_analyzer,
    NodeType,
    RelationshipType
)

router = APIRouter()

# Pydantic models for API
class BuildGraphRequest(BaseModel):
    time_window_days: int = 90
    min_transaction_amount: float = 1000.0
    rebuild: bool = False

class NodeDetailsRequest(BaseModel):
    node_id: str

class SubgraphRequest(BaseModel):
    center_node: str
    radius: int = 2

class PatternDetectionRequest(BaseModel):
    patterns: Optional[List[str]] = None  # Specific patterns to detect
    min_confidence: float = 0.5

class CommunityDetectionRequest(BaseModel):
    algorithm: str = "louvain"

@router.post("/build-graph")
async def build_network_graph(
    request: BuildGraphRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Build network graph from database data
    """
    try:
        analyzer = get_network_analyzer()
        
        # Build graph in background if it's a large operation
        if request.time_window_days > 365 or request.rebuild:
            def build_graph_background():
                analyzer.build_graph_from_database(
                    db=db,
                    time_window_days=request.time_window_days,
                    min_transaction_amount=request.min_transaction_amount
                )
            
            background_tasks.add_task(build_graph_background)
            
            return {
                "status": "started",
                "message": "Graph building started in background",
                "estimated_completion": "2-5 minutes"
            }
        else:
            # Build immediately for smaller graphs
            analyzer.build_graph_from_database(
                db=db,
                time_window_days=request.time_window_days,
                min_transaction_amount=request.min_transaction_amount
            )
            
            stats = analyzer.get_graph_statistics()
            
            return {
                "status": "completed",
                "message": "Graph built successfully",
                "statistics": stats
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build graph: {str(e)}")

@router.get("/statistics")
async def get_graph_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get network graph statistics
    """
    try:
        analyzer = get_network_analyzer()
        stats = analyzer.get_graph_statistics()
        
        if stats.get("node_count", 0) == 0:
            return {
                "message": "No graph data available. Please build graph first.",
                "statistics": stats
            }
        
        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.post("/centrality")
async def calculate_centrality_measures(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate centrality measures for all nodes
    """
    try:
        analyzer = get_network_analyzer()
        
        if analyzer.graph.number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail="No graph data available. Please build graph first.")
        
        # Calculate centrality in background for large graphs
        if analyzer.graph.number_of_nodes() > 1000:
            def calculate_centrality_background():
                analyzer.calculate_centrality_measures()
            
            background_tasks.add_task(calculate_centrality_background)
            
            return {
                "status": "started",
                "message": "Centrality calculation started in background"
            }
        else:
            centrality_results = analyzer.calculate_centrality_measures()
            
            # Get top nodes by different centrality measures
            top_by_degree = sorted(centrality_results.items(), 
                                 key=lambda x: x[1]["degree_centrality"], reverse=True)[:10]
            top_by_betweenness = sorted(centrality_results.items(), 
                                      key=lambda x: x[1]["betweenness_centrality"], reverse=True)[:10]
            top_by_pagerank = sorted(centrality_results.items(), 
                                   key=lambda x: x[1]["pagerank"], reverse=True)[:10]
            
            return {
                "status": "completed",
                "top_nodes": {
                    "by_degree_centrality": [{"node_id": node, **scores} for node, scores in top_by_degree],
                    "by_betweenness_centrality": [{"node_id": node, **scores} for node, scores in top_by_betweenness],
                    "by_pagerank": [{"node_id": node, **scores} for node, scores in top_by_pagerank]
                },
                "total_nodes_analyzed": len(centrality_results)
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate centrality: {str(e)}")

@router.post("/detect-communities")
async def detect_communities(
    request: CommunityDetectionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Detect communities in the network
    """
    try:
        analyzer = get_network_analyzer()
        
        if analyzer.graph.number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail="No graph data available. Please build graph first.")
        
        result = analyzer.detect_communities(algorithm=request.algorithm)
        
        # Format community information
        community_info = []
        for community_id, members in result.communities.items():
            # Calculate community statistics
            community_risk_scores = []
            total_volume = 0.0
            
            for member in members:
                if member in analyzer.node_cache:
                    node = analyzer.node_cache[member]
                    community_risk_scores.append(node.risk_score)
                    if node.properties:
                        total_volume += node.properties.get("total_transaction_amount", 0)
            
            avg_risk_score = sum(community_risk_scores) / len(community_risk_scores) if community_risk_scores else 0
            
            community_info.append({
                "community_id": community_id,
                "member_count": len(members),
                "members": members[:20],  # Limit for display
                "average_risk_score": round(avg_risk_score, 2),
                "total_transaction_volume": total_volume,
                "risk_level": "HIGH" if avg_risk_score > 70 else "MEDIUM" if avg_risk_score > 40 else "LOW"
            })
        
        # Sort by risk level and size
        community_info.sort(key=lambda x: (x["average_risk_score"], x["member_count"]), reverse=True)
        
        return {
            "algorithm": result.algorithm,
            "modularity": result.modularity,
            "total_communities": result.total_communities,
            "communities": community_info,
            "high_risk_communities": len([c for c in community_info if c["average_risk_score"] > 70])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect communities: {str(e)}")

@router.post("/detect-patterns")
async def detect_suspicious_patterns(
    request: PatternDetectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Detect suspicious patterns in the network
    """
    try:
        analyzer = get_network_analyzer()
        
        if analyzer.graph.number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail="No graph data available. Please build graph first.")
        
        # Detect patterns in background for large graphs
        if analyzer.graph.number_of_nodes() > 500:
            def detect_patterns_background():
                analyzer.detect_suspicious_patterns()
            
            background_tasks.add_task(detect_patterns_background)
            
            return {
                "status": "started",
                "message": "Pattern detection started in background"
            }
        else:
            patterns = analyzer.detect_suspicious_patterns()
            
            # Filter by confidence if specified
            if request.min_confidence:
                patterns = [p for p in patterns if p.confidence >= request.min_confidence]
            
            # Filter by specific pattern types if specified
            if request.patterns:
                patterns = [p for p in patterns if p.pattern_type in request.patterns]
            
            # Format patterns for response
            pattern_data = []
            for pattern in patterns:
                pattern_data.append({
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "confidence": pattern.confidence,
                    "risk_level": pattern.risk_level,
                    "involved_nodes": len(pattern.involved_nodes),
                    "involved_edges": len(pattern.involved_edges),
                    "properties": pattern.properties,
                    "detected_at": pattern.detected_at.isoformat()
                })
            
            # Group by pattern type
            pattern_summary = {}
            for pattern in patterns:
                if pattern.pattern_type not in pattern_summary:
                    pattern_summary[pattern.pattern_type] = {"count": 0, "high_risk": 0}
                pattern_summary[pattern.pattern_type]["count"] += 1
                if pattern.risk_level == "HIGH":
                    pattern_summary[pattern.pattern_type]["high_risk"] += 1
            
            return {
                "status": "completed",
                "patterns": pattern_data,
                "total_patterns": len(patterns),
                "pattern_summary": pattern_summary,
                "high_risk_patterns": len([p for p in patterns if p.risk_level == "HIGH"])
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect patterns: {str(e)}")

@router.post("/node/details")
async def get_node_details(
    request: NodeDetailsRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific node
    """
    try:
        analyzer = get_network_analyzer()
        node_details = analyzer.get_node_details(request.node_id)
        
        if not node_details:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return node_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node details: {str(e)}")

@router.post("/subgraph")
async def get_subgraph(
    request: SubgraphRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get subgraph around a specific node for visualization
    """
    try:
        analyzer = get_network_analyzer()
        subgraph_data = analyzer.get_subgraph(request.center_node, request.radius)
        
        if subgraph_data["node_count"] == 0:
            raise HTTPException(status_code=404, detail="Node not found or no connections")
        
        return subgraph_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subgraph: {str(e)}")

@router.get("/patterns/types")
async def get_pattern_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available pattern types for detection
    """
    pattern_types = [
        {
            "type": "dense_subgraph",
            "name": "Dense Subgraphs",
            "description": "Tightly connected groups that may indicate money laundering rings"
        },
        {
            "type": "star_pattern",
            "name": "Star Patterns",
            "description": "One central node with many connections, potential smurfing operations"
        },
        {
            "type": "chain_pattern",
            "name": "Chain Patterns",
            "description": "Sequential transactions with decreasing amounts, potential layering"
        },
        {
            "type": "circular_pattern",
            "name": "Circular Patterns",
            "description": "Circular transaction flows, potential structuring or wash trading"
        },
        {
            "type": "bridge_pattern",
            "name": "Bridge Patterns",
            "description": "Nodes that connect different network segments, potential intermediaries"
        }
    ]
    
    return {
        "pattern_types": pattern_types,
        "total_types": len(pattern_types)
    }

@router.get("/node-types")
async def get_node_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available node types
    """
    node_types = []
    for node_type in NodeType:
        node_types.append({
            "type": node_type.value,
            "name": node_type.value.replace("_", " ").title(),
            "description": f"{node_type.value.replace('_', ' ').title()} entity in the network"
        })
    
    return {
        "node_types": node_types,
        "total_types": len(node_types)
    }

@router.get("/relationship-types")
async def get_relationship_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available relationship types
    """
    relationship_types = []
    for rel_type in RelationshipType:
        description = {
            RelationshipType.TRANSACTS_WITH: "Financial transactions between entities",
            RelationshipType.OWNS: "Ownership relationship",
            RelationshipType.ASSOCIATES_WITH: "General association or connection",
            RelationshipType.SHARES_ADDRESS: "Entities sharing the same address",
            RelationshipType.SHARES_PHONE: "Entities sharing the same phone number",
            RelationshipType.SHARES_EMAIL: "Entities sharing the same email address",
            RelationshipType.SHARES_DEVICE: "Entities sharing the same device",
            RelationshipType.LOCATED_AT: "Geographic location relationship",
            RelationshipType.CONNECTED_TO: "General connection",
            RelationshipType.SIMILAR_TO: "Similarity relationship",
            RelationshipType.CONTROLS: "Control relationship",
            RelationshipType.BENEFITS_FROM: "Beneficiary relationship"
        }.get(rel_type, "Relationship between entities")
        
        relationship_types.append({
            "type": rel_type.value,
            "name": rel_type.value.replace("_", " ").title(),
            "description": description
        })
    
    return {
        "relationship_types": relationship_types,
        "total_types": len(relationship_types)
    }

@router.get("/high-risk-nodes")
async def get_high_risk_nodes(
    limit: int = 20,
    min_risk_score: float = 70.0,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get nodes with high risk scores
    """
    try:
        analyzer = get_network_analyzer()
        
        if analyzer.graph.number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail="No graph data available. Please build graph first.")
        
        # Find high-risk nodes
        high_risk_nodes = []
        for node_id, node in analyzer.node_cache.items():
            if node.risk_score >= min_risk_score:
                node_info = {
                    "node_id": node_id,
                    "node_type": node.node_type.value,
                    "risk_score": node.risk_score,
                    "name": node.properties.get("name", node_id),
                    "neighbor_count": analyzer.graph.degree(node_id),
                    "centrality_scores": node.centrality_scores or {}
                }
                high_risk_nodes.append(node_info)
        
        # Sort by risk score
        high_risk_nodes.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return {
            "high_risk_nodes": high_risk_nodes[:limit],
            "total_high_risk": len(high_risk_nodes),
            "min_risk_score": min_risk_score,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get high-risk nodes: {str(e)}")

@router.get("/analysis/recommendations")
async def get_analysis_recommendations(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get AI-powered analysis recommendations
    """
    try:
        analyzer = get_network_analyzer()
        stats = analyzer.get_graph_statistics()
        
        recommendations = []
        
        if stats.get("node_count", 0) == 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "Setup",
                "recommendation": "Build network graph from transaction data",
                "description": "Start by building the network graph to enable analysis",
                "action": "POST /api/v1/network/build-graph"
            })
        else:
            # Analyze current state and provide recommendations
            if stats.get("density", 0) < 0.01:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Data Quality",
                    "recommendation": "Increase time window or lower transaction threshold",
                    "description": "Network appears sparse, consider expanding data scope",
                    "action": "Adjust build-graph parameters"
                })
            
            if len(analyzer.patterns_detected) == 0:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "Analysis",
                    "recommendation": "Run suspicious pattern detection",
                    "description": "Detect potential money laundering patterns in the network",
                    "action": "POST /api/v1/network/detect-patterns"
                })
            
            if stats.get("node_count", 0) > 100:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Analysis",
                    "recommendation": "Perform community detection",
                    "description": "Identify customer clusters and community structures",
                    "action": "POST /api/v1/network/detect-communities"
                })
            
            recommendations.append({
                "priority": "LOW",
                "category": "Optimization",
                "recommendation": "Calculate centrality measures",
                "description": "Identify key nodes and influencers in the network",
                "action": "POST /api/v1/network/centrality"
            })
        
        return {
            "recommendations": recommendations,
            "graph_status": "available" if stats.get("node_count", 0) > 0 else "not_built",
            "analysis_completeness": {
                "graph_built": stats.get("node_count", 0) > 0,
                "patterns_detected": len(analyzer.patterns_detected) > 0,
                "centrality_calculated": any(
                    node.centrality_scores for node in analyzer.node_cache.values()
                )
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.get("/health")
async def network_analysis_health_check():
    """
    Health check for network analysis service
    """
    try:
        analyzer = get_network_analyzer()
        stats = analyzer.get_graph_statistics()
        
        return {
            "status": "healthy",
            "graph_available": stats.get("node_count", 0) > 0,
            "node_count": stats.get("node_count", 0),
            "edge_count": stats.get("edge_count", 0),
            "patterns_detected": len(analyzer.patterns_detected),
            "service": "network_analysis",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "network_analysis",
            "timestamp": datetime.now().isoformat()
        }