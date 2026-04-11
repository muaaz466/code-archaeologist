"""
Code Archaeologist - Java Tracer Integration
Week 3: Python glue for Java ByteBuddy agent
"""

import subprocess
import json
import os
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Optional
import shutil


class JavaTraceEvent:
    """Java trace event matching unified format"""
    
    def __init__(self, data: Dict):
        self.id = data.get('id', '')
        self.event = data.get('event', '')
        self.function = data.get('function', '')
        self.filename = data.get('filename', '')
        self.lineno = data.get('lineno', 0)
        self.code = data.get('code', '')
        self.language = data.get('language', 'java')
        self.thread_id = data.get('thread_id', 0)
        self.timestamp_ns = data.get('timestamp_ns', 0)
        self.reads = data.get('reads', [])
        self.writes = data.get('writes', [])


def find_java_agent() -> Optional[str]:
    """Find the Java tracer agent JAR"""
    # Check common locations
    possible_paths = [
        'backend/tracer/java/target/java-tracer-3.0.0.jar',
        'backend/tracer/java-tracer-3.0.0.jar',
        'java-tracer-3.0.0.jar',
        '../tracer/java/target/java-tracer-3.0.0.jar',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None


def trace_java_file(
    jar_path: str,
    agent_path: Optional[str] = None,
    output_file: Optional[str] = None,
    package_filter: Optional[str] = None,
    timeout: int = 60
) -> List[JavaTraceEvent]:
    """
    Trace a Java JAR file using the ByteBuddy agent
    
    Args:
        jar_path: Path to the Java JAR to trace
        agent_path: Path to java-tracer agent JAR (auto-detected if None)
        output_file: Where to save trace JSON
        package_filter: Only trace classes in this package
        timeout: Maximum seconds to run
        
    Returns:
        List of JavaTraceEvent objects
    """
    # Find agent if not specified
    if agent_path is None:
        agent_path = find_java_agent()
        if agent_path is None:
            raise FileNotFoundError(
                "Java tracer agent not found. Build with: "
                "cd backend/tracer/java && mvn clean package"
            )
    
    if not os.path.exists(agent_path):
        raise FileNotFoundError(f"Agent not found: {agent_path}")
    
    if not os.path.exists(jar_path):
        raise FileNotFoundError(f"JAR not found: {jar_path}")
    
    # Create temp output file if not specified
    if output_file is None:
        output_file = tempfile.mktemp(suffix='.json', prefix='java_trace_')
    else:
        output_file = os.path.abspath(output_file)
    
    # Build agent arguments
    agent_args = f"output={output_file}"
    if package_filter:
        agent_args += f",package={package_filter}"
    
    # Build Java command
    cmd = [
        'java',
        f'-javaagent:{agent_path}={agent_args}',
        '-jar',
        jar_path
    ]
    
    print(f"🔍 Tracing Java application: {jar_path}")
    print(f"   Agent: {agent_path}")
    print(f"   Output: {output_file}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        # Run Java application with agent
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        print(f"   Exit code: {result.returncode}")
        
        if result.returncode != 0 and result.returncode != 143:  # 143 = SIGTERM
            print(f"⚠️ Java process exited with code {result.returncode}")
            if result.stderr:
                print(f"   stderr: {result.stderr[:500]}")
        
        # Wait a moment for trace to be written
        time.sleep(0.5)
        
        # Read trace output
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                trace_data = json.load(f)
            
            events = [
                JavaTraceEvent(e) 
                for e in trace_data.get('events', [])
            ]
            
            print(f"✅ Captured {len(events)} Java events")
            return events
        else:
            print("⚠️ No trace output file generated")
            return []
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout after {timeout}s")
        return []
    except Exception as e:
        print(f"❌ Error tracing Java: {e}")
        return []
    finally:
        # Cleanup temp file
        if output_file and output_file.startswith(tempfile.gettempdir()):
            try:
                os.unlink(output_file)
            except:
                pass


def trace_java_project(
    project_path: str,
    main_class: str,
    agent_path: Optional[str] = None,
    output_file: Optional[str] = None,
    package_filter: Optional[str] = None,
    classpath: Optional[List[str]] = None
) -> List[JavaTraceEvent]:
    """
    Trace a Java project (not packaged as JAR)
    
    Args:
        project_path: Path to compiled .class files
        main_class: Fully qualified main class name (e.g., "com.example.Main")
        agent_path: Path to tracer agent
        output_file: Trace output file
        package_filter: Package to trace
        classpath: Additional classpath entries
    """
    # Find agent
    if agent_path is None:
        agent_path = find_java_agent()
        if agent_path is None:
            raise FileNotFoundError("Java tracer agent not found")
    
    # Create temp output file
    if output_file is None:
        output_file = tempfile.mktemp(suffix='.json', prefix='java_trace_')
    
    # Build classpath
    cp = [project_path]
    if classpath:
        cp.extend(classpath)
    
    # Build agent arguments
    agent_args = f"output={output_file}"
    if package_filter:
        agent_args += f",package={package_filter}"
    
    # Build command
    cmd = [
        'java',
        f'-javaagent:{agent_path}={agent_args}',
        '-cp', os.pathsep.join(cp),
        main_class
    ]
    
    print(f"🔍 Tracing Java project: {main_class}")
    print(f"   Project: {project_path}")
    print(f"   Output: {output_file}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        time.sleep(0.5)
        
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                trace_data = json.load(f)
            
            events = [JavaTraceEvent(e) for e in trace_data.get('events', [])]
            print(f"✅ Captured {len(events)} Java events")
            return events
        else:
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == '__main__':
    # Test
    print("Java Tracer Module - Week 3")
    print("Usage: trace_java_file('app.jar')")
    
    # Check for agent
    agent = find_java_agent()
    if agent:
        print(f"✅ Agent found: {agent}")
    else:
        print("⚠️ Agent not found. Build with Maven first.")
