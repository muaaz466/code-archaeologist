"""
Fast C++ graph implementation for Code Archaeologist
Provides high-performance graph operations using C++ backend
"""

import os
import ctypes
from typing import List, Tuple, Optional
from pathlib import Path
from backend.core.models import TraceEvent

# Define ctypes structures matching C++ TraceEvent
class CTraceEvent(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_char_p),
        ("event", ctypes.c_char_p),
        ("function", ctypes.c_char_p),
        ("filename", ctypes.c_char_p),
        ("lineno", ctypes.c_int),
        ("code", ctypes.c_char_p),
        ("parent", ctypes.c_char_p),
        ("language", ctypes.c_char_p),
        ("reads", ctypes.POINTER(ctypes.c_char_p)),
        ("writes", ctypes.POINTER(ctypes.c_char_p)),
        ("reads_count", ctypes.c_size_t),
        ("writes_count", ctypes.c_size_t),
    ]

class FastGraphWrapper:
    """Python wrapper for the fast C++ graph implementation"""

    def __init__(self):
        # Load the compiled C++ library
        lib_path = self._get_library_path()
        if lib_path and os.path.exists(lib_path):
            self.lib = ctypes.CDLL(lib_path)
            self._setup_function_signatures()
        else:
            # Fallback to Python implementation if C++ lib not available
            self.lib = None
            print("Warning: C++ graph library not found, using Python fallback")

    def _get_library_path(self) -> Optional[str]:
        """Find the compiled C++ library"""
        # Try common locations
        possible_paths = [
            Path(__file__).parent / "fast_graph.dll",  # Windows
            Path(__file__).parent / "fast_graph.so",   # Linux
            Path(__file__).parent / "libfast_graph.so", # Linux alternative
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        return None

    def _setup_function_signatures(self):
        """Set up ctypes function signatures"""
        if not self.lib:
            return

        # create_graph
        self.lib.create_graph.argtypes = [ctypes.POINTER(CTraceEvent), ctypes.c_size_t]
        self.lib.create_graph.restype = ctypes.c_void_p

        # delete_graph
        self.lib.delete_graph.argtypes = [ctypes.c_void_p]

        # get_functions
        self.lib.get_functions.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
        self.lib.get_functions.restype = ctypes.POINTER(ctypes.c_char_p)

        # get_callers
        self.lib.get_callers.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
        self.lib.get_callers.restype = ctypes.POINTER(ctypes.c_char_p)

        # get_callees
        self.lib.get_callees.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
        self.lib.get_callees.restype = ctypes.POINTER(ctypes.c_char_p)

        # get_affected
        self.lib.get_affected.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
        self.lib.get_affected.restype = ctypes.POINTER(ctypes.c_char_p)

        # free_string_array
        self.lib.free_string_array.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t]

        # get_node_count
        self.lib.get_node_count.argtypes = [ctypes.c_void_p]
        self.lib.get_node_count.restype = ctypes.c_size_t

        # get_edge_count
        self.lib.get_edge_count.argtypes = [ctypes.c_void_p]
        self.lib.get_edge_count.restype = ctypes.c_size_t

    def build_graph(self, events: List[TraceEvent]) -> Optional['FastGraphHandle']:
        """Build graph from trace events"""
        if not self.lib or not events:
            return None

        # Convert Python TraceEvent to C structures
        c_events = []
        string_buffers = []  # Keep references to prevent garbage collection
        ref_objects = []

        for event in events:
            # Convert strings to bytes
            id_bytes = event.id.encode('utf-8') if event.id else b""
            event_bytes = event.event.encode('utf-8') if event.event else b""
            function_bytes = event.function.encode('utf-8') if event.function else b""
            filename_bytes = event.filename.encode('utf-8') if event.filename else b""
            code_bytes = event.code.encode('utf-8') if event.code else b""
            parent_bytes = event.parent.encode('utf-8') if event.parent else b""
            language_bytes = event.language.encode('utf-8') if event.language else b"python"

            # Convert reads array
            reads_count = len(event.reads)
            if reads_count > 0:
                reads_strings = [s.encode('utf-8') for s in event.reads]
                reads_array = (ctypes.c_char_p * reads_count)(*reads_strings)
                string_buffers.extend(reads_strings)
                ref_objects.append(reads_array)
            else:
                reads_array = None

            # Convert writes array
            writes_count = len(event.writes)
            if writes_count > 0:
                writes_strings = [s.encode('utf-8') for s in event.writes]
                writes_array = (ctypes.c_char_p * writes_count)(*writes_strings)
                string_buffers.extend(writes_strings)
                ref_objects.append(writes_array)
            else:
                writes_array = None

            # Create C structure
            c_event = CTraceEvent(
                id=ctypes.c_char_p(id_bytes),
                event=ctypes.c_char_p(event_bytes),
                function=ctypes.c_char_p(function_bytes),
                filename=ctypes.c_char_p(filename_bytes),
                lineno=event.lineno,
                code=ctypes.c_char_p(code_bytes),
                parent=ctypes.c_char_p(parent_bytes),
                language=ctypes.c_char_p(language_bytes),
                reads=reads_array,
                writes=writes_array,
                reads_count=reads_count,
                writes_count=writes_count
            )

            c_events.append(c_event)
            string_buffers.extend([id_bytes, event_bytes, function_bytes, filename_bytes,
                                 code_bytes, parent_bytes, language_bytes])
            ref_objects.extend([id_bytes, event_bytes, function_bytes, filename_bytes,
                                code_bytes, parent_bytes, language_bytes])

        # Create array of C structures
        c_events_array = (CTraceEvent * len(events))(*c_events)

        # Call C++ function
        graph_ptr = self.lib.create_graph(c_events_array, len(events))

        if graph_ptr:
            return FastGraphHandle(graph_ptr, self.lib)
        return None

