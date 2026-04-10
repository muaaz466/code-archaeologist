import argparse
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.tracer.python_tracer import trace_python_file
from backend.tracer.cpp_tracer import trace_cpp_binary
from backend.graph.builder import build_graph
from backend.graph.queries import list_functions


def get_tracer_for_file(source_path: str):
    if source_path.endswith('.py'):
        return trace_python_file
    elif source_path.endswith('.cpp'):
        return trace_cpp_binary
    else:
        raise ValueError(f"Unsupported file type: {source_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Code Archaeologist CLI")
    parser.add_argument("source", type=Path, help="Python or C++ source file to analyze")
    parser.add_argument("--list-functions", action="store_true", help="List functions detected in the trace graph")
    args = parser.parse_args()

    source_path = str(args.source.resolve())
    tracer = get_tracer_for_file(source_path)
    events = tracer(source_path)
    if source_path.endswith('.py'):
        graph = build_graph(events)
        print(f"Traced {len(events)} execution events")
        print(f"Graph nodes: {graph.number_of_nodes()}, edges: {graph.number_of_edges()}")

        if args.list_functions:
            functions = list_functions(graph)
            print("Detected functions:")
            for func in functions:
                print(f"- {func}")
    else:
        print("C++ tracing: compiled and ran binary, but no events traced yet.")


if __name__ == "__main__":
    main()
