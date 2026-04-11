"""
Causal Discovery Module - Week 4

Provides causal graph discovery and what-if simulation capabilities.
"""

from backend.causal.causal_discovery import (
    CausalDiscovery,
    CausalGraph,
    CausalEdge,
    discover_from_traces
)

from backend.causal.what_if_simulator import (
    WhatIfSimulator,
    SimulationResult,
    simulate_removal,
    predict_refactor_impact
)

__all__ = [
    'CausalDiscovery',
    'CausalGraph',
    'CausalEdge',
    'WhatIfSimulator',
    'SimulationResult',
    'discover_from_traces',
    'simulate_removal',
    'predict_refactor_impact'
]