class FastGraphHandle:
    """Handle to a C++ graph instance"""

    def __init__(self, ptr: int, lib: ctypes.CDLL):
        self.ptr = ptr
        self.lib = lib

    def __del__(self):
        if self.ptr and self.lib:
            self.lib.delete_graph(self.ptr)

    def list_functions(self) -> List[str]:
        """Get list of functions in the graph"""
        if not self.ptr or not self.lib:
            return []

        count = ctypes.c_size_t()
        result_ptr = self.lib.get_functions(self.ptr, ctypes.byref(count))

        if not result_ptr:
            return []

        # Convert C strings to Python strings
        functions = []
        for i in range(count.value):
            functions.append(result_ptr[i].decode('utf-8'))

        # Free the C array
        self.lib.free_string_array(result_ptr, count.value)

        return functions

    def get_callers(self, function_name: str) -> List[str]:
        """Get callers from the C++ graph"""
        if not self.ptr or not self.lib:
            return []

        count = ctypes.c_size_t()
        result_ptr = self.lib.get_callers(self.ptr, function_name.encode('utf-8'), ctypes.byref(count))
        if not result_ptr:
            return []

        callers = [result_ptr[i].decode('utf-8') for i in range(count.value)]
        self.lib.free_string_array(result_ptr, count.value)
        return callers

    def get_callees(self, function_name: str) -> List[str]:
        """Get callees from the C++ graph"""
        if not self.ptr or not self.lib:
            return []

        count = ctypes.c_size_t()
        result_ptr = self.lib.get_callees(self.ptr, function_name.encode('utf-8'), ctypes.byref(count))
        if not result_ptr:
            return []

        callees = [result_ptr[i].decode('utf-8') for i in range(count.value)]
        self.lib.free_string_array(result_ptr, count.value)
        return callees

    def get_affected(self, function_name: str) -> List[str]:
        """Get affected downstream functions from the C++ graph"""
        if not self.ptr or not self.lib:
            return []

        count = ctypes.c_size_t()
        result_ptr = self.lib.get_affected(self.ptr, function_name.encode('utf-8'), ctypes.byref(count))
        if not result_ptr:
            return []

        affected = [result_ptr[i].decode('utf-8') for i in range(count.value)]
        self.lib.free_string_array(result_ptr, count.value)
        return affected

    def get_stats(self) -> Tuple[int, int]:
        """Get node and edge counts"""
        if not self.ptr or not self.lib:
            return (0, 0)

        nodes = self.lib.get_node_count(self.ptr)
        edges = self.lib.get_edge_count(self.ptr)
        return (nodes, edges)

# Global instance
_fast_graph = FastGraphWrapper()

def build_fast_graph(events: List[TraceEvent]) -> Optional[FastGraphHandle]:
    """Build a fast C++ graph from trace events"""
    return _fast_graph.build_graph(events)

def list_functions_fast(graph: FastGraphHandle) -> List[str]:
    """Fast function listing using C++"""
    if graph:
        return graph.list_functions()
    return []

def get_graph_stats_fast(graph: FastGraphHandle) -> Tuple[int, int]:
    """Fast graph statistics using C++"""
    if graph:
        return graph.get_stats()
    return (0, 0)