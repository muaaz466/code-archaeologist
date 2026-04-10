from __future__ import annotations

import networkx as nx
from typing import Iterable, Union, List, Dict, Any

from backend.core.models import TraceEvent

# Try to import fast C++ implementation
try:
    from backend.graph.fast_graph_wrapper import build_fast_graph, FastGraphHandle
    HAS_FAST_GRAPH = True
except ImportError:
    HAS_FAST_GRAPH = False
    
    # Define placeholder for type hints when C++ extension unavailable
    class FastGraphHandle:
        """Placeholder when C++ extension not compiled"""
        def list_functions(self) -> List[str]:
            return []
        
        def get_stats(self) -> tuple[int, int]:
            return (0, 0)

# Define return type alias - works for both cases
GraphType = Union[nx.DiGraph, FastGraphHandle]


def _variable_node_id(variable_name: str) -> str:
    return f"var:{variable_name}"


def build_graph(events: Iterable[TraceEvent]) -> GraphType:
    """
    Build a graph from trace events.
    Uses fast C++ implementation if available, otherwise falls back to NetworkX.
    """
    events_list = list(events)

    # Try fast C++ implementation first
    if HAS_FAST_GRAPH:
        try:
            fast_graph = build_fast_graph(events_list)
            if fast_graph:
                return fast_graph
        except Exception as e:
            print(f"Warning: Fast C++ graph failed ({e}), falling back to NetworkX")

    # Fallback to NetworkX implementation
    return _build_networkx_graph(events_list)


def _build_networkx_graph(events: List[TraceEvent]) -> nx.DiGraph:
    """Build a directed graph from trace events and data flow events."""
    graph = nx.DiGraph()

    for event in events:
        node_id = event.id
        graph.add_node(
            node_id,
            type="event",
            function=event.function,
            filename=event.filename,
            lineno=event.lineno,
            event=event.event,
            code=event.code,
            language=event.language,
        )

        parent = event.parent
        if parent:
            graph.add_edge(parent, node_id, type="call")

        for variable in event.writes:
            var_id = _variable_node_id(variable)
            graph.add_node(var_id, type="variable", name=variable)
            graph.add_edge(node_id, var_id, type="writes")

        for variable in event.reads:
            var_id = _variable_node_id(variable)
            graph.add_node(var_id, type="variable", name=variable)
            graph.add_edge(var_id, node_id, type="reads")

    return graph


def is_fast_graph(graph: GraphType) -> bool:
    """Check if graph is the C++ fast implementation"""
    return HAS_FAST_GRAPH and isinstance(graph, FastGraphHandle)


def get_graph_stats(graph: GraphType) -> Dict[str, Any]:
    """Get statistics from either graph type"""
    if is_fast_graph(graph):
        nodes, edges = graph.get_stats()
        return {"nodes": nodes, "edges": edges, "type": "fast_cpp"}
    else:
        return {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "type": "networkx"
        }