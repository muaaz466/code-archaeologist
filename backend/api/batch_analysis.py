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
    
    async def analyze_zip(
        self, 
        zip_bytes: bytes,
        project_name: Optional[str] = None
    ) -> BatchResult:
        """
        Analyze all source files in a ZIP archive.
        
        Args:
            zip_bytes: ZIP file contents
            project_name: Optional project name
            
        Returns:
            BatchResult with combined analysis
        """
        import time
        start_time = time.time()
        
        session_id = self._generate_session_id()
        all_events = []
        all_functions = set()
        errors = []
        files_analyzed = 0
        
        # Extract and analyze
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract ZIP
            zip_path = Path(tmpdir) / "upload.zip"
            with open(zip_path, 'wb') as f:
                f.write(zip_bytes)
            
            extract_dir = Path(tmpdir) / "extracted"
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(extract_dir)
            except zipfile.BadZipFile as e:
                return BatchResult(
                    session_id=session_id,
                    files_analyzed=0,
                    total_events=0,
                    functions_found=[],
                    causal_graph=None,
                    errors=[f"Invalid ZIP file: {e}"],
                    processing_time_ms=0.0
                )
            
            # Find and analyze source files
            source_files = self._find_source_files(extract_dir)
            
            for src_file in source_files:
                try:
                    events = self._analyze_file(src_file)
                    all_events.extend(events)
                    
                    # Extract function names
                    for event in events:
                        if 'function' in event:
                            all_functions.add(event['function'])
                    
                    files_analyzed += 1
                    
                except Exception as e:
                    errors.append(f"Error analyzing {src_file}: {e}")
        
        # Build causal graph
        causal_graph = None
        causal_graph_json = None
        if all_events:
            discovery = CausalDiscovery()
            discovery.add_trace(all_events)
            causal_graph = discovery.discover_causal_graph(min_confidence=0.2)
            if causal_graph:
                causal_graph_json = discovery.export_graph_json(causal_graph)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Save session data
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
        
        return BatchResult(
            session_id=session_id,
            files_analyzed=files_analyzed,
            total_events=len(all_events),
            functions_found=list(all_functions),
            causal_graph=causal_graph,
            errors=errors,
            processing_time_ms=processing_time
        )
    
    def _find_source_files(self, root_dir: Path) -> List[Path]:
        """Find all supported source files in directory"""
        source_files = []
        
        for ext in self.supported_extensions.keys():
            source_files.extend(root_dir.rglob(f"*{ext}"))
        
        # Filter out common non-project directories
        filtered = []
        for f in source_files:
            parts = f.parts
            skip = any(p in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']
                      for p in parts)
            if not skip:
                filtered.append(f)
        
        return filtered
    
    def _analyze_file(self, file_path: Path) -> List[Dict]:
        """Analyze a single source file"""
        ext = file_path.suffix.lower()
        language = self.supported_extensions.get(ext)
        
        if language == 'python':
            return trace_python_file(str(file_path))
        elif language == 'java':
            # Placeholder for Java tracer integration
            return self._placeholder_trace(file_path, language)
        else:
            # Other languages - placeholder
            return self._placeholder_trace(file_path, language)
    
    def _placeholder_trace(self, file_path: Path, language: str) -> List[Dict]:
        """Placeholder trace for non-Python languages"""
        # In real implementation, would call language-specific tracer
        return [{
            'function': f'<{language}_placeholder>',
            'file': str(file_path),
            'language': language,
            'timestamp': datetime.now().timestamp()
        }]
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        from uuid import uuid4
        return f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    
    def _save_session(self, session_id: str, data: Dict):
        """Save session data to storage"""
        # In real implementation, save to database or file
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        
        with open(sessions_dir / f"{session_id}.json", 'w') as f:
            json.dump(data, f, indent=2)
    
    def compare_runs(
        self, 
        baseline_session_id: str, 
        current_session_id: str
    ) -> ComparisonResult:
        """
        Compare two analysis runs (before/after refactor).
        
        Args:
            baseline_session_id: Previous run ID
            current_session_id: Current run ID
            
        Returns:
            ComparisonResult with differences
        """
        baseline = self._load_session(baseline_session_id)
        current = self._load_session(current_session_id)
        
        if not baseline or not current:
            return ComparisonResult(
                baseline_session_id=baseline_session_id,
                current_session_id=current_session_id,
                new_functions=[],
                removed_functions=[],
                modified_functions=[],
                new_dependencies=[],
                removed_dependencies=[],
                risk_assessment={'error': 'Session not found'}
            )
        
        baseline_funcs = set(baseline.get('functions', []))
        current_funcs = set(current.get('functions', []))
        
        new_functions = list(current_funcs - baseline_funcs)
        removed_functions = list(baseline_funcs - current_funcs)
        
        # Compare causal graphs
        baseline_graph = baseline.get('causal_graph', {})
        current_graph = current.get('causal_graph', {})
        
        baseline_edges = self._extract_edges(baseline_graph)
        current_edges = self._extract_edges(current_graph)
        
        new_deps = [e for e in current_edges if e not in baseline_edges]
        removed_deps = [e for e in baseline_edges if e not in current_edges]
        
        # Risk assessment
        risk = self._assess_risk(
            removed_functions,
            removed_deps,
            new_deps
        )
        
        return ComparisonResult(
            baseline_session_id=baseline_session_id,
            current_session_id=current_session_id,
            new_functions=new_functions,
            removed_functions=removed_functions,
            modified_functions=[],  # Would need AST diff
            new_dependencies=new_deps,
            removed_dependencies=removed_deps,
            risk_assessment=risk
        )
    
    def _load_session(self, session_id: str) -> Optional[Dict]:
        """Load session data from storage"""
        sessions_dir = Path("sessions")
        session_file = sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file) as f:
            return json.load(f)
    
    def _extract_edges(self, graph_data: Dict) -> List[Dict]:
        """Extract edges from graph data"""
        return graph_data.get('edges', [])
    
    def _assess_risk(
        self,
        removed_functions: List[str],
        removed_deps: List[Dict],
        new_deps: List[Dict]
    ) -> Dict:
        """Assess risk of changes"""
        risk_level = 'low'
        concerns = []
        
        if removed_functions:
            concerns.append(f"{len(removed_functions)} functions removed")
            if len(removed_functions) > 5:
                risk_level = 'high'
            elif len(removed_functions) > 2:
                risk_level = 'medium'
        
        if removed_deps:
            concerns.append(f"{len(removed_deps)} dependencies removed")
        
        # Check for circular dependencies in new graph
        if self._has_circular_deps(new_deps):
            concerns.append("Circular dependencies detected")
            risk_level = 'high'
        
        return {
            'level': risk_level,
            'concerns': concerns,
            'recommendation': 'review' if risk_level != 'low' else 'proceed'
        }
    
    def _has_circular_deps(self, edges: List[Dict]) -> bool:
        """Check for circular dependencies (simplified)"""
        # Build adjacency list
        adjacency = {}
        for e in edges:
            src = e.get('source', '')
            tgt = e.get('target', '')
            if src not in adjacency:
                adjacency[src] = []
            adjacency[src].append(tgt)
        
        # DFS for cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in adjacency:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def get_batch_summary(self, session_id: str) -> Dict:
        """Get summary of batch analysis"""
        session = self._load_session(session_id)
        
        if not session:
            return {'error': 'Session not found'}
        
        return {
            'session_id': session_id,
            'files_analyzed': session.get('files_analyzed', 0),
            'total_events': len(session.get('events', [])),
            'functions_count': len(session.get('functions', [])),
            'has_causal_graph': session.get('causal_graph') is not None,
            'timestamp': session.get('timestamp'),
            'processing_time_ms': session.get('processing_time_ms', 0)
        }


# Singleton instance for API
_batch_analyzer = None

def get_batch_analyzer() -> BatchAnalyzer:
    """Get singleton batch analyzer instance"""
    global _batch_analyzer
    if _batch_analyzer is None:
        _batch_analyzer = BatchAnalyzer()
    return _batch_analyzer
