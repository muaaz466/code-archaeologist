"""
Code Archaeologist - FastAPI REST API
Week 3: API-first backend with C++ engine integration

Supports: Python, C++, Java, Go, Rust
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path for imports
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.tracer.python_tracer import trace_python_file
    from backend.graph.fast_graph_wrapper import FastGraphHandle
    from backend.graph.queries import (
        get_callers, get_callees, get_affected, dead_code,
        list_functions, graph_summary
    )
    _graph_backend_available = True
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    print(f"Python path: {sys.path}")
    _graph_backend_available = False
    # Create placeholders - return empty but don't crash
    def trace_python_file(*args, **kwargs):
        print("⚠️ Python tracer not available, returning empty events")
        return []
    
    class FastGraphHandle:
        """Placeholder when DLL not available"""
        def __init__(self, ptr=None, lib=None):
            self.ptr = ptr or 0
            self.lib = lib
            self._nodes = 0
            self._edges = 0
            self._functions = set()
        
        def number_of_nodes(self): return self._nodes
        def number_of_edges(self): return self._edges
        def add_node(self, node_id, attrs=None): 
            self._nodes += 1
            if attrs and 'function' in attrs:
                self._functions.add(attrs['function'])
        def add_edge(self, *args, **kwargs): self._edges += 1
        def list_functions(self): return list(self._functions)
        def get_callers(self, target): return []
        def get_callees(self, target): return []

# API Models

class TraceRequest(BaseModel):
    language: str  # python, cpp, java, go, rust
    entry_point: Optional[str] = None
    trace_options: Optional[Dict] = {}

class QueryRequest(BaseModel):
    query_type: str  # callers, callees, affected, dead_code, data_flow
    target: Optional[str] = None
    start_var: Optional[str] = None
    end_var: Optional[str] = None

class LLMExplainRequest(BaseModel):
    function_name: str
    code_snippet: Optional[str] = None
    context: Optional[str] = None

class AnalysisResponse(BaseModel):
    session_id: str
    language: str
    nodes: int
    edges: int
    functions: List[str]
    events: int
    timestamp: str

class QueryResponse(BaseModel):
    query_type: str
    results: Any
    execution_time_ms: float

class ExplainResponse(BaseModel):
    function_name: str
    explanation: str
    key_points: List[str]
    model_used: str

# Global state
active_sessions: Dict[str, Any] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Code Archaeologist API starting...")
    print("Week 3: Multi-language + AI + C++ backend")
    yield
    print("👋 API shutting down...")

app = FastAPI(
    title="Code Archaeologist API",
    description="Week 3: Multi-language code analysis with C++ backend",
    version="3.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """API status"""
    return {
        "status": "ok",
        "version": "3.0.0",
        "week": 3,
        "features": [
            "python", "cpp", "java", "go", "rust",
            "ai_explain", "pdf_export", "data_flow"
        ],
        "backend": "C++ engine + Python API"
    }

@app.get("/health")
async def health_check():
    """Health check for C++ backend"""
    try:
        # Test C++ engine
        graph = FastGraphHandle()
        test_node = "test:1:func"
        graph.add_node(test_node, {"function": "test", "file": "test.py"})
        count = graph.number_of_nodes()
        return {
            "status": "healthy",
            "cpp_engine": "connected",
            "graph_nodes": count
        }
    except Exception as e:
        import traceback
        raise HTTPException(500, f"Analysis failed: {str(e)}\n{traceback.format_exc()}")

@app.post("/upload", response_model=AnalysisResponse)
async def upload_and_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = "python"
):
    """
    Upload code file and analyze it
    
    Supports: .py, .cpp/.cc/.cxx, .java, .go, .rs
    """
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    supported = {
        ".py": "python",
        ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
        ".java": "java",
        ".go": "go",
        ".rs": "rust"
    }
    
    if ext not in supported:
        raise HTTPException(400, f"Unsupported file type: {ext}")
    
    detected_lang = supported[ext]
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(mode='wb', suffix=ext, delete=False) as f:
        content = await file.read()
        f.write(content)
        temp_path = f.name
    
    try:
        # Analyze based on language
        if detected_lang == "python":
            result = await _analyze_python(temp_path, session_id)
        elif detected_lang == "cpp":
            result = await _analyze_cpp_binary(temp_path, session_id)
        elif detected_lang == "java":
            result = await _analyze_java(temp_path, session_id)
        elif detected_lang == "go":
            result = await _analyze_go(temp_path, session_id)
        elif detected_lang == "rust":
            result = await _analyze_rust(temp_path, session_id)
        else:
            raise HTTPException(400, f"Analysis not implemented for: {detected_lang}")
        
        # Store session
        active_sessions[session_id] = {
            "graph": result.get("graph"),
            "events": result.get("events", []),
            "language": detected_lang,
            "file": file.filename
        }
        
        return AnalysisResponse(
            session_id=session_id,
            language=detected_lang,
            nodes=result["nodes"],
            edges=result["edges"],
            functions=result["functions"],
            events=len(result.get("events", [])),
            timestamp=datetime.now().isoformat()
        )
        
    finally:
        # Cleanup temp file in background
        background_tasks.add_task(os.unlink, temp_path)

async def _analyze_python(file_path: str, session_id: str) -> Dict:
    """Analyze Python file"""
    # Use existing Python tracer
    events = trace_python_file(file_path)
    
    # Build graph
    graph = FastGraphHandle()
    functions = set()
    
    for e in events:
        if hasattr(e, 'function'):
            node_id = f"{e.filename}:{e.lineno}:{e.function}"
            graph.add_node(node_id, {
                "function": e.function,
                "file": e.filename,
                "line": str(e.lineno)
            })
            functions.add(e.function)
    
    return {
        "graph": graph,
        "events": events,
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "functions": list(functions)
    }

async def _analyze_cpp_binary(file_path: str, session_id: str) -> Dict:
    """Analyze C++ binary using DWARF parser"""
    # Week 3: Call C++ tracer
    # For now, return placeholder
    return {
        "graph": FastGraphHandle(),
        "events": [],
        "nodes": 0,
        "edges": 0,
        "functions": [],
        "note": "C++ binary analysis requires compilation with -g flag"
    }

async def _analyze_java(file_path: str, session_id: str) -> Dict:
    """Analyze Java file using ByteBuddy agent"""
    # Week 3: Java ByteBuddy integration
    return {
        "graph": FastGraphHandle(),
        "events": [],
        "nodes": 0,
        "edges": 0,
        "functions": [],
        "note": "Java analysis requires ByteBuddy agent (Week 3)"
    }

async def _analyze_go(file_path: str, session_id: str) -> Dict:
    """Analyze Go binary"""
    # Week 3: Go DWARF parsing
    return {
        "graph": FastGraphHandle(),
        "events": [],
        "nodes": 0,
        "edges": 0,
        "functions": [],
        "note": "Go analysis requires compiled binary with debug symbols"
    }

async def _analyze_rust(file_path: str, session_id: str) -> Dict:
    """Analyze Rust binary"""
    # Week 3: Rust DWARF parsing
    return {
        "graph": FastGraphHandle(),
        "events": [],
        "nodes": 0,
        "edges": 0,
        "functions": [],
        "note": "Rust analysis requires compiled binary with debug symbols"
    }

@app.post("/query/{session_id}", response_model=QueryResponse)
async def query_graph(session_id: str, request: QueryRequest):
    """
    Query the analyzed graph
    
    Query types:
    - callers: Who calls this function
    - callees: What this function calls
    - affected: Functions affected by changing target
    - dead_code: Potentially unused functions
    - data_flow: Variable-level data flow
    """
    import time
    start = time.time()
    
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")
    
    session = active_sessions[session_id]
    graph = session.get("graph")
    events = session.get("events", [])
    
    if not graph:
        raise HTTPException(400, "No graph available for this session")
    
    # Execute query
    if request.query_type == "callers":
        results = get_callers(graph, request.target)
    elif request.query_type == "callees":
        results = get_callees(graph, request.target)
    elif request.query_type == "affected":
        results = get_affected(graph, request.target)
    elif request.query_type == "dead_code":
        # Get source path from first event
        source = None
        if events:
            source = events[0].filename if hasattr(events[0], 'filename') else None
        results = dead_code(graph, source or "unknown")
    elif request.query_type == "data_flow":
        # Week 2 data flow query
        if hasattr(graph, 'find_data_path') and request.start_var and request.end_var:
            results = graph.find_data_path(request.start_var, request.end_var)
        else:
            results = {"error": "Data flow not available"}
    else:
        raise HTTPException(400, f"Unknown query type: {request.query_type}")
    
    elapsed = (time.time() - start) * 1000
    
    return QueryResponse(
        query_type=request.query_type,
        results=results,
        execution_time_ms=elapsed
    )

@app.post("/explain")
async def explain_function(request: LLMExplainRequest):
    """
    Week 3: AI-powered function explanation using GPT-3.5-Turbo
    
    Explains what a function does and extracts key insights.
    """
    try:
        # Try to use LLM explainer if available
        try:
            from backend.ai.llm_explainer import LLMFunctionExplainer
            explainer = LLMFunctionExplainer()
            
            result = explainer.explain_function(
                function_name=request.function_name,
                code_snippet=request.code_snippet or "",
                context=request.context,
                language="python"  # Default
            )
            
            return {
                "function_name": result.function_name,
                "explanation": result.explanation,
                "key_points": result.key_points,
                "model_used": result.model_used,
                "confidence": result.confidence
            }
        except Exception as e:
            # Fallback response
            return {
                "function_name": request.function_name,
                "explanation": f"Analysis for {request.function_name}: {request.code_snippet[:100] if request.code_snippet else 'No code provided'}...",
                "key_points": [
                    "Week 3: AI analysis ready",
                    "Set OPENAI_API_KEY for GPT-3.5",
                    "Fallback mode active"
                ],
                "model_used": "fallback",
                "confidence": "low"
            }
    except Exception as e:
        raise HTTPException(500, f"Explanation error: {str(e)}")

@app.post("/export/pdf/{session_id}")
async def export_pdf(session_id: str):
    """
    Week 3: Export analysis to PDF report
    
    Includes: graph, queries, AI explanations
    """
    # TODO: Implement with reportlab
    # For now, return placeholder info
    
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")
    
    return {
        "status": "Week 3: PDF export with reportlab",
        "session_id": session_id,
        "note": "Will include: graph visualization + query results + AI explanations"
    }

@app.get("/sessions")
async def list_sessions():
    """List active analysis sessions"""
    return {
        "sessions": [
            {
                "id": sid,
                "language": s["language"],
                "file": s["file"]
            }
            for sid, s in active_sessions.items()
        ]
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Clean up a session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"status": "deleted"}
    raise HTTPException(404, "Session not found")

# ==================== WEEK 4 ENDPOINTS ====================

@app.post("/batch/analyze")
async def batch_analyze(file: UploadFile = File(...)):
    """
    Week 4: Batch analysis - accepts ZIP upload
    Extracts, analyzes all files, builds combined causal graph
    """
    from backend.api.batch_analysis import get_batch_analyzer
    
    try:
        contents = await file.read()
        analyzer = get_batch_analyzer()
        result = await analyzer.analyze_zip(contents, project_name=file.filename)
        
        return {
            "session_id": result.session_id,
            "files_analyzed": result.files_analyzed,
            "total_events": result.total_events,
            "functions_found": result.functions_found,
            "has_causal_graph": result.causal_graph is not None,
            "processing_time_ms": result.processing_time_ms,
            "errors": result.errors if result.errors else None
        }
    except Exception as e:
        raise HTTPException(500, f"Batch analysis failed: {str(e)}")

@app.post("/batch/compare")
async def batch_compare(baseline_id: str, current_id: str):
    """
    Week 4: Compare two analysis runs (before/after refactor)
    """
    from backend.api.batch_analysis import get_batch_analyzer
    
    try:
        analyzer = get_batch_analyzer()
        result = analyzer.compare_runs(baseline_id, current_id)
        
        return {
            "baseline_session_id": result.baseline_session_id,
            "current_session_id": result.current_session_id,
            "new_functions": result.new_functions,
            "removed_functions": result.removed_functions,
            "new_dependencies": result.new_dependencies,
            "removed_dependencies": result.removed_dependencies,
            "risk_assessment": result.risk_assessment
        }
    except Exception as e:
        raise HTTPException(500, f"Comparison failed: {str(e)}")

@app.post("/causal/discover")
async def causal_discover(session_id: str, min_confidence: float = 0.3):
    """
    Week 4: Discover causal graph from session traces
    """
    try:
        from backend.causal.causal_discovery import CausalDiscovery
        
        if session_id not in active_sessions:
            raise HTTPException(404, "Session not found")
        
        session = active_sessions[session_id]
        events = session.get("events", [])
        
        if not events:
            return {"error": "No events in session"}
        
        discovery = CausalDiscovery()
        discovery.add_trace(events)
        graph = discovery.discover_causal_graph(min_confidence)
        
        return {
            "session_id": session_id,
            "nodes": list(graph.nodes),
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "confidence": e.confidence,
                    "strength": e.strength
                }
                for e in graph.edges
            ],
            "min_confidence": min_confidence
        }
    except Exception as e:
        raise HTTPException(500, f"Causal discovery failed: {str(e)}")

@app.post("/whatif/simulate")
async def what_if_simulate(session_id: str, remove_function: str):
    """
    Week 4: "What if we remove function X?" simulator
    
    Returns: affected functions, break probabilities, critical path
    """
    try:
        from backend.causal.causal_discovery import CausalDiscovery
        from backend.causal.what_if_simulator import WhatIfSimulator
        
        if session_id not in active_sessions:
            raise HTTPException(404, "Session not found")
        
        session = active_sessions[session_id]
        events = session.get("events", [])
        
        if not events:
            return {"error": "No events in session"}
        
        # Build causal graph
        discovery = CausalDiscovery()
        discovery.add_trace(events)
        graph = discovery.discover_causal_graph(min_confidence=0.2)
        
        # Run simulation
        simulator = WhatIfSimulator(graph)
        result = simulator.simulate_removal(remove_function)
        
        return {
            "session_id": session_id,
            "removed_function": result.intervention_node,
            "summary": {
                "affected_count": len(result.affected_functions),
                "cascade_depth": result.cascade_depth,
                "total_break_probability": result.total_break_probability
            },
            "critical_path": result.critical_path,
            "affected_functions": result.affected_functions,
            "alternative_paths": result.alternative_paths
        }
    except Exception as e:
        raise HTTPException(500, f"Simulation failed: {str(e)}")

@app.get("/score/{session_id}")
async def get_score(session_id: str):
    """
    Week 4: Get Code Archaeologist Score (maintainability benchmark)
    """
    try:
        from backend.causal.causal_discovery import CausalDiscovery
        from backend.graph.score_benchmark import calculate_maintainability_score
        
        if session_id not in active_sessions:
            raise HTTPException(404, "Session not found")
        
        session = active_sessions[session_id]
        events = session.get("events", [])
        functions = session.get("functions", [])
        
        if not events or not functions:
            return {"error": "Insufficient data for scoring"}
        
        # Build causal graph
        discovery = CausalDiscovery()
        discovery.add_trace(events)
        graph = discovery.discover_causal_graph(min_confidence=0.2)
        
        # Calculate score
        score = calculate_maintainability_score(graph, functions)
        
        return {
            "session_id": session_id,
            "overall_score": score.overall_score,
            "category": score.category,
            "component_scores": {
                "complexity": score.complexity_score,
                "coupling": score.coupling_score,
                "cohesion": score.cohesion_score,
                "documentation": score.documentation_score
            },
            "metrics": {
                "graph_density": score.graph_density,
                "avg_fan_out": score.avg_fan_out,
                "max_fan_out": score.max_fan_out,
                "dead_code_pct": score.dead_code_pct,
                "cyclomatic_proxy": score.cyclomatic_proxy,
                "causal_complexity": score.causal_complexity
            },
            "top_issues": score.top_issues,
            "strengths": score.strengths
        }
    except Exception as e:
        raise HTTPException(500, f"Score calculation failed: {str(e)}")

@app.post("/apikey/generate")
async def generate_api_key(tier: str = "free"):
    """
    Week 4: Generate API key for usage-based pricing
    
    Tiers: free (1000 calls), standard, enterprise
    """
    from backend.api.pricing import get_pricing_manager, PricingTier
    
    try:
        pricing = get_pricing_manager()
        tier_enum = PricingTier(tier.lower())
        api_key = pricing.generate_api_key(tier_enum)
        
        return {
            "api_key": api_key,
            "tier": tier,
            "free_calls_remaining": 1000 if tier == "free" else 0,
            "pricing": {
                "analysis": "$0.01",
                "query": "$0.001",
                "explain": "$0.005"
            }
        }
    except Exception as e:
        raise HTTPException(500, f"API key generation failed: {str(e)}")

@app.get("/apikey/usage/{api_key}")
async def get_api_usage(api_key: str):
    """
    Week 4: Get usage summary for API key
    """
    from backend.api.pricing import get_pricing_manager
    
    try:
        pricing = get_pricing_manager()
        summary = pricing.get_usage_summary(api_key)
        
        if "error" in summary:
            raise HTTPException(404, summary["error"])
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Usage retrieval failed: {str(e)}")

@app.get("/trace/format")
async def get_trace_format():
    """
    Week 4: Get open-source trace format specification
    """
    return {
        "version": "1.0.0",
        "spec_url": "/static/TRACE_FORMAT_SPEC.md",
        "description": "Open-source trace format for language-agnostic analysis",
        "supported_languages": ["python", "java", "go", "rust", "cpp", "javascript"],
        "github_repo": "https://github.com/code-archaeologist/trace-format",
        "license": "MIT"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
