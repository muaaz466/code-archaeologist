"""
C++ Binary Tracer - Main entry point
Wires up the C++ Windows Debug API tracer via ctypes wrapper
"""

from typing import List
from backend.core.models import TraceEvent
from backend.tracer.cpp_tracer_wrapper import trace_cpp_binary as _trace_cpp_binary


def trace_cpp_binary(source_path: str) -> List[TraceEvent]:
    """
    Trace a C++ binary by compiling and running it with debug API.

    Args:
        source_path: Path to .cpp source file

    Returns:
        List of TraceEvent objects representing function calls
    """
    return _trace_cpp_binary(source_path)
