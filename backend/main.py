from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.core.models import GraphRequest, GraphSummary, QueryResult
from backend.tracer.python_tracer import trace_python_file
from backend.tracer.cpp_tracer import trace_cpp_binary
from backend.graph.builder import build_graph
from backend.graph.queries import (
    list_functions,
    get_callers,
    get_callees,
    find_paths,
    get_affected,
    dead_code,
    writes_to,
    reads_from,
    data_paths,
    graph_summary,
)
from backend.auth.router import router as auth_router
from backend.auth.dependencies import require_auth, check_analysis_limit
from backend.auth.models import User

app = FastAPI(title="Code Archaeologist Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)


def get_tracer_for_file(source_path: str):
    if source_path.endswith('.py'):
        return trace_python_file
    elif source_path.endswith('.cpp'):
        return trace_cpp_binary
    else:
        raise ValueError(f"Unsupported file type: {source_path}")


@app.post("/trace")
async def trace_source(
    request: GraphRequest,
    user: User = Depends(check_analysis_limit)
):
    """
    Trace a source file (requires authentication)
    """
    try:
        tracer = get_tracer_for_file(request.source_path)
        result = tracer(request.source_path)
        
        # Track usage (increment in background)
        await _increment_analysis_count(user.id)
        
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


async def _increment_analysis_count(user_id: str):
    """Increment user's analysis count (background task)"""
    try:
        from backend.auth.supabase_client import get_supabase_admin
        admin = get_supabase_admin()
        
        # Get current count
        response = admin.table("profiles").select("analyses_used").eq("id", user_id).single().execute()
        if response.data:
            current = response.data.get("analyses_used", 0)
            admin.table("profiles").update({"analyses_used": current + 1}).eq("id", user_id).execute()
    except:
        pass  # Don't fail the request if tracking fails


@app.post("/graph")
async def create_graph(
    request: GraphRequest,
    user: User = Depends(require_auth)
):
    """
    Build graph from source file (requires authentication)
    """
    try:
        tracer = get_tracer_for_file(request.source_path)
        if request.source_path.endswith('.py'):
            events = tracer(request.source_path)
            graph = build_graph(events)
            return GraphSummary(nodes=graph.number_of_nodes(), edges=graph.number_of_edges())
        else:
            # For C++, return placeholder
            return GraphSummary(nodes=0, edges=0)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/query")
async def query_graph(
    request: GraphRequest,
    user: User = Depends(require_auth)
):
    """
    Run graph query (requires authentication)
    """
    try:
        tracer = get_tracer_for_file(request.source_path)
        if request.source_path.endswith('.py'):
            events = tracer(request.source_path)
            graph = build_graph(events)
            query_type = (request.query_type or "summary").lower()
            if query_type == "functions":
                result = list_functions(graph)
            elif query_type == "callers":
                result = get_callers(graph, request.function_name or "")
            elif query_type == "callees":
                result = get_callees(graph, request.function_name or "")
            elif query_type == "paths":
                result = [" -> ".join(path) for path in find_paths(graph, request.source_node or "", request.target_node or "")]
            elif query_type == "affected":
                result = get_affected(graph, request.function_name or "")
            elif query_type == "writes_to":
                result = writes_to(graph, request.variable_name or "")
            elif query_type == "reads_from":
                result = reads_from(graph, request.variable_name or "")
            elif query_type == "data_path":
                result = [" -> ".join(path) for path in data_paths(graph, request.source_variable or "", request.target_variable or "")]
            elif query_type == "dead_code":
                result = dead_code(graph, request.source_path)
            else:
                result = []

            return QueryResult(
                query=query_type,
                result=result,
                summary=graph_summary(graph),
            )
        else:
            # For C++, return placeholder
            return QueryResult(
                query="summary",
                result=["C++ tracing not yet implemented"],
                summary=GraphSummary(nodes=0, edges=0),
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/")
async def root():
    """API root - public endpoint"""
    return {
        "name": "Code Archaeologist API",
        "version": "0.1.0",
        "auth_required": True,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check - public endpoint"""
    return {"status": "healthy", "service": "code-archaeologist"}
