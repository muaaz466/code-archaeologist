from pydantic import BaseModel


class TraceEvent(BaseModel):
    id: str
    event: str
    function: str
    filename: str
    lineno: int
    code: str
    reads: list[str] = []
    writes: list[str] = []
    parent: str | None = None
    language: str = "python"


class TraceRequest(BaseModel):
    source_path: str


class GraphRequest(BaseModel):
    source_path: str
    query_type: str | None = None
    function_name: str | None = None
    variable_name: str | None = None
    source_variable: str | None = None
    target_variable: str | None = None


class GraphSummary(BaseModel):
    nodes: int
    edges: int


class QueryResult(BaseModel):
    query: str
    result: list[str]
    summary: GraphSummary
