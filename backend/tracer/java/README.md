# Code Archaeologist - Java Tracer

Week 3: Java ByteBuddy agent for method call tracing.

## Overview

The Java tracer uses ByteBuddy to instrument Java bytecode at runtime, capturing:
- Method entry/exit events
- Call graph structure
- Execution timestamps
- Thread information

## Building

Requires: Maven 3.6+ and Java 11+

```bash
cd backend/tracer/java
mvn clean package
```

Output: `target/java-tracer-3.0.0.jar`

## Usage

### As Java Agent

```bash
java -javaagent:java-tracer-3.0.0.jar=output=trace.json,package=com.yourapp -jar your-app.jar
```

Options:
- `output=<file>`: Output JSON file (default: java_trace.json)
- `package=<prefix>`: Only trace classes in this package

### From Python/FastAPI

```python
from backend.tracer.java_tracer import trace_java_application

# Trace a Java JAR
events = trace_java_application(
    jar_path="app.jar",
    agent_path="java-tracer-3.0.0.jar",
    output_file="trace.json",
    package_filter="com.yourapp"
)

# Send to C++ engine
graph = build_graph_from_events(events)
```

## Output Format

The tracer outputs JSON matching the Unified Trace Format:

```json
{
  "language": "java",
  "version": "3.0.0",
  "week": 3,
  "event_count": 150,
  "events": [
    {
      "id": "uuid",
      "event": "call",
      "function": "com.example.Service.process",
      "filename": "com/example/Service.java",
      "lineno": 0,
      "code": "(arg1, arg2)",
      "language": "java",
      "thread_id": 1,
      "timestamp_ns": 1234567890
    }
  ]
}
```

## Architecture

```
Java Application
    ↓ (instrumented by)
ByteBuddy Agent
    ↓ (captures)
Method Call Events
    ↓ (converts to)
Unified Trace Format (JSON)
    ↓ (sent to)
Python/FastAPI → C++ Engine → Graph
```

## Week 3 Integration

The Java tracer integrates with the Code Archaeologist system:

1. **FastAPI** receives Java upload
2. **Java agent** attaches to running process
3. **JSON output** sent to Python
4. **C++ engine** builds call graph
5. **AI analysis** explains functions
6. **PDF export** generates report

## Limitations

- Line numbers require debug symbols (`-g` flag)
- Variable tracking requires JVMTI (advanced)
- Reflection calls may not be fully captured

## License

MIT License - Code Archaeologist Project
