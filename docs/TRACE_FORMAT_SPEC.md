# Code Archaeologist Trace Format Specification

**Version:** 1.0.0  
**Status:** Open Source  
**License:** MIT

## Overview

This document defines the Code Archaeologist trace format - a standardized JSON format for code execution traces. Any tracer implementation that produces this format can interface with the C++ analysis engine.

## Goals

1. **Language Agnostic:** Works with Python, Java, Go, Rust, C++, and any language
2. **Extensible:** Easy to add language-specific metadata
3. **Compact:** Efficient storage and transmission
4. **Tool Friendly:** Easy to generate and parse

## Format Specification

### Top-Level Structure

```json
{
  "version": "1.0.0",
  "trace_id": "uuid-string",
  "timestamp": "2024-01-15T10:30:00Z",
  "source_language": "python",
  "entry_point": "main.py",
  "events": [...],
  "metadata": {...}
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Format version (semantic versioning) |
| `trace_id` | string | Unique identifier for this trace |
| `timestamp` | string | ISO 8601 timestamp when trace was generated |
| `source_language` | string | Source language: `python`, `java`, `go`, `rust`, `cpp`, `javascript`, etc. |
| `events` | array | List of trace events (see Event Structure) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `entry_point` | string | Main entry point file/module |
| `metadata` | object | Additional tool-specific metadata |
| `system_info` | object | OS, architecture, runtime version |

### Event Structure

Each event represents a point of interest during execution:

```json
{
  "id": "unique-event-id",
  "type": "call|return|variable|exception",
  "function": "function_name",
  "timestamp": 1234567890.123,
  "file": "/path/to/file.py",
  "line": 42,
  "column": 10,
  "parent": "parent-function-id",
  "data": {...}
}
```

### Event Fields

#### Required

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique event identifier |
| `type` | string | Event type: `call`, `return`, `variable`, `exception`, `entry`, `exit` |
| `function` | string | Function/method name |
| `timestamp` | number | Unix timestamp with microseconds |

#### Optional

| Field | Type | Description |
|-------|------|-------------|
| `file` | string | Source file path |
| `line` | integer | Line number in source |
| `column` | integer | Column number in source |
| `parent` | string | ID of calling function's event |
| `data` | object | Event-specific data (see below) |

### Event Types

#### `call` - Function Call

```json
{
  "id": "call_001",
  "type": "call",
  "function": "process_data",
  "timestamp": 1234567890.123,
  "file": "main.py",
  "line": 42,
  "parent": "call_000",
  "data": {
    "args": ["arg1", "arg2"],
    "arg_types": ["str", "int"]
  }
}
```

#### `return` - Function Return

```json
{
  "id": "ret_001",
  "type": "return",
  "function": "process_data",
  "timestamp": 1234567890.456,
  "parent": "call_001",
  "data": {
    "value": "result",
    "type": "str"
  }
}
```

#### `variable` - Variable Access

```json
{
  "id": "var_001",
  "type": "variable",
  "function": "process_data",
  "timestamp": 1234567890.200,
  "line": 45,
  "data": {
    "name": "user_input",
    "operation": "read|write",
    "type": "str",
    "value_hash": "sha256:abc123..."
  }
}
```

#### `exception` - Exception Thrown

```json
{
  "id": "exc_001",
  "type": "exception",
  "function": "process_data",
  "timestamp": 1234567890.500,
  "line": 50,
  "data": {
    "exception_type": "ValueError",
    "message": "Invalid input",
    "stack_trace": [...]
  }
}
```

### Data Flow Events

For data flow analysis:

```json
{
  "id": "flow_001",
  "type": "data_flow",
  "timestamp": 1234567890.300,
  "data": {
    "source": "var_001",
    "sink": "var_002",
    "flow_type": "assignment|argument|return"
  }
}
```

### Causal Events

For causal discovery:

```json
{
  "id": "cause_001",
  "type": "causal",
  "timestamp": 1234567890.400,
  "data": {
    "cause": "call_001",
    "effect": "call_002",
    "confidence": 0.85,
    "evidence": "temporal_sequence"
  }
}
```

## Language-Specific Extensions

### Python

```json
{
  "source_language": "python",
  "metadata": {
    "python_version": "3.11.0",
    "interpreter": "CPython"
  },
  "events": [{
    "data": {
      "qualname": "module.submodule.function",
      "locals": [...],
      "globals": [...]
    }
  }]
}
```

### Java

```json
{
  "source_language": "java",
  "metadata": {
    "java_version": "17",
    "jvm": "OpenJDK"
  },
  "events": [{
    "data": {
      "class": "com.example.MyClass",
      "method": "methodName",
      "signature": "(Ljava/lang/String;)V",
      "is_static": false
    }
  }]
}
```

### Go

```json
{
  "source_language": "go",
  "metadata": {
    "go_version": "1.21"
  },
  "events": [{
    "data": {
      "package": "main",
      "goroutine_id": 5
    }
  }]
}
```

### Rust

```json
{
  "source_language": "rust",
  "metadata": {
    "rustc_version": "1.75.0"
  },
  "events": [{
    "data": {
      "crate": "my_crate",
      "async": false
    }
  }]
}
```

## C++ Engine Integration

The C++ engine expects traces in this format:

```cpp
// C++ struct mapping
struct TraceEvent {
    std::string id;
    std::string type;
    std::string function;
    double timestamp;
    std::optional<std::string> file;
    std::optional<int> line;
    std::optional<std::string> parent;
    json data;
};
```

## Example Complete Trace

```json
{
  "version": "1.0.0",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:00Z",
  "source_language": "python",
  "entry_point": "main.py",
  "system_info": {
    "os": "Linux",
    "arch": "x86_64",
    "hostname": "dev-machine"
  },
  "events": [
    {
      "id": "evt_001",
      "type": "call",
      "function": "main",
      "timestamp": 1705314600.000,
      "file": "main.py",
      "line": 1
    },
    {
      "id": "evt_002",
      "type": "call",
      "function": "process_data",
      "timestamp": 1705314600.100,
      "file": "main.py",
      "line": 5,
      "parent": "evt_001",
      "data": {
        "args": ["input.txt"]
      }
    },
    {
      "id": "evt_003",
      "type": "variable",
      "function": "process_data",
      "timestamp": 1705314600.150,
      "line": 10,
      "data": {
        "name": "data",
        "operation": "write"
      }
    },
    {
      "id": "evt_004",
      "type": "return",
      "function": "process_data",
      "timestamp": 1705314600.300,
      "parent": "evt_002",
      "data": {
        "value": 42
      }
    },
    {
      "id": "evt_005",
      "type": "return",
      "function": "main",
      "timestamp": 1705314600.400,
      "parent": "evt_001"
    }
  ],
  "metadata": {
    "tracer": "code-archaeologist-python",
    "tracer_version": "1.0.0"
  }
}
```

## Tooling

### Validation

Use the provided JSON Schema for validation:

```bash
# Validate trace file
python -m jsonschema -i trace.json trace_format_schema.json
```

### Conversion

Utilities provided for converting from other formats:

- `convert_pdb.py` - Windows PDB to trace format
- `convert_dwarf.py` - DWARF debug info to trace format
- `convert_jvm.py` - JVM TI to trace format

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial release |

## Contributing

Contributions welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md)

## License

MIT License - See [LICENSE](../LICENSE)
