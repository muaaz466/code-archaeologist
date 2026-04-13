#!/usr/bin/env python3
"""
Code Archaeologist CLI
A command-line tool for analyzing code structure and dependencies.
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Optional

# Add project root to path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.tracer.python_tracer import trace_python_file
from backend.tracer.cpp_tracer import trace_cpp_binary
from backend.tracer.batch_tracer import BatchTracer
from backend.graph.builder import build_graph
from backend.graph.queries import list_functions, get_callers, get_callees
from backend.causal.causal_discovery import CausalDiscovery
from backend.graph.score_benchmark import ScoreBenchmark


def get_tracer_for_file(source_path: str):
    """Get appropriate tracer for file type."""
    if source_path.endswith('.py'):
        return trace_python_file
    elif source_path.endswith(('.cpp', '.cc', '.c')):
        return trace_cpp_binary
    else:
        raise ValueError(f"Unsupported file type: {source_path}")


def cmd_analyze(args):
    """Analyze a single file."""
    source_path = str(args.source.resolve())
    print(f"🔍 Analyzing: {source_path}")
    
    try:
        tracer = get_tracer_for_file(source_path)
        events = tracer(source_path)
        
        if source_path.endswith('.py'):
            graph = build_graph(events)
            print(f"✅ Traced {len(events)} execution events")
            print(f"📊 Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
            
            if args.list_functions:
                functions = list_functions(graph)
                print("\n📋 Detected functions:")
                for func in functions:
                    print(f"  • {func}")
            
            if args.query:
                target = args.query
                callers = get_callers(graph, target)
                callees = get_callees(graph, target)
                print(f"\n🔍 Query results for '{target}':")
                print(f"  ← Callers: {callers if callers else 'None'}")
                print(f"  → Callees: {callees if callees else 'None'}")
            
            if args.score:
                benchmark = ScoreBenchmark()
                functions = list_functions(graph)
                score = benchmark.calculate_score(graph, functions)
                print(f"\n📈 Code Score: {score.overall_score}/100 ({score.category})")
        else:
            print(f"⚠️ C++ tracing limited: {len(events)} events")
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_batch(args):
    """Batch analyze a directory or ZIP file."""
    source = args.source
    
    if zipfile.is_zipfile(source):
        print(f"📦 Analyzing ZIP: {source}")
    else:
        print(f"📂 Analyzing directory: {source}")
    
    try:
        tracer = BatchTracer()
        result = tracer.analyze_batch(str(source))
        
        print(f"\n📊 Batch Analysis Results:")
        print(f"  Files analyzed: {result.files_analyzed}")
        print(f"  Total events: {result.total_events}")
        print(f"  Functions found: {len(result.functions_found)}")
        print(f"  Languages: {', '.join(result.languages)}")
        
        if result.session_id and args.save:
            output = Path(args.save) if args.save else Path(f"analysis_{result.session_id}.json")
            with open(output, 'w') as f:
                json.dump({
                    'session_id': result.session_id,
                    'files_analyzed': result.files_analyzed,
                    'total_events': result.total_events,
                    'functions_found': result.functions_found,
                    'languages': result.languages,
                    'processing_time_ms': result.processing_time_ms
                }, f, indent=2)
            print(f"💾 Results saved to: {output}")
        
        print(f"\n🔗 Session ID: {result.session_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_query(args):
    """Query an existing session."""
    session_id = args.session_id
    query_type = args.type
    target = args.target
    
    print(f"🔍 Querying session {session_id}")
    print(f"   {query_type}: {target}")
    
    try:
        from backend.api.batch_analysis import get_batch_analyzer
        
        analyzer = get_batch_analyzer()
        session = analyzer._load_session(session_id)
        
        if not session:
            print(f"❌ Session not found: {session_id}", file=sys.stderr)
            sys.exit(1)
        
        graph = session.get('graph')
        
        if query_type == 'callers':
            result = get_callers(graph, target)
            print(f"\n← Functions that call '{target}':")
            for caller in result or []:
                print(f"  • {caller}")
        elif query_type == 'callees':
            result = get_callees(graph, target)
            print(f"\n→ Functions called by '{target}':")
            for callee in result or []:
                print(f"  • {callee}")
        elif query_type == 'score':
            functions = session.get('functions', [])
            discovery = CausalDiscovery()
            events = session.get('events', [])
            discovery.add_trace(events)
            causal_graph = discovery.discover_causal_graph()
            benchmark = ScoreBenchmark()
            score = benchmark.calculate_score(causal_graph, functions)
            print(f"\n📈 Code Score: {score.overall_score}/100 ({score.category})")
            print(f"   Complexity: {score.complexity_score}/100")
            print(f"   Coupling: {score.coupling_score}/100")
            print(f"   Cohesion: {score.cohesion_score}/100")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_export(args):
    """Export session to PDF."""
    session_id = args.session_id
    output = Path(args.output) if args.output else Path(f"report_{session_id}.pdf")
    
    print(f"📄 Exporting session {session_id} to PDF...")
    
    try:
        from backend.api.pdf_export import PDFReportGenerator
        from backend.api.batch_analysis import get_batch_analyzer
        
        analyzer = get_batch_analyzer()
        session = analyzer._load_session(session_id)
        
        if not session:
            print(f"❌ Session not found: {session_id}", file=sys.stderr)
            sys.exit(1)
        
        generator = PDFReportGenerator(str(output))
        
        graph_data = {
            'function_count': len(session.get('functions', [])),
            'node_count': len(session.get('graph', {}).get('nodes', [])),
            'edge_count': len(session.get('graph', {}).get('edges', [])),
            'languages': session.get('languages', ['python']),
            'functions': session.get('functions', [])
        }
        
        generator.generate_report(
            project_name=f"Analysis {session_id}",
            graph_data=graph_data,
            query_results=session.get('query_results', {}),
            ai_explanations=session.get('ai_explanations', [])
        )
        
        print(f"✅ PDF saved: {output}")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Code Archaeologist - Analyze code structure and dependencies",
        prog='code-archaeologist'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a single file')
    analyze_parser.add_argument('source', type=Path, help='Source file to analyze')
    analyze_parser.add_argument('-f', '--list-functions', action='store_true',
                                help='List all detected functions')
    analyze_parser.add_argument('-q', '--query', type=str,
                                help='Query function (show callers/callees)')
    analyze_parser.add_argument('-s', '--score', action='store_true',
                                help='Calculate code maintainability score')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch analyze directory or ZIP')
    batch_parser.add_argument('source', type=Path, help='Directory or ZIP file')
    batch_parser.add_argument('-o', '--save', type=str,
                             help='Save results to JSON file')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query existing session')
    query_parser.add_argument('session_id', help='Session ID to query')
    query_parser.add_argument('-t', '--type', choices=['callers', 'callees', 'score'],
                            default='callers', help='Query type')
    query_parser.add_argument('target', help='Function name to query')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export session to PDF')
    export_parser.add_argument('session_id', help='Session ID to export')
    export_parser.add_argument('-o', '--output', help='Output PDF file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Dispatch to command handlers
    commands = {
        'analyze': cmd_analyze,
        'batch': cmd_batch,
        'query': cmd_query,
        'export': cmd_export,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()

