"""
Batch Analysis Module - Week 4

Handles ZIP uploads, extracts files, runs tracer on all files,
and compares runs (before/after refactor).
"""

import zipfile
import io
import os
import tempfile
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime
import time
import traceback

from backend.tracer.python_tracer import trace_python_file
from backend.causal.causal_discovery import CausalDiscovery, CausalGraph
from backend.causal.what_if_simulator import WhatIfSimulator


@dataclass
class BatchResult:
    """Result of batch analysis"""
    session_id: str
    files_analyzed: int
    total_events: int
    functions_found: List[str]
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
                        causal_graph=None,
                        errors=errors,
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
                
                # Find and analyze source files
                source_files = self._find_source_files(tmp_path)
                
                for file_path in source_files:
                    try:
                        # Trace the file
                        events = trace_python_file(str(file_path))
                        all_events.extend(events)
                        files_analyzed += 1
                        
                        # Extract function names
                        for event in events:
                            if event.function and not event.function.startswith('__'):
                                all_functions.add(event.function)
                                
                    except Exception as e:
                        error_msg = f"Error analyzing {file_path}: {str(e)}"
                        errors.append(error_msg)
                        print(f"⚠️ {error_msg}")
                        continue
                
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
                    self._save_session(session_id, {
                        'session_id': session_id,
                        'project_name': project_name,
                        'files_analyzed': files_analyzed,
                        'functions': list(all_functions),
                        'events': all_events,
                        'causal_graph': causal_graph_json,
                        'timestamp': datetime.now().isoformat(),
                        'processing_time_ms': processing_time
                    })
                except Exception as e:
                    errors.append(f"Failed to save session: {str(e)}")
                    print(f"⚠️ Session save error: {e}")
                    
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            errors.append(f"Batch analysis failed: {str(e)}")
            print(f"❌ Batch analysis error: {e}")
            traceback.print_exc()
        
        return BatchResult(
            session_id=session_id,
            files_analyzed=files_analyzed,
            total_events=len(all_events),
            functions_found=list(all_functions),
            causal_graph=causal_graph,
            errors=errors,
            processing_time_ms=processing_time if 'processing_time' in locals() else (time.time() - start_time) * 1000
        )
    
    def _find_source_files(self, root_dir: Path) -> List[Path]:
        """Find all source files in directory."""
        source_files = []
        for ext in ['.py']:
            source_files.extend(root_dir.rglob(f"*{ext}"))
        # Skip __pycache__ and hidden files
        source_files = [f for f in source_files if '__pycache__' not in str(f) and not f.name.startswith('.')]
        return source_files
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        from datetime import datetime
        import uuid
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _save_session(self, session_id: str, data: Dict):
        """Save session data to file."""
        session_file = self.sessions_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(data, f, default=str, indent=2)


# Singleton instance
batch_analyzer = BatchAnalyzer()
