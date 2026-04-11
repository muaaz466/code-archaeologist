"""
Causal Discovery Module - Week 4

Converts traces to tabular form and builds causal graphs with confidence scores.
Uses causal-learn style logic (Python bridge for prototyping).
Can be ported to C++ later for speed.
"""

import json
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import numpy as np


@dataclass
class CausalEdge:
    """Represents a causal relationship between functions"""
    source: str
    target: str
    confidence: float  # 0.0 to 1.0
    strength: float    # Call frequency / dependency strength
    evidence: List[str]  # Supporting evidence (trace events)


@dataclass
class CausalGraph:
    """Causal graph with confidence scores"""
    nodes: Set[str]
    edges: List[CausalEdge]
    
    def get_confidence(self, source: str, target: str) -> float:
        """Get confidence score for a causal edge"""
        for edge in self.edges:
            if edge.source == source and edge.target == target:
                return edge.confidence
        return 0.0
    
    def get_affected_by(self, node: str) -> List[Tuple[str, float]]:
        """Get nodes affected by this node with confidence scores"""
        affected = []
        for edge in self.edges:
            if edge.source == node:
                affected.append((edge.target, edge.confidence))
        return sorted(affected, key=lambda x: x[1], reverse=True)
    
    def get_causes_of(self, node: str) -> List[Tuple[str, float]]:
        """Get causes of this node with confidence scores"""
        causes = []
        for edge in self.edges:
            if edge.target == node:
                causes.append((edge.source, edge.confidence))
        return sorted(causes, key=lambda x: x[1], reverse=True)


