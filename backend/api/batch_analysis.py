"""
Batch Analysis Module - Week 4

Handles ZIP uploads, extracts files, runs tracer on all files,
and compares runs (before/after refactor).
"""

import zipfile
import io
import os
import tempfile
import ast
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime
import time
import traceback

from backend.tracer.python_tracer import trace_python_file, TraceEvent
from backend.causal.causal_discovery import CausalDiscovery, CausalGraph
from backend.causal.what_if_simulator import WhatIfSimulator


@dataclass
class BatchResult:
    """Result of batch analysis"""
    session_id: str
    files_analyzed: int
    total_events: int
    functions_found: List[str]
    languages: List[str]
    causal_graph: Optional[CausalGraph]
    errors: List[str]
    processing_time_ms: float


@dataclass
class ComparisonResult:
    """Comparison between two analysis runs"""
    baseline_session_id: str
    current_session_id: str
    new_functions: List[str]
    removed_functions: List[str]
    modified_functions: List[str]
    new_dependencies: List[Dict]
    removed_dependencies: List[Dict]
    risk_assessment: Dict


def extract_functions_from_ast(file_path: str) -> Tuple[List[str], List[TraceEvent]]:
    """Extract function names using AST parsing - works even if file can't execute."""
    functions = []
    events = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                if not func_name.startswith('_'):  # Skip private functions
                    functions.append(func_name)
                    
                    # Create synthetic trace event for this function
                    event = TraceEvent(
                        id=f"{file_path}:{node.lineno}:{func_name}",
                        event="call",
                        function=func_name,
                        filename=file_path,
                        lineno=node.lineno,
                        code=f"def {func_name}(...)",
                        parent=None,
                        language="python",
                        reads=[],
                        writes=[]
                    )
                    events.append(event)
        
        print(f"  📄 AST: Found {len(functions)} functions in {Path(file_path).name}")
                
    except Exception as e:
        print(f"⚠️ AST parsing failed for {file_path}: {e}")
    
    return functions, events


