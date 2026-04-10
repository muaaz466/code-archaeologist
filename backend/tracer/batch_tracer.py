from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Set
import networkx as nx

from backend.tracer.python_tracer import trace_python_file
from backend.graph.builder import build_graph
from backend.core.models import TraceEvent


def discover_python_files(folder_path: str) -> List[str]:
    """Recursively find all Python files in a folder"""
    python_files = []
    root = Path(folder_path)
    
    for py_file in root.rglob("*.py"):
        # Skip common non-project directories
        if any(part.startswith('.') for part in py_file.parts):
            continue
        if 'site-packages' in str(py_file) or '__pycache__' in str(py_file):
            continue
        python_files.append(str(py_file))
    
    return sorted(python_files)


def trace_folder(folder_path: str, entry_point: str | None = None) -> Dict[str, List[TraceEvent]]:
    """
    Analyze all Python files in a folder.
    
    Args:
        folder_path: Root directory to scan
        entry_point: Specific file to execute (if None, tries to find main/__main__)
    
    Returns:
        Dictionary mapping file paths to their trace events
    """
    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"{folder_path} is not a directory")
    
    all_files = discover_python_files(folder_path)
    print(f"Found {len(all_files)} Python files in {folder_path}")
    
    results = {}
    
    # Strategy 1: If entry point provided, trace it (captures imported modules too)
    if entry_point:
        full_path = os.path.join(folder_path, entry_point)
        if os.path.exists(full_path):
            print(f"Tracing entry point: {entry_point}")
            results[full_path] = trace_python_file(full_path)
    
    # Strategy 2: Trace each file individually (limited - won't show cross-file calls)
    for py_file in all_files:
        if py_file not in results:  # Skip if already traced as entry point
            try:
                print(f"Analyzing: {Path(py_file).name}")
                events = trace_python_file(py_file)
                results[py_file] = events
            except Exception as e:
                print(f"Warning: Failed to trace {py_file}: {e}")
                results[py_file] = []
    
    return results


def merge_traces(trace_results: Dict[str, List[TraceEvent]]) -> nx.DiGraph:
    """Combine multiple file traces into a unified project graph"""
    master_graph = nx.DiGraph()
    
    for file_path, events in trace_results.items():
        # Build individual graph
        file_graph = build_graph(events)
        
        # Add prefix to distinguish files
        file_name = Path(file_path).name
        
        # Merge nodes with file attribution
        for node, attrs in file_graph.nodes(data=True):
            new_node = f"{file_name}:{node}"
            master_graph.add_node(new_node, **attrs, source_file=file_name)
        
        # Merge edges
        for u, v, attrs in file_graph.edges(data=True):
            new_u = f"{file_name}:{u}"
            new_v = f"{file_name}:{v}"
            master_graph.add_edge(new_u, new_v, **attrs)
    
    print(f"Merged graph: {master_graph.number_of_nodes()} nodes, {master_graph.number_of_edges()} edges")
    return master_graph


def find_cross_file_dependencies(folder_path: str) -> List[Dict[str, str]]:
    """
    Static analysis: Find which files import which other files
    (Faster than tracing, but only shows import relationships, not runtime calls)
    """
    python_files = discover_python_files(folder_path)
    file_names = {Path(f).stem: f for f in python_files}
    dependencies = []
    
    for py_file in python_files:
        content = Path(py_file).read_text(encoding='utf-8', errors='ignore')
        tree = __import__('ast').parse(content)
        
        for node in __import__('ast').walk(tree):
            if isinstance(node, __import__('ast').Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module in file_names and file_names[module] != py_file:
                        dependencies.append({
                            "from": Path(py_file).name,
                            "to": Path(file_names[module]).name,
                            "type": "import"
                        })
            elif isinstance(node, __import__('ast').ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module in file_names and file_names[module] != py_file:
                        dependencies.append({
                            "from": Path(py_file).name,
                            "to": Path(file_names[module]).name,
                            "type": "import_from"
                        })
    
    return dependencies