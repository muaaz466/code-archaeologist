from __future__ import annotations

import ast
import linecache
import re
import runpy
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, List, Dict, Optional, Union  # Added List, Dict, Optional

from backend.core.models import TraceEvent

# Try to import fast C++ AST analyzer - fallback gracefully if not compiled
try:
    from backend.tracer.fast_ast import analyze_ast as fast_analyze_ast  # type: ignore
    HAS_FAST_AST = True
except ImportError:
    HAS_FAST_AST = False
    fast_analyze_ast = None  # type: ignore


def extract_vars_from_code(code_line: str) -> tuple[List[str], List[str]]:
    """Simple regex-based variable extraction for reads/writes"""
    if not code_line:
        return [], []
    
    # Remove comments
    code = code_line.split('#')[0].strip()
    if not code:
        return [], []
    
    reads = []
    writes = []
    
    # Assignment pattern: var = ...
    import re
    assign_match = re.match(r'^(\w+)\s*=', code)
    if assign_match:
        writes.append(assign_match.group(1))
    
    # Extract all identifiers (potential reads)
    keywords = {'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'return', 
                'import', 'from', 'as', 'try', 'except', 'finally', 'with',
                'pass', 'break', 'continue', 'lambda', 'yield', 'raise', 'True', 
                'False', 'None', 'and', 'or', 'not', 'in', 'is', 'print'}
    
    all_vars = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
    for var in all_vars:
        if var not in keywords and var not in writes:
            reads.append(var)
    
    return reads, writes


def _should_skip_stdlib(filename: str, func_name: str) -> bool:
    """Skip Python standard library and internals"""
    fname_lower = filename.lower()
    
    if filename.startswith(('<frozen', '<built-in', '__builtin__')):
        return True
        
    std_lib_indicators = [
        'pythonsoftwarefoundation.python',
        '\\lib\\', '/lib/',
        'site-packages', 'dist-packages',
        'importlib', 'pkgutil', 'runpy',
        'pathlib', 'os.py', 'sys.py',
        'tracer.py', 'python_tracer.py',
        'backend\\tracer', 'backend/tracer',
        'streamlit',
        'local-packages',
    ]
    
    if any(ind in fname_lower for ind in std_lib_indicators):
        return True
        
    skip_funcs = {'<module>', '<genexpr>', '<listcomp>', '<setcomp>', '<dictcomp>', '<lambda>'}
    if func_name in skip_funcs:
        return True
        
    return False


def _extract_targets(node: ast.AST) -> List[str]:
    """Extract variable names from assignment targets"""
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        result: List[str] = []
        for element in node.elts:
            result.extend(_extract_targets(element))
        return result
    if isinstance(node, ast.Attribute):
        return []
    return []


def _collect_reads(node: ast.AST) -> List[str]:
    """Collect all variable reads in a node"""
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            names.add(child.id)
    return sorted(names)


def analyze_source_variables(source_path: str) -> Dict[int, Dict[str, List[str]]]:
    """Analyze source code for variable reads/writes per line"""
    source_text = Path(source_path).read_text(encoding="utf-8")
    tree = ast.parse(source_text)

    # Try fast C++ analyzer first
    if HAS_FAST_AST and fast_analyze_ast:
        try:
            result = fast_analyze_ast(tree)
            line_vars: Dict[int, Dict[str, List[str]]] = {}
            for func_name, func_info in result.items():
                if "variables" in func_info:
                    for lineno_str, var_info in func_info["variables"].items():
                        lineno = int(lineno_str)
                        if lineno not in line_vars:
                            line_vars[lineno] = {"reads": [], "writes": []}
                        if "reads" in var_info:
                            line_vars[lineno]["reads"].extend(var_info["reads"])
                        if "writes" in var_info:
                            line_vars[lineno]["writes"].extend(var_info["writes"])

            # Deduplicate
            for line, data in line_vars.items():
                data["reads"] = sorted(set(data["reads"]))
                data["writes"] = sorted(set(data["writes"]))

            return line_vars

        except Exception as e:
            print(f"Warning: Fast C++ AST analyzer failed ({e}), falling back to Python")

    # Fallback to Python implementation
    line_vars: Dict[int, Dict[str, List[str]]] = defaultdict(lambda: {"reads": [], "writes": []})

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            writes: List[str] = []
            for target in node.targets:
                writes.extend(_extract_targets(target))
            reads = _collect_reads(node.value)
            if node.lineno:
                line_vars[node.lineno]["writes"].extend(writes)
                line_vars[node.lineno]["reads"].extend(reads)
        elif isinstance(node, ast.AugAssign):
            writes = _extract_targets(node.target)
            reads = _collect_reads(node.value)
            if node.lineno:
                line_vars[node.lineno]["writes"].extend(writes)
                line_vars[node.lineno]["reads"].extend(reads)
        elif isinstance(node, ast.AnnAssign) and node.target is not None:
            writes = _extract_targets(node.target)
            reads = _collect_reads(node.annotation)
            if node.value is not None:
                reads.extend(_collect_reads(node.value))
            if node.lineno:
                line_vars[node.lineno]["writes"].extend(writes)
                line_vars[node.lineno]["reads"].extend(reads)
        elif isinstance(node, ast.For):
            writes = _extract_targets(node.target)
            reads = _collect_reads(node.iter)
            if node.lineno:
                line_vars[node.lineno]["writes"].extend(writes)
                line_vars[node.lineno]["reads"].extend(reads)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.lineno:
            line_vars[node.lineno]["reads"].append(node.id)

    for line, data in line_vars.items():
        data["reads"] = sorted(set(data["reads"]))
        data["writes"] = sorted(set(data["writes"]))

    return dict(line_vars)


