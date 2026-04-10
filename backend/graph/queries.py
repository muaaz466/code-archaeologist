from __future__ import annotations

import networkx as nx
from typing import Any, List, Set, Dict

# Import from builder module
from backend.graph.builder import GraphType, is_fast_graph, FastGraphHandle


def list_functions(graph: GraphType) -> List[str]:
    """List all functions in the graph"""
    if is_fast_graph(graph):
        return graph.list_functions()
    
    # NetworkX implementation
    functions: Set[str] = set()
    for node, attrs in graph.nodes(data=True):
        if attrs.get("type") == "event" and attrs.get("function"):
            functions.add(attrs["function"])
    return sorted(list(functions))


def get_callers(graph: GraphType, function_name: str) -> List[str]:
    """Find functions that call the given function"""
    if is_fast_graph(graph):
        return graph.get_callers(function_name)
    
    # NetworkX implementation
    callers: Set[str] = set()
    target_nodes = [
        n for n, attr in graph.nodes(data=True)
        if attr.get("function") == function_name
    ]
    
    for target in target_nodes:
        for predecessor in graph.predecessors(target):
            pred_attrs = graph.nodes[predecessor]
            if pred_attrs.get("function"):
                callers.add(pred_attrs["function"])
    
    return sorted(list(callers))


def get_callees(graph: GraphType, function_name: str) -> List[str]:
    """Find functions called by the given function"""
    if is_fast_graph(graph):
        return graph.get_callees(function_name)
    
    callees: Set[str] = set()
    source_nodes = [
        n for n, attr in graph.nodes(data=True)
        if attr.get("function") == function_name
    ]
    
    for source in source_nodes:
        for successor in graph.successors(source):
            succ_attrs = graph.nodes[successor]
            if succ_attrs.get("function") and succ_attrs.get("type") == "event":
                callees.add(succ_attrs["function"])
    
    return sorted(list(callees))


def find_paths(
    graph: GraphType, 
    source: str, 
    target: str, 
    max_depth: int = 10
) -> List[List[str]]:
    """Find execution paths between two functions"""
    if is_fast_graph(graph):
        return []
    
    try:
        # Find all node IDs for source and target functions
        source_nodes = [
            n for n, attr in graph.nodes(data=True)
            if attr.get("function") == source
        ]
        target_nodes = [
            n for n, attr in graph.nodes(data=True)
            if attr.get("function") == target
        ]
        
        all_paths: List[List[str]] = []
        for s in source_nodes:
            for t in target_nodes:
                try:
                    path = nx.shortest_path(graph, s, t)
                    # Convert node IDs to function names
                    path_names: List[str] = []
                    for node in path:
                        attrs = graph.nodes[node]
                        name = attrs.get("function", node)
                        path_names.append(name)
                    all_paths.append(path_names)
                except nx.NetworkXNoPath:
                    continue
        return all_paths
    except Exception:
        return []


def get_affected(graph: GraphType, function_name: str) -> List[str]:
    """Find functions affected by changes to the given function (downstream dependencies)"""
    if is_fast_graph(graph):
        return graph.get_affected(function_name)
    
    affected: Set[str] = set()
    source_nodes = [
        n for n, attr in graph.nodes(data=True)
        if attr.get("function") == function_name
    ]
    
    for source in source_nodes:
        # Get all descendants (nodes reachable from source)
        try:
            descendants = nx.descendants(graph, source)
            for node in descendants:
                attrs = graph.nodes[node]
                if attrs.get("function") and attrs.get("type") == "event":
                    affected.add(attrs["function"])
        except Exception:
            continue
    
    return sorted(list(affected))


def dead_code(graph: GraphType, source_path: str) -> List[str]:
    """Find potentially dead code (functions never called)"""
    all_funcs = set(list_functions(graph))
    
    # A function is dead if it has no callers
    # Entry points like main are not dead even if they have no callers
    dead: List[str] = []
    for func in all_funcs:
        callers_list = get_callers(graph, func)
        # Function is dead if no one calls it AND it's not an entry point
        if not callers_list and func not in ["main", "<module>", "__main__", "run"]:
            dead.append(func)
    
    return dead


def writes_to(graph: GraphType, variable_name: str) -> List[str]:
    """Find functions that write to a specific variable"""
    if is_fast_graph(graph):
        return []
    
    functions: Set[str] = set()
    var_id = f"var:{variable_name}"
    
    for node, attrs in graph.nodes(data=True):
        if attrs.get("type") == "event" and attrs.get("function"):
            # Check if this node has an edge TO the variable (writes)
            if graph.has_edge(node, var_id):
                functions.add(attrs["function"])
    
    return sorted(list(functions))


def reads_from(graph: GraphType, variable_name: str) -> List[str]:
    """Find functions that read from a specific variable"""
    if is_fast_graph(graph):
        return []
    
    functions: Set[str] = set()
    var_id = f"var:{variable_name}"
    
    for node, attrs in graph.nodes(data=True):
        if attrs.get("type") == "event" and attrs.get("function"):
            # Check if this node has an edge FROM the variable (reads)
            if graph.has_edge(var_id, node):
                functions.add(attrs["function"])
    
    return sorted(list(functions))


def data_paths(graph: GraphType, source_var: str, target_var: str) -> List[List[str]]:
    """Find data flow paths between variables"""
    if is_fast_graph(graph):
        return []
    
    source_id = f"var:{source_var}"
    target_id = f"var:{target_var}"
    
    if source_id not in graph or target_id not in graph:
        return []
    
    try:
        paths: List[List[str]] = []
        # Find paths through the graph
        for path in nx.all_simple_paths(graph, source_id, target_id, cutoff=5):
            # Convert to readable format
            readable: List[str] = []
            for node in path:
                if node.startswith("var:"):
                    readable.append(node[4:])  # Remove var: prefix
                else:
                    attrs = graph.nodes[node]
                    readable.append(attrs.get("function", node))
            paths.append(readable)
        return paths
    except Exception:
        return []


def graph_summary(graph: GraphType) -> Dict[str, Any]:
    """Get summary statistics about the graph"""
    stats: Dict[str, Any] = {
        "total_functions": len(list_functions(graph)),
        "is_fast_graph": is_fast_graph(graph)
    }
    
    if is_fast_graph(graph):
        nodes, edges = graph.get_stats()
        stats["nodes"] = nodes
        stats["edges"] = edges
    else:
        stats["nodes"] = graph.number_of_nodes()
        stats["edges"] = graph.number_of_edges()
        stats["density"] = nx.density(graph) if graph.number_of_nodes() > 0 else 0
    
    return stats