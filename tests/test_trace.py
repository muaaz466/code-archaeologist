from pathlib import Path

from backend.tracer.python_tracer import trace_python_file
from backend.graph.builder import build_graph
from backend.graph.queries import (
    list_functions,
    get_callers,
    get_callees,
    get_affected,
    dead_code,
    writes_to,
    reads_from,
    data_paths,
)


def test_trace_and_graph(tmp_path: Path):
    sample = tmp_path / "sample.py"
    sample.write_text(
        """def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


def main():
    x = add(2, 3)
    y = multiply(x, 7)
    print(f\"Result: {y}\")


if __name__ == '__main__':
    main()
"""
    )

    events = trace_python_file(str(sample))
    assert events

    graph = build_graph(events)
    assert "main" in list_functions(graph)
    assert "add" in get_callees(graph, "main")
    assert "multiply" in get_callees(graph, "main") or "multiply" in get_affected(graph, "main")
    assert writes_to(graph, "x") == ["main"]
    assert reads_from(graph, "y") == ["main"]
    assert data_paths(graph, "x", "y") == [["x", "main", "y"]]
    assert dead_code(graph, str(sample)) == []
