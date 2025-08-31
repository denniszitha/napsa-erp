"""
Graph Database Network Analysis Service
Provides network analysis capabilities using graph databases for relationship mapping
"""

import networkx as nx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
import community as community_louvain
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class NodeType(Enum):
    """Types of nodes in the graph"""
    CUSTOMER = "customer"
    TRANSACTION = "transaction"
    ACCOUNT = "account"
    ENTITY = "entity"
    ADDRESS = "address"
    PHONE = "phone"
    EMAIL = "email"
    IP_ADDRESS = "ip_address"
    DEVICE = "device"
    LOCATION = "location"

class RelationshipType(Enum):
    """Types of relationships between nodes"""
    TRANSACTS_WITH = "transacts_with"
    OWNS = "owns"
    ASSOCIATES_WITH = "associates_with"
    SHARES_ADDRESS = "shares_address"
    SHARES_PHONE = "shares_phone"
    SHARES_EMAIL = "shares_email"
    SHARES_DEVICE = "shares_device"
    LOCATED_AT = "located_at"
    CONNECTED_TO = "connected_to"
    SIMILAR_TO = "similar_to"
    CONTROLS = "controls"
    BENEFITS_FROM = "benefits_from"

@dataclass
class GraphNode:
    """Graph node representation"""
    node_id: str
    node_type: NodeType
    properties: Dict[str, Any]
    risk_score: float = 0.0
    centrality_scores: Dict[str, float] = None

@dataclass
class GraphEdge:
    """Graph edge representation"""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any]
    weight: float = 1.0
    confidence: float = 1.0

@dataclass
class NetworkPattern:
    """Detected network pattern"""
    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    risk_level: str
    involved_nodes: List[str]
    involved_edges: List[Tuple[str, str]]
    properties: Dict[str, Any]
    detected_at: datetime

@dataclass
class CommunityDetectionResult:
    """Community detection result"""
    communities: Dict[int, List[str]]  # community_id -> list of node_ids
    modularity: float
    total_communities: int
    algorithm: str