class CausalDiscovery:
    """
    Discovers causal relationships from code traces.
    
    Uses temporal ordering and statistical patterns to infer causality:
    1. Temporal precedence: if A calls B, A may cause B
    2. Statistical dependency: frequent co-occurrence suggests causation
    3. Intervention testing: what happens when A is removed
    """
    
    def __init__(self):
        self.call_counts = defaultdict(int)
        self.temporal_pairs = defaultdict(int)
        self.total_calls = 0
    
    def add_trace(self, events: List[Dict]):
        """
        Add trace events to build causal model.
        
        Args:
            events: List of trace events with function, timestamp, etc.
        """
        # Convert TraceEvent objects to dicts if needed
        def _to_dict(e):
            if hasattr(e, 'function'):
                return {
                    'function': e.function,
                    'parent': getattr(e, 'parent', None),
                    'timestamp': getattr(e, 'timestamp', None),
                    'filename': getattr(e, 'filename', None),
                }
            return e
        
        events = [_to_dict(e) for e in events]
        
        # Sort by timestamp if available
        events = sorted(events, key=lambda e: e.get('timestamp') or 0)
        
        # Track call sequences
        for i, event in enumerate(events):
            func = event.get('function', '')
            if not func:
                continue
                
            self.call_counts[func] += 1
            self.total_calls += 1
            
            # Look at next events for temporal causality
            for j in range(i + 1, min(i + 5, len(events))):
                next_func = events[j].get('function', '')
                if next_func and next_func != func:
                    pair = (func, next_func)
                    self.temporal_pairs[pair] += 1
    
    def discover_causal_graph(self, min_confidence: float = 0.3) -> CausalGraph:
        """
        Build causal graph from collected traces.
        
        Args:
            min_confidence: Minimum confidence threshold (0.0-1.0)
            
        Returns:
            CausalGraph with edges and confidence scores
        """
        nodes = set(self.call_counts.keys())
        edges = []
        
        # Calculate causal edges from temporal patterns
        for (source, target), count in self.temporal_pairs.items():
            # Confidence based on:
            # 1. Frequency of temporal ordering
            # 2. Statistical significance
            source_calls = self.call_counts[source]
            target_calls = self.call_counts[target]
            
            if source_calls == 0 or target_calls == 0:
                continue
            
            # Confidence = P(target | source) adjusted for base rate
            temporal_strength = count / source_calls
            base_rate = target_calls / self.total_calls if self.total_calls > 0 else 0
            
            # Lift score: how much more likely is target after source
            if base_rate > 0:
                lift = temporal_strength / base_rate
                confidence = min(1.0, max(0.0, 
                    (lift - 1) / (lift + 1)  # Normalize to 0-1
                ))
            else:
                confidence = temporal_strength
            
            # Evidence
            evidence = [f"Temporal ordering: {count} occurrences"]
            
            if confidence >= min_confidence:
                edges.append(CausalEdge(
                    source=source,
                    target=target,
                    confidence=round(confidence, 3),
                    strength=round(temporal_strength, 3),
                    evidence=evidence
                ))
        
        return CausalGraph(nodes=nodes, edges=edges)
    
    def analyze_intervention(
        self, 
        graph: CausalGraph, 
        remove_node: str
    ) -> Dict:
        """
        Analyze what happens if a node is removed (intervention analysis).
        
        Args:
            graph: Causal graph
            remove_node: Node to remove
            
        Returns:
            Analysis of affected nodes and break probabilities
        """
        # Find all nodes downstream of removed node
        affected = graph.get_affected_by(remove_node)
        
        # Calculate break probability for each affected node
        breaks = []
        for target, confidence in affected:
            # Higher confidence = more likely to break
            # Also consider if target has other causes
            other_causes = graph.get_causes_of(target)
            other_causes = [c for c in other_causes if c[0] != remove_node]
            
            # If no other causes, very likely to break
            # If many other causes, less likely to break
            if len(other_causes) == 0:
                break_prob = min(0.95, confidence * 1.5)  # Cap at 95%
            else:
                # Reduce probability based on alternative causes
                alt_strength = sum(c[1] for c in other_causes)
                break_prob = confidence / (confidence + alt_strength + 0.1)
            
            breaks.append({
                'function': target,
                'break_probability': round(break_prob, 3),
                'confidence': confidence,
                'alternative_causes': len(other_causes)
            })
        
        # Sort by break probability
        breaks.sort(key=lambda x: x['break_probability'], reverse=True)
        
        return {
            'removed_node': remove_node,
            'affected_count': len(breaks),
            'high_risk_breaks': [b for b in breaks if b['break_probability'] > 0.7],
            'all_affected': breaks
        }
    
    def to_tabular(self) -> Tuple[List[str], np.ndarray]:
        """
        Convert to tabular format for causal-learn library.
        
        Returns:
            (column_names, data_matrix)
        """
        nodes = sorted(self.call_counts.keys())
        n = len(nodes)
        
        # Create adjacency matrix from temporal pairs
        matrix = np.zeros((n, n))
        
        for i, source in enumerate(nodes):
            for j, target in enumerate(nodes):
                pair = (source, target)
                if pair in self.temporal_pairs:
                    # Normalize by source frequency
                    count = self.temporal_pairs[pair]
                    source_calls = self.call_counts[source]
                    matrix[i, j] = count / source_calls if source_calls > 0 else 0
        
        return nodes, matrix
    
    def export_graph_json(self, graph: CausalGraph) -> Dict:
        """Export causal graph to JSON format"""
        return {
            'nodes': list(graph.nodes),
            'edges': [
                {
                    'source': e.source,
                    'target': e.target,
                    'confidence': e.confidence,
                    'strength': e.strength,
                    'evidence': e.evidence
                }
                for e in graph.edges
            ]
        }


# Convenience function
def discover_from_traces(events: List[Dict], min_confidence: float = 0.3) -> CausalGraph:
    """
    Discover causal graph from trace events.
    
    Usage:
        events = load_traces('trace.json')
        graph = discover_from_traces(events)
        
        # Check what breaks if function X is removed
        analysis = analyzer.analyze_intervention(graph, 'function_X')
        print(f"{analysis['affected_count']} functions affected")
    """
    discovery = CausalDiscovery()
    discovery.add_trace(events)
    return discovery.discover_causal_graph(min_confidence)
