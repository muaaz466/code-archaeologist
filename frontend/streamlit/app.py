from __future__ import annotations

import sys
import tempfile
import threading
import zipfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import streamlit as st

# Add project root to path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.tracer.python_tracer import trace_python_file
from backend.graph.builder import build_graph, GraphType, is_fast_graph
from backend.graph.queries import (
    list_functions, 
    graph_summary, 
    get_callers, 
    get_callees, 
    get_affected,
    dead_code,
    find_paths
)
from backend.tracer.batch_tracer import (
    discover_python_files, 
    trace_folder, 
    merge_traces,
    find_cross_file_dependencies
)

st.set_page_config(
    page_title="Code Archaeologist", 
    layout="wide", 
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': 'Code Archaeologist - Legacy Code Intelligence (Week 1 MVP)'
    }
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .file-tree {
        font-family: monospace;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    .dependency-arrow {
        color: #ff4b4b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🏛️ Code Archaeologist</p>', unsafe_allow_html=True)
st.markdown("*Trace execution, build call graphs, understand legacy code*")

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'current_graph' not in st.session_state:
    st.session_state.current_graph = None
if 'current_files' not in st.session_state:
    st.session_state.current_files = None
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = None
if 'current_events' not in st.session_state:
    st.session_state.current_events = None
if 'graph' not in st.session_state:
    st.session_state.graph = None
if 'events' not in st.session_state:
    st.session_state.events = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    analysis_mode = st.radio(
        "Analysis Mode",
        ["📄 Single File", "📁 Project Folder (ZIP)"],
        help="Single File: One Python file. Project Folder: ZIP with multiple files - traces entry point and follows imports."
    )
    
    st.divider()
    
    st.header("📊 Analysis History")
    history = st.session_state.get('analysis_history', [])
    if history:
        for idx, item in enumerate(history[-5:]):
            st.text(f"{idx+1}. {item['name']} ({item['nodes']} nodes)")
    
    if st.button("Clear History"):
        st.session_state.analysis_history = []
        st.session_state.pop('current_graph', None)
        st.session_state.pop('current_files', None)
        st.rerun()

# Main content
if analysis_mode == "📄 Single File":
    st.header("Single File Analysis")
    
    uploaded_files = st.file_uploader(
        "Upload Python/C++ files", 
        type=["py", "cpp"],
        accept_multiple_files=True,
        help="Upload one or more .py/.cpp files to analyze their execution traces"
    )

    if uploaded_files:
        # Read each uploaded file once and reuse the content
        file_contents = {}
        for uploaded_file in uploaded_files:
            uploaded_file.seek(0)
            file_contents[uploaded_file.name] = uploaded_file.read().decode("utf-8").lstrip('\ufeff')
            uploaded_file.seek(0)

        # Display file list
        st.subheader("Uploaded Files")
        file_list = list(file_contents.keys())
        st.write("Files to analyze:", ", ".join(file_list))
        
        # File selection for analysis
        if len(uploaded_files) > 1:
            selected_file = st.selectbox(
                "Select main file to trace",
                options=file_list,
                help="Choose which file to start tracing from"
            )
        else:
            selected_file = file_list[0]
        
        source_code = file_contents[selected_file]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Source Code")
            with st.expander("View Code", expanded=False):
                st.code(source_code[:5000], language="python" if selected_file.endswith('.py') else "cpp")
        
        with col2:
            st.subheader("Controls")
            
            if st.button("🚀 Analyze Files", type="primary", use_container_width=True):
                with st.spinner("Tracing execution..."):
                    try:
                        # Save all files to temp directory
                        with tempfile.TemporaryDirectory() as tmpdir:
                            temp_files = []
                            for uploaded_file in uploaded_files:
                                temp_file = Path(tmpdir) / uploaded_file.name
                                temp_file.parent.mkdir(parents=True, exist_ok=True)
                                
                                file_content = file_contents[uploaded_file.name]
                                temp_file.write_text(file_content, encoding="utf-8")
                                temp_files.append(str(temp_file))
                            
                            # Find main file path
                            main_file_path = next(f for f in temp_files if Path(f).name == selected_file)
                            
                            if main_file_path.endswith('.cpp'):
                                raise ValueError("C++ file tracing is not supported in single-file mode yet.")

                            result: Dict[str, Any] = {}
                            def trace_worker():
                                try:
                                    print(f"DEBUG: Tracing {main_file_path}")
                                    events = trace_python_file(main_file_path, project_root=tmpdir)
                                    print(f"DEBUG: Got {len(events)} events")
                                    result['events'] = events
                                    result['success'] = True
                                except Exception as e:
                                    import traceback
                                    result['error'] = str(e)
                                    result['traceback'] = traceback.format_exc()
                                    result['success'] = False
                                    print(f"DEBUG: Error: {e}")

                            thread = threading.Thread(target=trace_worker, daemon=True)
                            thread.start()
                            thread.join(timeout=15)

                            if thread.is_alive():
                                raise TimeoutError("Tracing timed out after 15 seconds. Check for infinite loops or long-running code.")
                            if not result.get('success', False):
                                st.error(f"Trace error: {result.get('error')}")
                                st.code(result.get('traceback', 'No traceback'))
                                raise RuntimeError(result.get('error', 'Unknown tracing error'))

                            events = result['events']
                            print(f"DEBUG: Final events count: {len(events)}")
                            graph = build_graph(events)
                            
                            # Store results
                            st.session_state['graph'] = graph
                            st.session_state['events'] = events
                            st.session_state['current_files'] = file_list
                            st.session_state['current_mode'] = 'multiple'
                            
                            # Add to history
                            st.session_state.analysis_history.append({
                                'name': f"{len(file_list)} files ({selected_file})",
                                'nodes': graph.number_of_nodes(),
                                'mode': 'multiple'
                            })
                            
                            # Display results
                            st.success(f"✅ Traced {len(events)} events")
                            
                            metrics_cols = st.columns(3)
                            metrics_cols[0].metric("Nodes", graph.number_of_nodes())
                            metrics_cols[1].metric("Edges", graph.number_of_edges())
                            metrics_cols[2].metric("Functions", len(list_functions(graph)))
                            
                            # Store in session
                            st.session_state['current_graph'] = graph
                            st.session_state['current_files'] = file_list
                            st.session_state['current_mode'] = 'single'
                            st.session_state['current_events'] = events
                    except TimeoutError as e:
                        st.error(str(e))
                        st.info("💡 Tip: Try a smaller script or add a timeout-friendly entry path.")
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
                        st.info("💡 Tip: Make sure your main file can run independently and has proper imports.")

elif analysis_mode == "📁 Project Folder (ZIP)":
    st.header("Project Analysis")
    st.info("Upload a ZIP containing multiple Python files. We'll trace the entry point and follow imports to build a complete call graph.")
    
    uploaded_zip = st.file_uploader(
        "Upload Project ZIP", 
        type=["zip"],
        help="ZIP file containing your Python project with .py files"
    )
    
    if uploaded_zip:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save ZIP
            zip_path = Path(tmpdir) / "project.zip"
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getvalue())
            
            # Extract
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(Path(tmpdir) / "project")
            except zipfile.BadZipFile:
                st.error("❌ Invalid ZIP file")
                st.stop()
            
            project_dir = Path(tmpdir) / "project"
            py_files = discover_python_files(str(project_dir))
            
            if not py_files:
                st.warning("No Python files found in archive")
                st.stop()
            
            # Layout
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader(f"📂 Project ({len(py_files)} files)")
                
                with st.expander("Files", expanded=True):
                    for f in py_files[:20]:  # Show first 20
                        rel = Path(f).relative_to(project_dir)
                        size = Path(f).stat().st_size
                        st.text(f"📄 {rel} ({size} bytes)")
                    if len(py_files) > 20:
                        st.text(f"... and {len(py_files) - 20} more")
                
                # Auto-detect entry points
                entry_candidates = ["main.py", "app.py", "run.py", "__main__.py", "server.py"]
                detected = []
                for cand in entry_candidates:
                    matches = [f for f in py_files if Path(f).name == cand]
                    if matches:
                        detected.append(str(Path(matches[0]).relative_to(project_dir)))
                
                if detected:
                    st.success(f"Detected entry points: {', '.join(detected[:3])}")
            
            with col2:
                st.subheader("Analysis Settings")
                
                entry_options = ["Auto-detect"] + detected + ["Other (specify below)"]
                entry_choice = st.selectbox("Entry Point", entry_options)
                
                if entry_choice == "Other (specify below)":
                    entry_point = st.text_input("Specify file path", placeholder="src/main.py")
                elif entry_choice == "Auto-detect":
                    entry_point = detected[0] if detected else None
                else:
                    entry_point = entry_choice
                
                st.caption(f"Will execute: {entry_point or 'First found file'}")
                
                if st.button("🔍 Analyze Project", type="primary", use_container_width=True):
                    progress = st.progress(0, "Initializing...")
                    
                    try:
                        # Step 1: Trace
                        progress.progress(10, "Tracing entry point and imports...")
                        results = trace_folder(
                            str(project_dir), 
                            entry_point=entry_point
                        )
                        
                        if not results:
                            st.error("No events captured. Check if entry point exists and runs.")
                            st.stop()
                        
                        # Step 2: Build graph
                        progress.progress(50, "Building unified graph...")
                        
                        # Flatten all events
                        all_events = []
                        for file_path, events in results.items():
                            all_events.extend(events)
                        
                        merged_graph = build_graph(all_events)
                        
                        # Step 3: Cross-file deps
                        progress.progress(75, "Analyzing dependencies...")
                        cross_deps = find_cross_file_dependencies(str(project_dir))
                        
                        progress.progress(100, "Complete!")
                        
                        # Results
                        st.success(f"✅ Project analyzed!")
                        
                        # Key metrics
                        file_count = len(results)
                        func_count = len(list_functions(merged_graph))
                        
                        metric_cols = st.columns(4)
                        metric_cols[0].metric("Files Traced", file_count)
                        metric_cols[1].metric("Total Events", len(all_events))
                        metric_cols[2].metric("Graph Nodes", merged_graph.number_of_nodes())
                        metric_cols[3].metric("Functions", func_count)
                        
                        # Cross-file calls (from trace)
                        st.subheader("🔗 Cross-File Call Graph")
                        
                        # Group events by file to show inter-file calls
                        file_calls: Dict[str, List[str]] = {}
                        for event in all_events:
                            caller_file = event.parent.split(':')[0] if event.parent else None
                            callee_file = event.filename
                            
                            if caller_file and callee_file != caller_file:
                                if caller_file not in file_calls:
                                    file_calls[caller_file] = []
                                rel_caller = Path(caller_file).name if 'tmp' not in caller_file else 'entry'
                                rel_callee = Path(callee_file).name
                                call_desc = f"{rel_caller} → {rel_callee} : {event.function}"
                                if call_desc not in file_calls[caller_file]:
                                    file_calls[caller_file].append(call_desc)
                        
                        if file_calls:
                            with st.expander("Inter-File Calls (from execution)", expanded=True):
                                for caller, calls in list(file_calls.items())[:10]:
                                    st.markdown(f"**{Path(caller).name}** calls:")
                                    for call in calls[:5]:
                                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{call}")
                        else:
                            st.info("No cross-file calls detected in trace")
                        
                        # Static imports
                        if cross_deps:
                            with st.expander("Static Import Dependencies"):
                                for dep in cross_deps[:20]:
                                    st.markdown(
                                        f"`{dep['from']}` <span class='dependency-arrow'>→</span> "
                                        f"`{dep['to']}` *({dep['type']})*",
                                        unsafe_allow_html=True
                                    )
                        
                        # Store for queries
                        st.session_state['current_graph'] = merged_graph
                        st.session_state['current_files'] = list(results.keys())
                        st.session_state['current_mode'] = 'project'
                        st.session_state['current_events'] = all_events
                        
                        # History
                        st.session_state.analysis_history.append({
                            'name': f"Project ({len(py_files)} files)",
                            'nodes': merged_graph.number_of_nodes(),
                            'mode': 'project'
                        })
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
                        import traceback
                        with st.expander("Debug Info"):
                            st.code(traceback.format_exc())

# Query Interface (shown after analysis)
if st.session_state.get('current_graph') is not None:
    st.divider()
    st.header("🔍 Query Graph")
    
    graph = st.session_state['current_graph']
    is_project = st.session_state.get('current_mode') == 'project'
    
    query_tabs = st.tabs(["Functions", "Dependencies", "Impact Analysis", "Dead Code", "Data Flow", "Raw Data"])
    
    with query_tabs[0]:  # Functions
        funcs = list_functions(graph)
        st.write(f"**{len(funcs)} functions found:**")
        
        search = st.text_input("Search functions", "")
        filtered = [f for f in funcs if search.lower() in f.lower()] if search else funcs
        
        cols = st.columns(3)
        for idx, func in enumerate(filtered[:30]):  # Limit display
            cols[idx % 3].text(f"⚡ {func}")
        if len(filtered) > 30:
            st.text(f"... and {len(filtered) - 30} more")
    
    with query_tabs[1]:  # Dependencies
        funcs = list_functions(graph)
        target = st.selectbox("Select function to analyze", funcs, key="dep_func")
        
        if target:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("← Callers (who calls this)")
                callers = get_callers(graph, target)
                if callers:
                    for c in callers:
                        st.success(f"• {c}")
                else:
                    st.info("No callers found (entry point or uncalled)")
            
            with col2:
                st.subheader("→ Callees (what this calls)")
                callees = get_callees(graph, target)
                if callees:
                    for c in callees:
                        st.info(f"• {c}")
                else:
                    st.info("No callees (leaf function)")
    
    with query_tabs[2]:  # Impact Analysis
        funcs = list_functions(graph)
        target = st.selectbox("Select function to change", funcs, key="impact_func")
        
        if target:
            affected = get_affected(graph, target)
            if affected:
                st.warning(f"⚠️ Changing '{target}' may break these {len(affected)} downstream functions:")
                for aff in affected[:20]:
                    st.error(f"💥 {aff}")
                if len(affected) > 20:
                    st.error(f"... and {len(affected) - 20} more")
            else:
                st.success(f"✅ Safe to change - '{target}' affects no other functions")
    
    with query_tabs[3]:  # Dead Code
        st.subheader("🪦 Potentially Unused Functions")
        
        # Try to get source path from events
        source_path = None
        if 'current_events' in st.session_state and st.session_state['current_events']:
            first = st.session_state['current_events'][0]
            source_path = first.filename if hasattr(first, 'filename') else None
        
        dead_funcs = dead_code(graph, source_path or "unknown")
        
        if dead_funcs:
            st.error(f"Found {len(dead_funcs)} functions that may be unused:")
            for d in dead_funcs:
                st.text(f"• {d}")
            st.info("Note: These may be called dynamically or be library functions")
        else:
            st.success("All functions appear to be called")
    
    with query_tabs[4]:  # Data Flow (Week 2)
        st.subheader("🌊 Data Flow Analysis")
        st.caption("Week 2 Feature: Track variable reads and writes across functions")
        
        # Get events from session to extract variables
        events = st.session_state.get('current_events', [])
        
        # Debug: Show first event structure
        if events and st.checkbox("Debug: Show first event structure"):
            first_event = events[0]
            st.write(f"Event type: {type(first_event)}")
            if hasattr(first_event, '__dict__'):
                st.json(first_event.__dict__)
            elif isinstance(first_event, dict):
                st.json(first_event)
            else:
                st.write(str(first_event))
        
        # Debug: Show all events with reads/writes
        if events and st.checkbox("Debug: Show events with variables"):
            var_events = [e for e in events if (hasattr(e, 'reads') and e.reads) or (hasattr(e, 'writes') and e.writes)]
            st.write(f"Found {len(var_events)} events with variables out of {len(events)} total")
            for e in var_events[:10]:
                st.write(f"Line {e.lineno}: {e.code}")
                st.write(f"  reads={e.reads}, writes={e.writes}")
        
        # Debug: Show ALL events to verify data structure
        if events and st.checkbox("Debug: Show ALL events"):
            st.write(f"Total events: {len(events)}")
            for i, e in enumerate(events[:5]):
                st.write(f"Event {i}: Line {e.lineno if hasattr(e, 'lineno') else 'N/A'}")
                st.write(f"  function={e.function if hasattr(e, 'function') else 'N/A'}")
                st.write(f"  reads={e.reads if hasattr(e, 'reads') else 'N/A'}")
                st.write(f"  writes={e.writes if hasattr(e, 'writes') else 'N/A'}")
        
        # Extract all variables from events
        all_variables = set()
        for e in events:
            if hasattr(e, 'reads') and e.reads:
                all_variables.update(e.reads)
            if hasattr(e, 'writes') and e.writes:
                all_variables.update(e.writes)
        
        if all_variables:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔵 Variable Writers** - Functions that WRITE to variables")
                var_write = st.selectbox("Select variable", sorted(all_variables), key="var_write")
                
                # Search in events for writers
                writers = set()
                for e in events:
                    if hasattr(e, 'writes') and e.writes and var_write in e.writes:
                        writers.add(e.function)
                if writers:
                    for func in writers:
                        st.markdown(f"� `{func}`")
                else:
                    st.info(f"No functions write to '{var_write}'")
            
            with col2:
                st.markdown("**🟠 Variable Readers** - Functions that READ from variables")
                var_read = st.selectbox("Select variable", sorted(all_variables), key="var_read")
                
                # Search in events for readers
                readers = set()
                for e in events:
                    if hasattr(e, 'reads') and e.reads and var_read in e.reads:
                        readers.add(e.function)
                if readers:
                    for func in readers:
                        st.markdown(f"🔵 `{func}`")
                else:
                    st.info(f"No functions read from '{var_read}'")
            
            # Data Flow Path
            st.divider()
            st.subheader("🔗 Data Flow Path")
            col3, col4 = st.columns(2)
            with col3:
                start_var = st.selectbox("From variable (source)", sorted(all_variables), key="start_var")
            with col4:
                end_var = st.selectbox("To variable (destination)", sorted(all_variables), key="end_var")
            
            if st.button("Find Data Flow Path", type="primary"):
                # Find all functions that touch the variables
                start_writers = set()
                start_readers = set()
                end_writers = set()
                end_readers = set()
                
                for e in events:
                    if hasattr(e, 'writes') and e.writes:
                        if start_var in e.writes:
                            start_writers.add(e.function)
                        if end_var in e.writes:
                            end_writers.add(e.function)
                    if hasattr(e, 'reads') and e.reads:
                        if start_var in e.reads:
                            start_readers.add(e.function)
                        if end_var in e.reads:
                            end_readers.add(e.function)
                
                # Use C++ graph if available
                if hasattr(graph, 'find_data_path') and start_var and end_var:
                    try:
                        paths = graph.find_data_path(start_var, end_var)
                        if paths:
                            st.success(f"Found {len(paths)} data flow path(s):")
                            for p in paths:
                                st.write(f"  → {p}")
                    except Exception as e:
                        st.write(f"C++ path query error: {e}")
                
                # Check for direct data flow (same function writes start and reads end)
                direct_flow = start_writers & end_readers
                
                if direct_flow:
                    st.success(f"✅ Direct data flow found: `{start_var}` → {direct_flow} → `{end_var}`")
                elif start_writers and end_readers:
                    st.info(f"📊 Data flow analysis:")
                    st.markdown(f"**`{start_var}`** is written by: {start_writers}")
                    st.markdown(f"**`{end_var}`** is read by: {end_readers}")
                    
                    # Check for intermediate connection
                    intermediate = start_readers & end_writers
                    if intermediate:
                        st.success(f"✅ Multi-hop flow: `{start_var}` → {intermediate} → `{end_var}`")
                    else:
                        st.warning(f"⚠️ No direct connection found")
                else:
                    st.warning(f"❌ No data flow path found from '{start_var}' to '{end_var}'")
        else:
            st.info("No variables detected in the trace. Try tracing code with variable assignments.")
            st.markdown("""
            **Example code to trace:**
            ```python
            def process():
                x = 1      # write x
                y = x + 2  # read x, write y
                return y   # read y
            ```
            """)
    
    with query_tabs[5]:  # Raw Data
        if st.checkbox("Show graph summary"):
            st.json(graph_summary(graph))
        
        if st.checkbox("Show file list") and 'current_files' in st.session_state:
            st.json(st.session_state['current_files'])
st.divider()
footer_cols = st.columns([1, 1, 1])
footer_cols[0].caption("Code Archaeologist MVP")
footer_cols[1].caption("Week 1: Python Analysis")
history_count = len(st.session_state.get('analysis_history', []))
footer_cols[2].caption(f"Session: {history_count} analyses")