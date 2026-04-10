# Code Archaeologist

AI-powered code intelligence for legacy Python systems. This repository includes a prototype backend, Streamlit UI, CLI, and Docker sandbox for analyzing Python execution traces.

## Performance

The system includes optional C++ acceleration for both graph operations and AST analysis. When C++ extensions are compiled, the system provides significant performance improvements for large codebases.

### Available C++ Accelerations

1. **Fast Graph Operations** (`backend/graph/`): High-performance graph algorithms using C++ STL
2. **Fast AST Analysis** (`backend/tracer/`): Optimized variable analysis using C++ AST processing

### Building C++ Extensions (Optional)

```bash
# Build graph acceleration
cd backend/graph
python setup_fast_ast.py build_ext --inplace

# Build AST acceleration  
cd backend/tracer
python setup_fast_ast.py build_ext --inplace
```

If C++ compilers are not available, the system automatically falls back to Python implementations with no performance impact.

## Project Structure

- `backend/`: core tracing, graph construction, and FastAPI backend.
- `frontend/streamlit/`: Streamlit UI for uploading and exploring traces.
- `cli/`: simple command-line interface.
- `docker/`: sandbox container definition.
- `tests/`: sample code and test harness.

## Getting Started

### Install

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Run the backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Streamlit UI

```bash
streamlit run frontend/streamlit/app.py
```

### Use the CLI

```bash
python cli/codearch.py tests/sample_code.py --list-functions
```

## API Endpoints

- `POST /trace`: returns execution trace events for a Python file.
- `POST /graph`: returns graph summary for a traced file.
- `POST /query`: run named graph queries.

Example query payload:

```json
{
  "source_path": "tests/sample_code.py",
  "query_type": "callers",
  "function_name": "multiply"
}
```

## Docker

Build and run a sandbox container for the backend:

```bash
docker compose up --build
```

## Notes

This MVP supports Python dynamic tracing with optional C++ acceleration for both graph operations and AST analysis. When C++ extensions are compiled, the system provides significant performance improvements for large codebases through optimized graph algorithms and fast variable analysis. The system automatically falls back to Python implementations (NetworkX and ast module) if C++ extensions are unavailable. Graph queries include call graphs, data flows, and dead code detection. Future milestones include full multi-language tracing, causal discovery, AI documentation, and team features.