class NetworkAnalyzer:
    """Main network analysis engine using NetworkX"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.node_cache: Dict[str, GraphNode] = {}
        self.edge_cache: Dict[Tuple[str, str], List[GraphEdge]] = {}
        self.patterns_detected: List[NetworkPattern] = []
        self.last_analysis: Optional[datetime] = None
    
    def build_graph_from_database(self, db: Session, 
                                 time_window_days: int = 90,
                                 min_transaction_amount: float = 1000.0):
        """Build network graph from database data"""
        try:
            logger.info(f"Building graph from database with {time_window_days}-day window")
            
            # Clear existing graph
            self.graph.clear()
            self.node_cache.clear()
            self.edge_cache.clear()
            
            cutoff_date = datetime.now() - timedelta(days=time_window_days)
            
            # Add customer nodes
            self._add_customer_nodes(db, cutoff_date)
            
            # Add transaction relationships
            self._add_transaction_relationships(db, cutoff_date, min_transaction_amount)
            
            # Add shared attribute relationships
            self._add_shared_attribute_relationships(db)
            
            # Add account relationships
            self._add_account_relationships(db)
            
            logger.info(f"Graph built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
            
        except Exception as e:
            logger.error(f"Error building graph from database: {e}")
            raise
    
    def _add_customer_nodes(self, db: Session, cutoff_date: datetime):
        """Add customer nodes to the graph"""
        query = """
        SELECT 
            c.id,
            c.first_name,
            c.last_name,
            c.date_of_birth,
            c.risk_score,
            c.kyc_status,
            c.address,
            c.phone_number,
            c.email,
            c.created_at,
            COUNT(t.id) as transaction_count,
            SUM(t.amount) as total_transaction_amount,
            MAX(t.transaction_date) as last_transaction_date
        FROM customers c
        LEFT JOIN transactions t ON c.id = t.customer_id AND t.transaction_date >= :cutoff_date
        GROUP BY c.id, c.first_name, c.last_name, c.date_of_birth, c.risk_score, 
                 c.kyc_status, c.address, c.phone_number, c.email, c.created_at
        """
        
        result = db.execute(text(query), {"cutoff_date": cutoff_date})
        customers = result.fetchall()
        
        for customer in customers:
            node_id = f"customer_{customer[0]}"
            
            properties = {
                "customer_id": customer[0],
                "name": f"{customer[1]} {customer[2]}".strip(),
                "first_name": customer[1],
                "last_name": customer[2],
                "date_of_birth": str(customer[3]) if customer[3] else None,
                "kyc_status": customer[5],
                "address": customer[6],
                "phone_number": customer[7],
                "email": customer[8],
                "created_at": customer[9].isoformat() if customer[9] else None,
                "transaction_count": customer[10] or 0,
                "total_transaction_amount": float(customer[11] or 0),
                "last_transaction_date": customer[12].isoformat() if customer[12] else None
            }
            
            node = GraphNode(
                node_id=node_id,
                node_type=NodeType.CUSTOMER,
                properties=properties,
                risk_score=float(customer[4] or 0)
            )
            
            self.node_cache[node_id] = node
            self.graph.add_node(node_id, **asdict(node))
    
    def _add_transaction_relationships(self, db: Session, cutoff_date: datetime, min_amount: float):
        """Add transaction relationships between customers"""
        # For this example, we'll create relationships based on transactions to/from the same accounts
        # In a real system, you'd have more sophisticated relationship detection
        
        query = """
        WITH customer_transactions AS (
            SELECT 
                t1.customer_id as customer1_id,
                t2.customer_id as customer2_id,
                COUNT(*) as transaction_count,
                SUM(t1.amount + t2.amount) as total_amount,
                MAX(GREATEST(t1.transaction_date, t2.transaction_date)) as last_transaction_date,
                STRING_AGG(DISTINCT t1.country, ', ') as countries
            FROM transactions t1
            JOIN transactions t2 ON t1.customer_id != t2.customer_id
                AND ABS(EXTRACT(EPOCH FROM (t1.transaction_date - t2.transaction_date))) < 3600  -- Within 1 hour
                AND t1.amount >= :min_amount
                AND t2.amount >= :min_amount
                AND t1.transaction_date >= :cutoff_date
                AND t2.transaction_date >= :cutoff_date
            GROUP BY t1.customer_id, t2.customer_id
            HAVING COUNT(*) >= 2  -- At least 2 related transactions
        )
        SELECT * FROM customer_transactions
        ORDER BY total_amount DESC
        LIMIT 1000
        """
        
        result = db.execute(text(query), {"cutoff_date": cutoff_date, "min_amount": min_amount})
        relationships = result.fetchall()
        
        for rel in relationships:
            source_id = f"customer_{rel[0]}"
            target_id = f"customer_{rel[1]}"
            
            if source_id in self.node_cache and target_id in self.node_cache:
                edge = GraphEdge(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=RelationshipType.TRANSACTS_WITH,
                    properties={
                        "transaction_count": rel[2],
                        "total_amount": float(rel[3]),
                        "last_transaction_date": rel[4].isoformat() if rel[4] else None,
                        "countries": rel[5]
                    },
                    weight=float(rel[3]) / 10000,  # Normalize weight
                    confidence=min(1.0, rel[2] / 10)  # More transactions = higher confidence
                )
                
                self.graph.add_edge(source_id, target_id, **asdict(edge))
    
    def _add_shared_attribute_relationships(self, db: Session):
        """Add relationships based on shared attributes"""
        # Customers sharing the same address
        query = """
        SELECT c1.id, c2.id, c1.address
        FROM customers c1
        JOIN customers c2 ON c1.address = c2.address AND c1.id < c2.id
        WHERE c1.address IS NOT NULL AND c1.address != ''
        """
        
        result = db.execute(text(query))
        shared_addresses = result.fetchall()
        
        for addr_rel in shared_addresses:
            source_id = f"customer_{addr_rel[0]}"
            target_id = f"customer_{addr_rel[1]}"
            
            if source_id in self.node_cache and target_id in self.node_cache:
                edge = GraphEdge(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=RelationshipType.SHARES_ADDRESS,
                    properties={"shared_address": addr_rel[2]},
                    weight=2.0,  # Shared address is significant
                    confidence=0.9
                )
                
                self.graph.add_edge(source_id, target_id, **asdict(edge))
        
        # Customers sharing the same phone number
        query = """
        SELECT c1.id, c2.id, c1.phone_number
        FROM customers c1
        JOIN customers c2 ON c1.phone_number = c2.phone_number AND c1.id < c2.id
        WHERE c1.phone_number IS NOT NULL AND c1.phone_number != ''
        """
        
        result = db.execute(text(query))
        shared_phones = result.fetchall()
        
        for phone_rel in shared_phones:
            source_id = f"customer_{phone_rel[0]}"
            target_id = f"customer_{phone_rel[1]}"
            
            if source_id in self.node_cache and target_id in self.node_cache:
                edge = GraphEdge(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=RelationshipType.SHARES_PHONE,
                    properties={"shared_phone": phone_rel[2]},
                    weight=2.5,  # Phone sharing is very significant
                    confidence=0.95
                )
                
                self.graph.add_edge(source_id, target_id, **asdict(edge))
    
    def _add_account_relationships(self, db: Session):
        """Add account ownership relationships (if account data available)"""
        # This is a placeholder - in a real system, you'd have account tables
        pass
    
    def calculate_centrality_measures(self) -> Dict[str, Dict[str, float]]:
        """Calculate various centrality measures for all nodes"""
        try:
            logger.info("Calculating centrality measures")
            
            centrality_results = {}
            
            # Convert to undirected for some centrality measures
            undirected_graph = self.graph.to_undirected()
            
            # Degree centrality
            degree_centrality = nx.degree_centrality(self.graph)
            
            # Betweenness centrality
            betweenness_centrality = nx.betweenness_centrality(undirected_graph, k=min(100, len(undirected_graph)))
            
            # Closeness centrality
            closeness_centrality = nx.closeness_centrality(undirected_graph)
            
            # Eigenvector centrality (if graph is connected)
            try:
                eigenvector_centrality = nx.eigenvector_centrality(undirected_graph, max_iter=1000)
            except nx.NetworkXException:
                eigenvector_centrality = {node: 0.0 for node in self.graph.nodes()}
            
            # PageRank
            pagerank = nx.pagerank(self.graph, max_iter=1000)
            
            # Combine all centrality measures
            for node in self.graph.nodes():
                centrality_results[node] = {
                    "degree_centrality": degree_centrality.get(node, 0.0),
                    "betweenness_centrality": betweenness_centrality.get(node, 0.0),
                    "closeness_centrality": closeness_centrality.get(node, 0.0),
                    "eigenvector_centrality": eigenvector_centrality.get(node, 0.0),
                    "pagerank": pagerank.get(node, 0.0)
                }
                
                # Update node cache
                if node in self.node_cache:
                    self.node_cache[node].centrality_scores = centrality_results[node]
            
            logger.info(f"Calculated centrality measures for {len(centrality_results)} nodes")
            return centrality_results
            
        except Exception as e:
            logger.error(f"Error calculating centrality measures: {e}")
            return {}
    
    def detect_communities(self, algorithm: str = "louvain") -> CommunityDetectionResult:
        """Detect communities in the network"""
        try:
            logger.info(f"Detecting communities using {algorithm} algorithm")
            
            if algorithm == "louvain":
                # Convert to undirected for community detection
                undirected_graph = self.graph.to_undirected()
                
                # Apply Louvain community detection
                partition = community_louvain.best_partition(undirected_graph, weight='weight')
                modularity = community_louvain.modularity(partition, undirected_graph, weight='weight')
                
                # Organize communities
                communities = defaultdict(list)
                for node, community_id in partition.items():
                    communities[community_id].append(node)
                
                result = CommunityDetectionResult(
                    communities=dict(communities),
                    modularity=modularity,
                    total_communities=len(communities),
                    algorithm=algorithm
                )
                
                logger.info(f"Detected {result.total_communities} communities with modularity {modularity:.3f}")
                return result
            
            else:
                raise ValueError(f"Unsupported community detection algorithm: {algorithm}")
                
        except Exception as e:
            logger.error(f"Error detecting communities: {e}")
            return CommunityDetectionResult(
                communities={},
                modularity=0.0,
                total_communities=0,
                algorithm=algorithm
            )
    
    def detect_suspicious_patterns(self) -> List[NetworkPattern]:
        """Detect suspicious patterns in the network"""
        try:
            logger.info("Detecting suspicious network patterns")
            
            patterns = []
            
            # Pattern 1: Dense subgraphs (potential money laundering rings)
            patterns.extend(self._detect_dense_subgraphs())
            
            # Pattern 2: Star patterns (potential smurfing operations)
            patterns.extend(self._detect_star_patterns())
            
            # Pattern 3: Chain patterns (potential layering)
            patterns.extend(self._detect_chain_patterns())
            
            # Pattern 4: Circular patterns (potential structuring)
            patterns.extend(self._detect_circular_patterns())
            
            # Pattern 5: Bridge nodes (potential intermediaries)
            patterns.extend(self._detect_bridge_patterns())
            
            self.patterns_detected = patterns
            logger.info(f"Detected {len(patterns)} suspicious patterns")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting suspicious patterns: {e}")
            return []
    
    def _detect_dense_subgraphs(self) -> List[NetworkPattern]:
        """Detect densely connected subgraphs"""
        patterns = []
        
        try:
            # Find cliques of size 4 or larger
            cliques = list(nx.find_cliques(self.graph.to_undirected()))
            large_cliques = [clique for clique in cliques if len(clique) >= 4]
            
            for i, clique in enumerate(large_cliques[:10]):  # Limit to top 10
                # Calculate total transaction volume in clique
                total_volume = 0.0
                edges = []
                
                for node1 in clique:
                    for node2 in clique:
                        if node1 != node2 and self.graph.has_edge(node1, node2):
                            edge_data = self.graph.get_edge_data(node1, node2)
                            if edge_data:
                                for edge in edge_data.values():
                                    if edge.get('relationship_type') == RelationshipType.TRANSACTS_WITH.value:
                                        total_volume += edge.get('properties', {}).get('total_amount', 0)
                                        edges.append((node1, node2))
                
                if total_volume > 100000:  # Significant volume threshold
                    pattern = NetworkPattern(
                        pattern_id=f"dense_subgraph_{i}",
                        pattern_type="dense_subgraph",
                        description=f"Dense subgraph of {len(clique)} customers with high transaction volume",
                        confidence=min(0.9, total_volume / 1000000),
                        risk_level="HIGH" if total_volume > 500000 else "MEDIUM",
                        involved_nodes=list(clique),
                        involved_edges=edges,
                        properties={
                            "clique_size": len(clique),
                            "total_volume": total_volume,
                            "density": len(edges) / (len(clique) * (len(clique) - 1))
                        },
                        detected_at=datetime.now()
                    )
                    patterns.append(pattern)
        
        except Exception as e:
            logger.error(f"Error detecting dense subgraphs: {e}")
        
        return patterns
    
    def _detect_star_patterns(self) -> List[NetworkPattern]:
        """Detect star patterns (one central node with many connections)"""
        patterns = []
        
        try:
            # Find nodes with high degree centrality
            centrality = nx.degree_centrality(self.graph)
            high_degree_nodes = [(node, centrality[node]) for node in centrality 
                               if centrality[node] > 0.1]  # Top 10% by degree
            
            for node, degree_centrality in high_degree_nodes[:5]:  # Top 5 candidates
                neighbors = list(self.graph.neighbors(node))
                
                if len(neighbors) >= 5:  # At least 5 connections
                    # Check if it's actually a star (neighbors not connected to each other)
                    neighbor_edges = 0
                    for n1 in neighbors:
                        for n2 in neighbors:
                            if n1 != n2 and self.graph.has_edge(n1, n2):
                                neighbor_edges += 1
                    
                    neighbor_connectivity = neighbor_edges / (len(neighbors) * (len(neighbors) - 1))
                    
                    if neighbor_connectivity < 0.2:  # Low connectivity among neighbors = star pattern
                        # Calculate total transaction volume
                        total_volume = 0.0
                        edges = []
                        
                        for neighbor in neighbors:
                            if self.graph.has_edge(node, neighbor):
                                edge_data = self.graph.get_edge_data(node, neighbor)
                                if edge_data:
                                    for edge in edge_data.values():
                                        if edge.get('relationship_type') == RelationshipType.TRANSACTS_WITH.value:
                                            total_volume += edge.get('properties', {}).get('total_amount', 0)
                                            edges.append((node, neighbor))
                        
                        pattern = NetworkPattern(
                            pattern_id=f"star_pattern_{node}",
                            pattern_type="star_pattern",
                            description=f"Star pattern with {len(neighbors)} connections (potential smurfing)",
                            confidence=min(0.9, (1 - neighbor_connectivity) * len(neighbors) / 10),
                            risk_level="HIGH" if len(neighbors) > 10 else "MEDIUM",
                            involved_nodes=[node] + neighbors,
                            involved_edges=edges,
                            properties={
                                "center_node": node,
                                "spoke_count": len(neighbors),
                                "neighbor_connectivity": neighbor_connectivity,
                                "total_volume": total_volume
                            },
                            detected_at=datetime.now()
                        )
                        patterns.append(pattern)
        
        except Exception as e:
            logger.error(f"Error detecting star patterns: {e}")
        
        return patterns
    
    def _detect_chain_patterns(self) -> List[NetworkPattern]:
        """Detect chain patterns (potential layering)"""
        patterns = []
        
        try:
            # Look for long paths with decreasing amounts (typical layering pattern)
            for start_node in list(self.graph.nodes())[:50]:  # Sample nodes
                try:
                    # Find paths of length 3-6 from this node
                    for target_node in self.graph.nodes():
                        if start_node != target_node:
                            try:
                                paths = list(nx.all_simple_paths(self.graph, start_node, target_node, cutoff=6))
                                
                                for path in paths:
                                    if len(path) >= 4:  # At least 4 nodes in chain
                                        # Analyze transaction amounts along the path
                                        amounts = []
                                        edges = []
                                        
                                        for i in range(len(path) - 1):
                                            if self.graph.has_edge(path[i], path[i + 1]):
                                                edge_data = self.graph.get_edge_data(path[i], path[i + 1])
                                                if edge_data:
                                                    for edge in edge_data.values():
                                                        if edge.get('relationship_type') == RelationshipType.TRANSACTS_WITH.value:
                                                            amount = edge.get('properties', {}).get('total_amount', 0)
                                                            amounts.append(amount)
                                                            edges.append((path[i], path[i + 1]))
                                                            break
                                        
                                        # Check for decreasing pattern (layering indicator)
                                        if len(amounts) >= 3 and amounts[0] > 50000:
                                            decreasing = sum(1 for i in range(len(amounts) - 1) 
                                                           if amounts[i] > amounts[i + 1])
                                            decreasing_ratio = decreasing / (len(amounts) - 1)
                                            
                                            if decreasing_ratio > 0.6:  # Mostly decreasing
                                                pattern = NetworkPattern(
                                                    pattern_id=f"chain_pattern_{start_node}_{target_node}",
                                                    pattern_type="chain_pattern",
                                                    description=f"Chain of {len(path)} nodes with decreasing amounts (potential layering)",
                                                    confidence=decreasing_ratio,
                                                    risk_level="HIGH" if decreasing_ratio > 0.8 else "MEDIUM",
                                                    involved_nodes=path,
                                                    involved_edges=edges,
                                                    properties={
                                                        "chain_length": len(path),
                                                        "decreasing_ratio": decreasing_ratio,
                                                        "start_amount": amounts[0] if amounts else 0,
                                                        "end_amount": amounts[-1] if amounts else 0
                                                    },
                                                    detected_at=datetime.now()
                                                )
                                                patterns.append(pattern)
                                                
                                                if len(patterns) >= 10:  # Limit results
                                                    break
                                
                                if len(patterns) >= 10:
                                    break
                            except nx.NetworkXNoPath:
                                continue
                        
                        if len(patterns) >= 10:
                            break
                    
                    if len(patterns) >= 10:
                        break
                        
                except Exception:
                    continue
        
        except Exception as e:
            logger.error(f"Error detecting chain patterns: {e}")
        
        return patterns[:5]  # Return top 5
    
    def _detect_circular_patterns(self) -> List[NetworkPattern]:
        """Detect circular transaction patterns"""
        patterns = []
        
        try:
            # Find simple cycles in the graph
            try:
                cycles = list(nx.simple_cycles(self.graph))
                cycles = [cycle for cycle in cycles if len(cycle) >= 3 and len(cycle) <= 8]  # Reasonable cycle sizes
                
                for i, cycle in enumerate(cycles[:10]):  # Limit to 10 cycles
                    # Calculate total volume in cycle
                    total_volume = 0.0
                    edges = []
                    
                    for j in range(len(cycle)):
                        current = cycle[j]
                        next_node = cycle[(j + 1) % len(cycle)]
                        
                        if self.graph.has_edge(current, next_node):
                            edge_data = self.graph.get_edge_data(current, next_node)
                            if edge_data:
                                for edge in edge_data.values():
                                    if edge.get('relationship_type') == RelationshipType.TRANSACTS_WITH.value:
                                        total_volume += edge.get('properties', {}).get('total_amount', 0)
                                        edges.append((current, next_node))
                                        break
                    
                    if total_volume > 25000:  # Significant circular flow
                        pattern = NetworkPattern(
                            pattern_id=f"circular_pattern_{i}",
                            pattern_type="circular_pattern",
                            description=f"Circular transaction pattern of {len(cycle)} customers",
                            confidence=min(0.9, total_volume / 100000),
                            risk_level="HIGH" if total_volume > 100000 else "MEDIUM",
                            involved_nodes=cycle,
                            involved_edges=edges,
                            properties={
                                "cycle_length": len(cycle),
                                "total_volume": total_volume,
                                "average_amount": total_volume / len(edges) if edges else 0
                            },
                            detected_at=datetime.now()
                        )
                        patterns.append(pattern)
                        
            except nx.NetworkXError:
                # Graph might be too large for cycle detection
                pass
        
        except Exception as e:
            logger.error(f"Error detecting circular patterns: {e}")
        
        return patterns
    
    def _detect_bridge_patterns(self) -> List[NetworkPattern]:
        """Detect bridge nodes that connect different communities"""
        patterns = []
        
        try:
            # Calculate betweenness centrality to find bridge nodes
            betweenness = nx.betweenness_centrality(self.graph.to_undirected(), k=100)
            high_betweenness = [(node, score) for node, score in betweenness.items() 
                              if score > 0.1]  # High betweenness centrality
            
            for node, betweenness_score in high_betweenness[:5]:  # Top 5 bridge candidates
                neighbors = list(self.graph.neighbors(node))
                
                if len(neighbors) >= 3:  # Must connect multiple nodes
                    # Calculate transaction volume through this bridge
                    total_volume = 0.0
                    edges = []
                    
                    for neighbor in neighbors:
                        if self.graph.has_edge(node, neighbor):
                            edge_data = self.graph.get_edge_data(node, neighbor)
                            if edge_data:
                                for edge in edge_data.values():
                                    if edge.get('relationship_type') == RelationshipType.TRANSACTS_WITH.value:
                                        total_volume += edge.get('properties', {}).get('total_amount', 0)
                                        edges.append((node, neighbor))
                    
                    pattern = NetworkPattern(
                        pattern_id=f"bridge_pattern_{node}",
                        pattern_type="bridge_pattern",
                        description=f"Bridge node connecting {len(neighbors)} different network segments",
                        confidence=min(0.9, betweenness_score * 2),
                        risk_level="MEDIUM",
                        involved_nodes=[node] + neighbors,
                        involved_edges=edges,
                        properties={
                            "bridge_node": node,
                            "betweenness_centrality": betweenness_score,
                            "connected_nodes": len(neighbors),
                            "flow_volume": total_volume
                        },
                        detected_at=datetime.now()
                    )
                    patterns.append(pattern)
        
        except Exception as e:
            logger.error(f"Error detecting bridge patterns: {e}")
        
        return patterns
    
    def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific node"""
        if node_id not in self.node_cache:
            return None
        
        node = self.node_cache[node_id]
        
        # Get neighbors
        neighbors = list(self.graph.neighbors(node_id))
        
        # Get edge details
        edges = []
        for neighbor in neighbors:
            edge_data = self.graph.get_edge_data(node_id, neighbor)
            if edge_data:
                for edge in edge_data.values():
                    edges.append({
                        "target": neighbor,
                        "relationship_type": edge.get('relationship_type'),
                        "weight": edge.get('weight'),
                        "properties": edge.get('properties', {})
                    })
        
        return {
            "node_id": node_id,
            "node_type": node.node_type.value,
            "properties": node.properties,
            "risk_score": node.risk_score,
            "centrality_scores": node.centrality_scores or {},
            "neighbor_count": len(neighbors),
            "neighbors": neighbors,
            "edges": edges
        }
    
    def get_subgraph(self, center_node: str, radius: int = 2) -> Dict[str, Any]:
        """Get subgraph around a specific node"""
        if center_node not in self.graph.nodes():
            return {"nodes": [], "edges": []}
        
        # Get nodes within radius
        subgraph_nodes = set([center_node])
        current_layer = {center_node}
        
        for _ in range(radius):
            next_layer = set()
            for node in current_layer:
                neighbors = set(self.graph.neighbors(node))
                next_layer.update(neighbors)
            current_layer = next_layer - subgraph_nodes
            subgraph_nodes.update(current_layer)
        
        # Extract subgraph
        subgraph = self.graph.subgraph(subgraph_nodes)
        
        # Format for visualization
        nodes = []
        for node in subgraph.nodes():
            node_data = self.node_cache.get(node, None)
            if node_data:
                nodes.append({
                    "id": node,
                    "type": node_data.node_type.value,
                    "label": node_data.properties.get("name", node),
                    "risk_score": node_data.risk_score,
                    "properties": node_data.properties
                })
        
        edges = []
        for source, target in subgraph.edges():
            edge_data = self.graph.get_edge_data(source, target)
            if edge_data:
                for edge in edge_data.values():
                    edges.append({
                        "source": source,
                        "target": target,
                        "relationship_type": edge.get('relationship_type'),
                        "weight": edge.get('weight', 1.0),
                        "properties": edge.get('properties', {})
                    })
        
        return {
            "center_node": center_node,
            "radius": radius,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get overall graph statistics"""
        try:
            stats = {
                "node_count": self.graph.number_of_nodes(),
                "edge_count": self.graph.number_of_edges(),
                "density": nx.density(self.graph),
                "is_connected": nx.is_weakly_connected(self.graph),
                "patterns_detected": len(self.patterns_detected),
                "last_analysis": self.last_analysis.isoformat() if self.last_analysis else None
            }
            
            # Node type distribution
            node_type_dist = {}
            for node_id, node in self.node_cache.items():
                node_type = node.node_type.value
                node_type_dist[node_type] = node_type_dist.get(node_type, 0) + 1
            
            stats["node_type_distribution"] = node_type_dist
            
            # Relationship type distribution
            relationship_type_dist = {}
            for _, _, edge_data in self.graph.edges(data=True):
                rel_type = edge_data.get('relationship_type', 'unknown')
                relationship_type_dist[rel_type] = relationship_type_dist.get(rel_type, 0) + 1
            
            stats["relationship_type_distribution"] = relationship_type_dist
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting graph statistics: {e}")
            return {}

# Global network analyzer instance
network_analyzer = None

def get_network_analyzer() -> NetworkAnalyzer:
    """Get the global network analyzer instance"""
    global network_analyzer
    if network_analyzer is None:
        network_analyzer = NetworkAnalyzer()
    return network_analyzer