def trace_python_file(source_path: str, project_root: Optional[str] = None) -> List[TraceEvent]:
    """
    Execute a Python file and collect execution trace.
    
    Args:
        source_path: The Python file to execute
        project_root: If provided, also trace files in this directory
    """
    file_path = Path(source_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    project_path = Path(project_root) if project_root else None
    
    variable_map = analyze_source_variables(str(file_path))
    events: List[TraceEvent] = []

    def tracer(frame, event, arg):
        if event not in {"call", "line", "return"}:
            return tracer

        code = frame.f_code
        filename = code.co_filename
        func_name = code.co_name

        # Skip standard library - but allow <module> for line events (top-level code)
        if _should_skip_stdlib(filename, func_name):
            # Don't skip <module> for line events - that's where top-level code runs
            if func_name == '<module>' and event == 'line':
                pass  # Allow top-level code
            else:
                return tracer
            
        # Filter by project scope
        if project_path:
            file_in_project = (
                filename == str(file_path) or 
                str(Path(filename).absolute()).startswith(str(project_path.absolute()))
            )
            if not file_in_project:
                return tracer
        else:
            # Original single-file behavior
            if filename != str(file_path):
                return tracer

        parent = frame.f_back
        reads: List[str] = []
        writes: List[str] = []
        code_line = ""
        
        try:
            if Path(filename).exists():
                line_data = variable_map.get(frame.f_lineno, {})
                reads = line_data.get("reads", [])
                writes = line_data.get("writes", [])
                code_line = linecache.getline(filename, frame.f_lineno).strip()
                
                # Debug output
                if code_line and ('=' in code_line or 'return' in code_line):
                    print(f"[TRACE] Line {frame.f_lineno}: '{code_line}'")
                    print(f"[TRACE]   AST reads={reads}, writes={writes}")
                
                # Fallback: if AST extraction is empty, use regex-based extraction
                if not reads and not writes and code_line:
                    reads, writes = extract_vars_from_code(code_line)
                    if reads or writes:
                        print(f"[REGEX] Line {frame.f_lineno}: '{code_line}' -> reads={reads}, writes={writes}")
        except Exception as e:
            print(f"[ERROR] Variable extraction: {e}")
            pass

        event_data = TraceEvent(
            id=f"{filename}:{code.co_firstlineno}:{func_name}",
            event=event,
            function=func_name,
            filename=filename,
            lineno=frame.f_lineno,
            code=linecache.getline(filename, frame.f_lineno).strip(),
            parent=f"{parent.f_code.co_filename}:{parent.f_code.co_firstlineno}:{parent.f_code.co_name}" if parent else None,
            language="python",
            reads=reads,
            writes=writes,
        )
        events.append(event_data)
        return tracer

    old_trace = sys.gettrace()
    sys.settrace(tracer)
    
    if project_path:
        sys.path.insert(0, str(project_path))
    
    try:
        runpy.run_path(str(file_path), run_name="__main__")
    except Exception as e:
        # Log error but don't crash - return partial trace if any
        print(f"⚠️ Error tracing {file_path}: {e}")
        # Add a synthetic event to show the file was attempted
        fname = str(file_path)
        events.append(TraceEvent(
            id=f"{fname}:1:__error__",
            event="error",
            function="__trace_error__",
            filename=fname,
            lineno=1,
            code=f"# Trace error: {str(e)[:100]}",
            parent=None,
            language="python",
            reads=[],
            writes=[],
        ))
    finally:
        sys.settrace(old_trace)
        if project_path:
            try:
                sys.path.remove(str(project_path))
            except ValueError:
                pass

    return events