class BatchAnalyzer:
    """
    Analyzes multiple files in batch (ZIP upload).
    
    Features:
    1. Extract ZIP and find all source files
    2. Run tracer on each file
    3. Build combined causal graph
    4. Compare runs for refactoring analysis
    """
    
    def __init__(self):
        self.supported_extensions = {
            '.py': 'python',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'header',
            '.hpp': 'header'
        }
        self.sessions_dir = Path(__file__).parent.parent.parent / "data" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    async def analyze_zip(
        self, 
        zip_bytes: bytes,
        project_name: Optional[str] = None
    ) -> BatchResult:
        """
        Analyze all source files in a ZIP archive.
        """
        start_time = time.time()
        
        session_id = self._generate_session_id()
        all_events = []
        all_functions = set()
        errors = []
        files_analyzed = 0
        causal_graph = None
        
        try:
            # Extract and analyze
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                
                # Extract ZIP
                try:
                    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
                        zf.extractall(tmp_path)
                except zipfile.BadZipFile as e:
                    errors.append(f"Invalid ZIP file: {e}")
                    return BatchResult(
                        session_id=session_id,
                        files_analyzed=0,
                        total_events=0,
                        functions_found=[],
                        languages=[],
                        causal_graph=None,
                        errors=errors,
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Find and analyze source files
                source_files = self._find_source_files(tmp_path)
                print(f"🔍 Found {len(source_files)} source files in {tmp_path}")
                
                # Debug: list all files found
                if source_files:
                    for sf in source_files[:5]:  # Show first 5
                        print(f"  📄 {sf}")
                    if len(source_files) > 5:
                        print(f"  ... and {len(source_files) - 5} more")
                else:
                    # List all files in tmp_path for debugging
                    print(f"📂 Contents of {tmp_path}:")
                    for item in tmp_path.rglob('*'):
                        print(f"  {item}")
                
                for file_path in source_files:
                    events = []
                    ast_functions = []
                    try:
                        # Trace the file
                        events = trace_python_file(str(file_path))
                        print(f"✅ Traced {file_path}: {len(events)} events")
                    except Exception as e:
                        error_msg = f"Error tracing {file_path}: {str(e)}"
                        errors.append(error_msg)
                        print(f"⚠️ {error_msg}")
                    
                    # If tracer found no events, use AST as fallback
                    if not events:
                        print(f"  🔍 Using AST fallback for {file_path}")
                        ast_functions, ast_events = extract_functions_from_ast(str(file_path))
                        if ast_events:
                            events = ast_events
                            print(f"  ✅ AST found {len(ast_functions)} functions")
                        else:
                            print(f"  ❌ AST found no functions in {file_path}")
                    
                    # Count file and use events even if partial
                    if events:
                        all_events.extend(events)
                        files_analyzed += 1
                        
                        # Extract function names from events
                        for event in events:
                            if event.function and not event.function.startswith('__'):
                                all_functions.add(event.function)
                
                # Build causal graph
                causal_graph = None
                causal_graph_json = None
                if all_events:
                    try:
                        discovery = CausalDiscovery()
                        discovery.add_trace(all_events)
                        causal_graph = discovery.discover_causal_graph(min_confidence=0.2)
                        if causal_graph:
                            causal_graph_json = discovery.export_graph_json(causal_graph)
                    except Exception as e:
                        errors.append(f"Causal graph failed: {str(e)}")
                        print(f"⚠️ Causal graph error: {e}")
                
                processing_time = (time.time() - start_time) * 1000
                
                # Save session data
                try:
                    events_as_dicts = []
                    for event in all_events:
                        if hasattr(event, 'function'):
                            events_as_dicts.append({
                                'id': event.id,
                                'event': event.event,
                                'function': event.function,
                                'filename': event.filename,
                                'lineno': event.lineno,
                                'code': event.code,
                                'parent': event.parent,
                                'language': event.language,
                                'reads': event.reads,
                                'writes': event.writes
                            })
                        else:
                            events_as_dicts.append(event)
                
                    session_data = {
                        "session_id": session_id,
                        "files_analyzed": files_analyzed,
                        "functions": list(all_functions),
                        "events": events_as_dicts,
                        "languages": ["python"],
                        "errors": errors,
                        "timestamp": datetime.now().isoformat()
                    }
                    self._save_session(session_id, session_data)
                except Exception as e:
                    errors.append(f"Failed to save session: {str(e)}")
                    print(f"⚠️ Session save error: {e}")
                    
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            errors.append(f"Batch analysis failed: {str(e)}")
            print(f"❌ Batch analysis error: {e}")
            traceback.print_exc()
        
        # Debug: Show final counts
        print(f"📊 FINAL RESULT: {files_analyzed} files, {len(all_functions)} functions, {len(all_events)} events")
        
        # Build result
        result = BatchResult(
            session_id=session_id,
            files_analyzed=files_analyzed,
            total_events=len(all_events),
            functions_found=list(all_functions),
            languages=["python"],
            causal_graph=causal_graph,
            errors=errors,
            processing_time_ms=processing_time if 'processing_time' in locals() else (time.time() - start_time) * 1000
        )
        print(f"🎯 RETURNING: files={result.files_analyzed}, funcs={len(result.functions_found)}, events={result.total_events}, langs={result.languages}")
        # Debug: Show JSON output
        import json
        result_dict = {
            'session_id': result.session_id,
            'files_analyzed': result.files_analyzed,
            'total_events': result.total_events,
            'functions_found': result.functions_found,
            'languages': result.languages,
            'errors': result.errors,
            'processing_time_ms': result.processing_time_ms
        }
        print(f"📤 JSON RESPONSE: {json.dumps(result_dict, default=str)[:200]}")
        return result
    
    def _find_source_files(self, root_dir: Path) -> List[Path]:
        """Find all source files in directory."""
        source_files = []
        for ext in ['.py']:
            source_files.extend(root_dir.rglob(f"*{ext}"))
        # Skip __pycache__, hidden files, and virtual environments
        skip_dirs = ['__pycache__', '.venv', 'venv', 'env', '.git', 'node_modules', 'site-packages', 'dist-packages']
        source_files = [
            f for f in source_files 
            if not any(skip in str(f) for skip in skip_dirs) 
            and not f.name.startswith('.')
        ]
        return source_files
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        from datetime import datetime
        import uuid
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _save_session(self, session_id: str, data: Dict):
        """Save session data to file."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        session_file = self.sessions_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(data, f, default=str, indent=2)
        print(f"💾 Session saved: {session_file}")
    
    def _load_session(self, session_id: str) -> Optional[Dict]:
        """Load session data from file."""
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                print(f"📂 Session loaded: {session_file}")
                return data
            except Exception as e:
                print(f"⚠️ Error loading session {session_id}: {e}")
                return None
        return None


# Singleton instance
batch_analyzer = BatchAnalyzer()


def get_batch_analyzer():
    """Get the singleton batch analyzer instance."""
    return batch_analyzer
