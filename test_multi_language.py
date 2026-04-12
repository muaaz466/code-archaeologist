#!/usr/bin/env python3
"""
Test multi-language tracer integration
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.tracer.python_tracer import trace_python_file
from backend.tracer.java_tracer import trace_java_file
from backend.graph.builder import build_graph
from backend.graph.queries import list_functions, get_callers, get_callees

def test_python_tracing():
    """Test Python tracer"""
    print("\n" + "="*50)
    print("🐍 Testing Python Tracer")
    print("="*50)
    
    # Create a test Python file
    test_code = '''
def greet(name):
    return f"Hello, {name}!"

def main():
    result = greet("World")
    print(result)

if __name__ == "__main__":
    main()
'''
    
    test_file = "/tmp/test_sample.py"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    events = trace_python_file(test_file)
    print(f"✅ Traced {len(events)} events")
    
    graph = build_graph(events)
    if hasattr(graph, 'number_of_nodes'):
        print(f"✅ Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    functions = list_functions(graph)
    print(f"✅ Functions: {functions}")
    
    return True

def test_java_tracing():
    """Test Java tracer stub"""
    print("\n" + "="*50)
    print("☕ Testing Java Tracer (stub)")
    print("="*50)
    
    # Java tracer is stub - just verify it exists
    try:
        from backend.tracer.java_tracer import JavaTracer
        tracer = JavaTracer()
        print("✅ Java tracer initialized")
        print("⚠️  Java tracing requires compiled agent (see java/CodeArchaeologistAgent.java)")
        return True
    except Exception as e:
        print(f"⚠️  Java tracer not available: {e}")
        return False

def test_graph_queries():
    """Test graph query functionality"""
    print("\n" + "="*50)
    print("📊 Testing Graph Queries")
    print("="*50)
    
    test_code = '''
def process_data(data):
    return data.upper()

def main():
    result = process_data("hello")
    print(result)

if __name__ == "__main__":
    main()
'''
    
    test_file = "/tmp/test_queries.py"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    events = trace_python_file(test_file)
    graph = build_graph(events)
    
    functions = list_functions(graph)
    print(f"✅ Functions detected: {functions}")
    
    # Test queries
    for func in functions:
        callers = get_callers(graph, func)
        callees = get_callees(graph, func)
        print(f"  • {func}:")
        print(f"    ← Callers: {callers}")
        print(f"    → Callees: {callees}")
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  Code Archaeologist - Multi-Language Tracer Tests")
    print("="*60)
    
    results = {
        "Python Tracing": test_python_tracing(),
        "Java Tracing": test_java_tracing(),
        "Graph Queries": test_graph_queries(),
    }
    
    print("\n" + "="*60)
    print("📋 Test Summary")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(results.values())
    print("\n" + ("✅ All tests passed!" if all_passed else "⚠️  Some tests failed"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
