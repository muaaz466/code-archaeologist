"""
What-If Simulator - Week 4

Simulates interventions on the causal graph:
- Remove a node
- Propagate effects
- Calculate break probabilities

Can be ported to C++ later for performance.
"""

from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json

from backend.causal.causal_discovery import CausalGraph, CausalEdge


@dataclass
class SimulationResult:
    """Result of a what-if simulation"""
    intervention_node: str
    affected_functions: List[Dict]
    cascade_depth: int
    total_break_probability: float
    critical_path: List[str]  # Most likely break chain
    alternative_paths: List[List[str]]  # Other possible chains


class WhatIfSimulator:
    """
    Simulates "what if we remove function X?" scenarios.
    
    Uses the causal graph to propagate effects and predict breaks.
    """
    
    def __init__(self, graph: CausalGraph):
        self.graph = graph
        self._build_adjacency()
    
    def _build_adjacency(self):
        """Build adjacency list for fast traversal"""
        self.adjacency = defaultdict(list)
        self.edge_confidence = {}
        
        for edge in self.graph.edges:
            self.adjacency[edge.source].append(edge.target)
            key = (edge.source, edge.target)
            self.edge_confidence[key] = edge.confidence
    
    def simulate_removal(
        self, 
        node: str, 
        propagation_depth: int = 10
    ) -> SimulationResult:
        """
        Simulate removing a node and propagate effects.
        
        Args:
            node: Function to remove
            propagation_depth: How far to propagate effects
            
        Returns:
            SimulationResult with break predictions
        """
        if node not in self.graph.nodes:
            return SimulationResult(
                intervention_node=node,
                affected_functions=[],
                cascade_depth=0,
                total_break_probability=0.0,
                critical_path=[],
                alternative_paths=[]
            )
        
        # BFS to find all affected nodes
        affected = self._propagate_effects(node, propagation_depth)
        
        # Calculate break probabilities for each affected node
        affected_with_probs = []
        for target, path_confidence in affected.items():
            # Combined confidence along the path
            break_prob = self._calculate_break_probability(node, target, path_confidence)
            
            # Find alternative causes
            alt_causes = self.graph.get_causes_of(target)
            alt_causes = [c for c in alt_causes if c[0] != node]
            
            affected_with_probs.append({
                'function': target,
                'break_probability': round(break_prob, 3),
                'path_confidence': round(path_confidence, 3),
                'alternative_causes': len(alt_causes),
                'alt_cause_strength': round(sum(c[1] for c in alt_causes), 3),
                'severity': 'high' if break_prob > 0.7 else 'medium' if break_prob > 0.4 else 'low'
            })
        
        # Sort by break probability
        affected_with_probs.sort(
            key=lambda x: x['break_probability'], 
            reverse=True
        )
        
        # Find critical path (highest probability chain)
        critical_path = self._find_critical_path(node, affected)
        
        # Find alternative paths
        alternative_paths = self._find_alternative_paths(node, affected)
        
        # Calculate total system break probability
        # (probability that at least one function breaks)
        if affected_with_probs:
            # P(at least one breaks) = 1 - P(none break)
            prob_none_break = 1.0
            for af in affected_with_probs:
                prob_none_break *= (1 - af['break_probability'])
            total_break_prob = 1 - prob_none_break
        else:
            total_break_prob = 0.0
        
        return SimulationResult(
            intervention_node=node,
            affected_functions=affected_with_probs,
            cascade_depth=self._get_max_depth(affected),
            total_break_probability=round(total_break_prob, 3),
            critical_path=critical_path,
            alternative_paths=alternative_paths
        )
    
    def _propagate_effects(
        self, 
        start_node: str, 
        max_depth: int
    ) -> Dict[str, float]:
        """
        Propagate effects through the graph.
        
        Returns:
            Dict mapping affected node to path confidence
        """
        affected = {}  # node -> accumulated confidence
        visited = {start_node}
        queue = [(start_node, 1.0, 0)]  # (node, confidence, depth)
        
        while queue:
            current, confidence, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            # Get outgoing edges
            neighbors = self.adjacency.get(current, [])
            
            for neighbor in neighbors:
                # Edge confidence
                edge_key = (current, neighbor)
                edge_conf = self.edge_confidence.get(edge_key, 0.5)
                
                # Combined confidence along path
                new_confidence = confidence * edge_conf
                
                # Update if this path has higher confidence
                if neighbor not in affected or affected[neighbor] < new_confidence:
                    affected[neighbor] = new_confidence
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, new_confidence, depth + 1))
        
        return affected
    
    def _calculate_break_probability(
        self, 
        source: str, 
        target: str,
        path_confidence: float
    ) -> float:
        """
        Calculate probability that target breaks if source is removed.
        
        Formula considers:
        1. Path confidence (how strongly connected)
        2. Alternative causes (redundancy reduces break probability)
        """
        # Get alternative causes
        alt_causes = self.graph.get_causes_of(target)
        alt_causes = [c for c in alt_causes if c[0] != source]
        
        if not alt_causes:
            # No alternative causes - likely to break
            return min(0.95, path_confidence * 1.2)
        
        # Calculate alternative support
        alt_strength = sum(c[1] for c in alt_causes)
        
        # Break probability decreases with alternative support
        # Using a logistic-like curve
        if path_confidence + alt_strength > 0:
            break_prob = path_confidence / (path_confidence + alt_strength + 0.1)
        else:
            break_prob = 0.0
        
        return min(0.95, break_prob)
    
    def _find_critical_path(
        self, 
        start: str, 
        affected: Dict[str, float]
    ) -> List[str]:
        """Find the highest confidence path from start to a sink"""
        if not affected:
            return [start]
        
        # Start with highest confidence affected node
        target = max(affected.items(), key=lambda x: x[1])[0]
        
        # Trace back to find path
        path = [start]
        current = start
        
        while current != target:
            # Find best next step
            neighbors = self.adjacency.get(current, [])
            best_next = None
            best_conf = 0
            
            for neighbor in neighbors:
                if neighbor in affected:
                    conf = affected[neighbor]
                    if conf > best_conf:
                        best_conf = conf
                        best_next = neighbor
            
            if best_next is None:
                break
            
            path.append(best_next)
            current = best_next
        
        return path
    
    def _find_alternative_paths(
        self, 
        start: str, 
        affected: Dict[str, float],
        max_paths: int = 3
    ) -> List[List[str]]:
        """Find alternative high-confidence paths"""
        paths = []
        
        for target, conf in sorted(affected.items(), key=lambda x: x[1], reverse=True):
            if len(paths) >= max_paths:
                break
            
            # Try to find a path to this target
            path = self._trace_path(start, target)
            if path and path not in paths:
                paths.append(path)
        
        return paths
    
    def _trace_path(self, start: str, target: str) -> List[str]:
        """Trace a path from start to target using BFS"""
        if start == target:
            return [start]
        
        queue = [(start, [start])]
        visited = {start}
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in self.adjacency.get(current, []):
                if neighbor == target:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def _get_max_depth(self, affected: Dict[str, float]) -> int:
        """Estimate cascade depth from affected nodes"""
        if not affected:
            return 0
        # Rough estimate based on number of affected nodes
        return min(10, len(affected))
    
    def batch_simulate(
        self, 
        nodes: List[str]
    ) -> List[SimulationResult]:
        """Run simulations for multiple nodes"""
        return [self.simulate_removal(node) for node in nodes]
    
    def find_safe_removals(self, max_break_prob: float = 0.3) -> List[str]:
        """
        Find functions that can be safely removed.
        
        Args:
            max_break_prob: Maximum acceptable break probability
            
        Returns:
            List of safe-to-remove function names
        """
        safe = []
        
        for node in self.graph.nodes:
            result = self.simulate_removal(node)
            
            # Safe if no high-risk breaks
            high_risk = [f for f in result.affected_functions 
                        if f['break_probability'] > max_break_prob]
            
            if not high_risk:
                safe.append({
                    'function': node,
                    'affected_count': len(result.affected_functions),
                    'max_break_prob': max(
                        (f['break_probability'] for f in result.affected_functions),
                        default=0
                    )
                })
        
        # Sort by affected count (fewer is better)
        safe.sort(key=lambda x: x['affected_count'])
        return [s['function'] for s in safe]
    
    def export_simulation(self, result: SimulationResult) -> Dict:
        """Export simulation result to JSON"""
        return {
            'intervention': result.intervention_node,
            'summary': {
                'affected_functions': len(result.affected_functions),
                'cascade_depth': result.cascade_depth,
                'total_break_probability': result.total_break_probability
            },
            'critical_path': result.critical_path,
            'affected': result.affected_functions
        }


# Convenience functions
def simulate_removal(graph: CausalGraph, node: str) -> SimulationResult:
    """Quick simulation of removing a function"""
    simulator = WhatIfSimulator(graph)
    return simulator.simulate_removal(node)


def predict_refactor_impact(
    graph: CausalGraph, 
    functions_to_remove: List[str]
) -> Dict:
    """
    Predict impact of refactoring by removing multiple functions.
    
    Returns aggregated impact analysis.
    """
    simulator = WhatIfSimulator(graph)
    results = simulator.batch_simulate(functions_to_remove)
    
    # Aggregate results
    all_affected = set()
    total_break_prob = 0.0
    
    for result in results:
        for af in result.affected_functions:
            if af['break_probability'] > 0.5:
                all_affected.add(af['function'])
        total_break_prob += result.total_break_probability
    
    return {
        'functions_removed': functions_to_remove,
        'high_risk_affected': list(all_affected),
        'estimated_break_probability': min(1.0, total_break_prob),
        'recommendation': 'proceed' if len(all_affected) < 3 else 'review'
    }
