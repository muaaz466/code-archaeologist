"""
C++ Binary Tracer Wrapper
Provides Python interface to the Windows Debug API tracer
"""

import os
import sys
import ctypes
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional
from backend.core.models import TraceEvent


# Define ctypes structures matching C++ CallEvent
class CCallEvent(ctypes.Structure):
    _fields_ = [
        ("caller", ctypes.c_char_p),
        ("callee", ctypes.c_char_p),
        ("threadId", ctypes.c_ulong),
        ("timestamp", ctypes.c_ulonglong),
    ]


class CppTracerWrapper:
    """Python wrapper for the C++ binary tracer using Windows Debug API"""

    def __init__(self):
        self.lib = None
        self._load_library()

    def _load_library(self) -> bool:
        """Load the compiled C++ tracer DLL"""
        possible_paths = [
            Path(__file__).parent / "cpp_tracer.dll",
            Path(__file__).parent / "fast_ast.dll",
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    self.lib = ctypes.CDLL(str(path))
                    self._setup_function_signatures()
                    return True
                except OSError as e:
                    print(f"Warning: Could not load {path}: {e}")
                    continue

        print("Warning: C++ tracer DLL not found. Binary tracing unavailable.")
        return False

    def _setup_function_signatures(self):
        """Set up ctypes function signatures"""
        if not self.lib:
            return

        # tracer_create
        self.lib.tracer_create.argtypes = []
        self.lib.tracer_create.restype = ctypes.c_void_p

        # tracer_load
        self.lib.tracer_load.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        self.lib.tracer_load.restype = ctypes.c_int

        # tracer_run
        self.lib.tracer_run.argtypes = [ctypes.c_void_p]
        self.lib.tracer_run.restype = None

        # tracer_get_event_count
        self.lib.tracer_get_event_count.argtypes = [ctypes.c_void_p]
        self.lib.tracer_get_event_count.restype = ctypes.c_int

        # tracer_get_events
        self.lib.tracer_get_events.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(CCallEvent),
            ctypes.c_int
        ]
        self.lib.tracer_get_events.restype = None

        # tracer_destroy
        self.lib.tracer_destroy.argtypes = [ctypes.c_void_p]
        self.lib.tracer_destroy.restype = None

    def is_available(self) -> bool:
        """Check if C++ tracer is available"""
        return self.lib is not None

    def compile_cpp(self, source_path: str) -> Optional[str]:
        """Compile C++ source to executable"""
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        # Create temp directory for output
        exe_path = source.with_suffix('.exe')

        # Try compilers in order: g++, cl.exe
        compilers = [
            (['g++', str(source), '-o', str(exe_path), '-g'], 'MinGW'),
            (['cl.exe', '/Fe:' + str(exe_path), '/Zi', str(source)], 'MSVC'),
        ]

        for cmd, name in compilers:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(source.parent)
                )
                if result.returncode == 0 and exe_path.exists():
                    return str(exe_path)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        raise RuntimeError(
            "Failed to compile C++ source. "
            "Install MinGW (g++) or Visual Studio (cl.exe)"
        )

    def trace_binary(self, exe_path: str, args: str = "") -> List[TraceEvent]:
        """Trace a compiled binary and return TraceEvents"""
        if not self.is_available():
            raise RuntimeError("C++ tracer not available")

        exe = Path(exe_path)
        if not exe.exists():
            raise FileNotFoundError(f"Binary not found: {exe_path}")

        # Create tracer instance
        tracer = self.lib.tracer_create()
        if not tracer:
            raise RuntimeError("Failed to create tracer instance")

        try:
            # Load the binary
            exe_bytes = str(exe).encode('utf-8')
            args_bytes = args.encode('utf-8') if args else b""

            loaded = self.lib.tracer_load(tracer, exe_bytes, args_bytes)
            if not loaded:
                raise RuntimeError(f"Failed to load binary: {exe_path}")

            # Run the tracer (this blocks until process exits)
            self.lib.tracer_run(tracer)

            # Get event count
            count = self.lib.tracer_get_event_count(tracer)
            if count == 0:
                return []

            # Allocate buffer and retrieve events
            events_buffer = (CCallEvent * count)()
            self.lib.tracer_get_events(tracer, events_buffer, count)

            # Convert to TraceEvent objects
            trace_events = []
            for i, c_event in enumerate(events_buffer):
                caller = c_event.caller.decode('utf-8') if c_event.caller else ""
                callee = c_event.callee.decode('utf-8') if c_event.callee else ""

                trace_events.append(TraceEvent(
                    id=f"cpp_{i}",
                    event="call",
                    function=callee,
                    filename=str(exe),
                    lineno=0,
                    code=f"{caller} -> {callee}",
                    reads=[],
                    writes=[],
                    parent=caller if caller else None,
                    language="cpp"
                ))

            return trace_events

        finally:
            # Always cleanup
            self.lib.tracer_destroy(tracer)


def trace_cpp_binary(source_path: str) -> List[TraceEvent]:
    """
    Main entry point: Compile and trace a C++ source file

    Args:
        source_path: Path to .cpp source file

    Returns:
        List of TraceEvent objects
    """
    wrapper = CppTracerWrapper()

    if not wrapper.is_available():
        # Fallback: just compile and run without tracing
        print("C++ tracer not available, running without trace")
        exe_path = wrapper.compile_cpp(source_path)
        try:
            result = subprocess.run([exe_path], capture_output=True, text=True, timeout=10)
            print(f"Output: {result.stdout}")
            return []
        finally:
            if os.path.exists(exe_path):
                os.remove(exe_path)

    # Full tracing available
    exe_path = None
    try:
        # Compile
        exe_path = wrapper.compile_cpp(source_path)

        # Trace
        events = wrapper.trace_binary(exe_path)

        return events

    except Exception as e:
        print(f"Tracing failed: {e}")
        return []

    finally:
        # Cleanup exe
        if exe_path and os.path.exists(exe_path):
            try:
                os.remove(exe_path)
            except:
                pass
