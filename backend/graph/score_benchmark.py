"""
Code Archaeologist Score Benchmark - Week 4

Computes maintainability metrics in C++ backend:
- Graph density
- Fan-out (coupling)
- Cyclomatic complexity proxy
- Dead code percentage
- Causal complexity

Shows score in UI.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import math

from backend.causal.causal_discovery import CausalGraph


@dataclass
class MaintainabilityScore:
    """Complete maintainability score"""
    overall_score: float  # 0-100
    category: str  # 'excellent', 'good', 'fair', 'poor', 'critical'
    
    # Component scores
    complexity_score: float  # 0-100 (lower complexity = higher score)
    coupling_score: float    # 0-100 (lower coupling = higher score)
    cohesion_score: float    # 0-100 (higher cohesion = higher score)
    documentation_score: float  # 0-100 (AI explanations available)
    
    # Metrics
    graph_density: float
    avg_fan_out: float
    max_fan_out: int
    dead_code_pct: float
    cyclomatic_proxy: int
    causal_complexity: float
    
    # Recommendations
    top_issues: List[Dict]
    strengths: List[str]


class ScoreBenchmark:
    """
    Computes the "Code Archaeologist Score" - a maintainability benchmark.
    
    Score Components:
    1. Complexity (25%): Cyclomatic complexity proxy from graph structure
    2. Coupling (25%): Fan-out analysis
    3. Cohesion (25%): Module independence
    4. Documentation (25%): AI explanations coverage
    
    Total: 0-100 score
    """
    
    def __init__(self):
        self.weights = {
            'complexity': 0.25,
            'coupling': 0.25,
            'cohesion': 0.25,
            'documentation': 0.25
        }
    
    def calculate_score(
        self, 
        causal_graph: CausalGraph,
        functions: List[str],
        explained_functions: Optional[Set[str]] = None
    ) -> MaintainabilityScore:
        """
        Calculate complete maintainability score.
        
        Args:
            causal_graph: Causal graph from analysis
            functions: List of all functions in codebase
            explained_functions: Set of functions with AI explanations
            
        Returns:
            MaintainabilityScore with all metrics
        """
        # Calculate individual metrics
        graph_density = self._calculate_graph_density(causal_graph)
        avg_fan_out, max_fan_out = self._calculate_fan_out(causal_graph)
        dead_code_pct = self._calculate_dead_code_pct(causal_graph, functions)
        cyclomatic_proxy = self._calculate_cyclomatic_proxy(causal_graph)
        causal_complexity = self._calculate_causal_complexity(causal_graph)
        
        # Calculate component scores
        complexity_score = self._score_complexity(cyclomatic_proxy, len(functions))
        coupling_score = self._score_coupling(avg_fan_out, max_fan_out)
        cohesion_score = self._score_cohesion(graph_density)
        documentation_score = self._score_documentation(
            explained_functions, functions
        )
        
        # Overall score
        overall = (
            complexity_score * self.weights['complexity'] +
            coupling_score * self.weights['coupling'] +
            cohesion_score * self.weights['cohesion'] +
            documentation_score * self.weights['documentation']
        )
        
        # Determine category
        category = self._get_category(overall)
        
        # Generate recommendations
        top_issues = self._generate_issues(
            complexity_score, coupling_score, cohesion_score, documentation_score,
            cyclomatic_proxy, avg_fan_out, max_fan_out, dead_code_pct
        )
        
        strengths = self._generate_strengths(
            complexity_score, coupling_score, cohesion_score, documentation_score
        )
        
        return MaintainabilityScore(
            overall_score=round(overall, 1),
            category=category,
            complexity_score=round(complexity_score, 1),
            coupling_score=round(coupling_score, 1),
            cohesion_score=round(cohesion_score, 1),
            documentation_score=round(documentation_score, 1),
            graph_density=round(graph_density, 3),
            avg_fan_out=round(avg_fan_out, 2),
            max_fan_out=max_fan_out,
            dead_code_pct=round(dead_code_pct, 1),
            cyclomatic_proxy=cyclomatic_proxy,
            causal_complexity=round(causal_complexity, 2),
            top_issues=top_issues,
            strengths=strengths
        )
    
    def _calculate_graph_density(self, graph: CausalGraph) -> float:
        """
        Calculate graph density (0-1).
        
        Density = actual edges / possible edges
        Higher density = more tightly coupled
        """
        n = len(graph.nodes)
        if n <= 1:
            return 0.0
        
        possible_edges = n * (n - 1)  # Directed graph
        actual_edges = len(graph.edges)
        
        return actual_edges / possible_edges if possible_edges > 0 else 0.0
    
    def _calculate_fan_out(self, graph: CausalGraph) -> Tuple[float, int]:
        """
        Calculate fan-out metrics.
        
        Returns (average_fan_out, max_fan_out)
        """
        if not graph.nodes:
            return 0.0, 0
        
        # Build adjacency
        fan_outs = defaultdict(int)
        for edge in graph.edges:
            fan_outs[edge.source] += 1
        
        if not fan_outs:
            return 0.0, 0
        
        avg_fan_out = sum(fan_outs.values()) / len(graph.nodes)
        max_fan_out = max(fan_outs.values()) if fan_outs else 0
        
        return avg_fan_out, max_fan_out
    
    def _calculate_dead_code_pct(
        self, 
        graph: CausalGraph, 
        functions: List[str]
    ) -> float:
        """
        Calculate percentage of dead code (functions with no callers).
        """
        if not functions:
            return 0.0
        
        # Find functions with no incoming edges
        called = set()
        for edge in graph.edges:
            called.add(edge.target)
        
        dead = set(functions) - called
        
        return (len(dead) / len(functions)) * 100
    
    def _calculate_cyclomatic_proxy(self, graph: CausalGraph) -> int:
        """
        Calculate proxy for cyclomatic complexity from graph.
        
        Proxy = nodes - edges + 2 * connected_components
        Simplified: just use edges - nodes + 2
        """
        n = len(graph.nodes)
        e = len(graph.edges)
        
        # Simplified cyclomatic complexity proxy
        if n == 0:
            return 0
        
        # Estimate connected components (simplified)
        # In reality, would need to find actual components
        return max(1, e - n + 2)
    
    def _calculate_causal_complexity(self, graph: CausalGraph) -> float:
        """
        Calculate causal complexity score.
        
        Based on:
        1. Number of causal paths
        2. Average path length
        3. Confidence distribution
        """
        if not graph.edges:
            return 0.0
        
        # Average confidence weighted by strength
        total_confidence = sum(
            e.confidence * e.strength for e in graph.edges
        )
        avg_confidence = total_confidence / len(graph.edges)
        
        # Complexity increases with confidence and edge count
        return len(graph.edges) * avg_confidence
    
    def _score_complexity(self, cyclomatic: int, num_functions: int) -> float:
        """Score complexity (0-100, higher is better/lower complexity)"""
        if num_functions == 0:
            return 100.0
        
        # Average complexity per function
        avg_complexity = cyclomatic / num_functions
        
        # Score: 100 at complexity 1, decreasing as complexity increases
        # Using exponential decay
        score = 100 * math.exp(-0.3 * (avg_complexity - 1))
        
        return max(0, min(100, score))
    
    def _score_coupling(self, avg_fan_out: float, max_fan_out: int) -> float:
        """Score coupling (0-100, higher is better/lower coupling)"""
        # Ideal fan-out: 1-3
        # Score decreases as fan-out increases
        
        if avg_fan_out <= 3:
            score = 100 - (avg_fan_out - 1) * 10
        else:
            score = 70 - (avg_fan_out - 3) * 15
        
        # Penalty for extreme max fan-out
        if max_fan_out > 10:
            score -= (max_fan_out - 10) * 2
        
        return max(0, min(100, score))
    
    def _score_cohesion(self, graph_density: float) -> float:
        """Score cohesion (0-100, higher is better)"""
        # Ideal density: 0.1-0.3 (some connections, not too many)
        # Too low = fragmented, too high = tightly coupled
        
        if graph_density < 0.1:
            # Too fragmented
            score = 50 + graph_density * 500
        elif graph_density <= 0.3:
            # Sweet spot
            score = 100 - (graph_density - 0.2) * 100
        else:
            # Too coupled
            score = 80 - (graph_density - 0.3) * 200
        
        return max(0, min(100, score))
    
    def _score_documentation(
        self, 
        explained: Optional[Set[str]], 
        functions: List[str]
    ) -> float:
        """Score documentation coverage (0-100)"""
        if not functions:
            return 100.0
        
        if not explained:
            return 0.0
        
        coverage = len(explained) / len(functions)
        return coverage * 100
    
    def _get_category(self, score: float) -> str:
        """Determine score category"""
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'fair'
        elif score >= 20:
            return 'poor'
        else:
            return 'critical'
    
    def _generate_issues(
        self,
        complexity_score: float,
        coupling_score: float,
        cohesion_score: float,
        documentation_score: float,
        cyclomatic: int,
        avg_fan_out: float,
        max_fan_out: int,
        dead_code_pct: float
    ) -> List[Dict]:
        """Generate list of top issues"""
        issues = []
        
        if complexity_score < 60:
            issues.append({
                'type': 'complexity',
                'severity': 'high' if complexity_score < 40 else 'medium',
                'message': f'High cyclomatic complexity proxy ({cyclomatic})',
                'recommendation': 'Refactor complex functions into smaller ones'
            })
        
        if coupling_score < 60:
            issues.append({
                'type': 'coupling',
                'severity': 'high' if max_fan_out > 15 else 'medium',
                'message': f'High coupling (avg fan-out: {avg_fan_out:.1f}, max: {max_fan_out})',
                'recommendation': 'Reduce dependencies, use dependency injection'
            })
        
        if cohesion_score < 60:
            issues.append({
                'type': 'cohesion',
                'severity': 'medium',
                'message': 'Low cohesion - modules too fragmented or too coupled',
                'recommendation': 'Review module boundaries'
            })
        
        if documentation_score < 50:
            issues.append({
                'type': 'documentation',
                'severity': 'medium',
                'message': f'Low documentation coverage ({documentation_score:.0f}%)',
                'recommendation': 'Generate AI explanations for undocumented functions'
            })
        
        if dead_code_pct > 10:
            issues.append({
                'type': 'dead_code',
                'severity': 'low',
                'message': f'{dead_code_pct:.1f}% dead code detected',
                'recommendation': 'Remove or utilize dead functions'
            })
        
        # Sort by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        issues.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return issues[:5]  # Top 5
    
    def _generate_strengths(
        self,
        complexity_score: float,
        coupling_score: float,
        cohesion_score: float,
        documentation_score: float
    ) -> List[str]:
        """Generate list of strengths"""
        strengths = []
        
        if complexity_score >= 80:
            strengths.append('Low complexity - well-structured code')
        
        if coupling_score >= 80:
            strengths.append('Low coupling - good separation of concerns')
        
        if cohesion_score >= 80:
            strengths.append('High cohesion - well-organized modules')
        
        if documentation_score >= 80:
            strengths.append('Excellent documentation coverage')
        
        return strengths
    
    def export_score(self, score: MaintainabilityScore) -> Dict:
        """Export score to JSON format"""
        return {
            'overall_score': score.overall_score,
            'category': score.category,
            'component_scores': {
                'complexity': score.complexity_score,
                'coupling': score.coupling_score,
                'cohesion': score.cohesion_score,
                'documentation': score.documentation_score
            },
            'metrics': {
                'graph_density': score.graph_density,
                'avg_fan_out': score.avg_fan_out,
                'max_fan_out': score.max_fan_out,
                'dead_code_pct': score.dead_code_pct,
                'cyclomatic_proxy': score.cyclomatic_proxy,
                'causal_complexity': score.causal_complexity
            },
            'top_issues': score.top_issues,
            'strengths': score.strengths
        }


# Convenience function
def calculate_maintainability_score(
    causal_graph: CausalGraph,
    functions: List[str],
    explained_functions: Optional[Set[str]] = None
) -> MaintainabilityScore:
    """
    Quick function to calculate maintainability score.
    
    Usage:
        from backend.graph.score_benchmark import calculate_maintainability_score
        
        score = calculate_maintainability_score(graph, functions)
        print(f"Code Archaeologist Score: {score.overall_score}/100")
        print(f"Category: {score.category}")
    """
    benchmark = ScoreBenchmark()
    return benchmark.calculate_score(causal_graph, functions, explained_functions)
