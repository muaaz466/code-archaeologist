# Building the C++ Binary Tracer

The C++ tracer uses Windows Debug API (DbgHelp) to trace function calls in compiled binaries.

## Prerequisites

- Windows OS
- Visual Studio with C++ workload (for cl.exe)
- OR MinGW-w64 (for g++)

## Build Steps

### Option 1: Using Visual Studio (Recommended)

1. Open **"Developer Command Prompt for VS"** (find it in Start Menu)

2. Navigate to the tracer directory:
   ```cmd
   cd c:\Users\HP\Documents\code-archaeologist\backend\tracer
   ```

3. Run the build script:
   ```cmd
   build_cpp_tracer.bat
   ```

4. This creates `cpp_tracer.dll` in the same directory

### Option 2: Manual Build

If the batch file doesn't work:

```cmd
cd backend\tracer
cl.exe /LD /EHsc /std:c++17 fast_ast.cpp /link /OUT:cpp_tracer.dll dbghelp.lib kernel32.lib
```

## Verification

After building, verify the DLL exists:
```cmd
dir backend\tracer\cpp_tracer.dll
```

## Usage

Once built, the tracer automatically uses the C++ DLL:

```python
from backend.tracer import trace_cpp_binary

events = trace_cpp_binary("path/to/file.cpp")
for event in events:
    print(f"{event.parent} -> {event.function}")
```

## How It Works

1. **Compile**: C++ source is compiled to executable with debug symbols
2. **Debug**: The C++ tracer creates the target process in debug mode
3. **Trace**: Uses Windows Debug API to capture function entry/exit
4. **Convert**: Raw events converted to TraceEvent objects
5. **Return**: Standard format compatible with Python tracer

## Architecture

```
Python (cpp_tracer.py)
    ↓
Python Wrapper (cpp_tracer_wrapper.py) - ctypes
    ↓
C++ DLL (cpp_tracer.dll) - Windows Debug API
    ↓
Target Binary (your .cpp compiled)
```

## Fallback Behavior

If the C++ DLL is not available, the system falls back to:
- Compiling and running the binary
- Returning empty trace (can't trace without debug API)
- Clear warning message

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "C++ tracer DLL not found" | Build the DLL using steps above |
| "cl.exe not found" | Run from Developer Command Prompt |
| "Failed to create process" | Check binary path, may need admin rights |
| Empty trace events | Binary needs debug symbols (compile with /Zi or -g) |
| Permission denied | Run IDE/terminal as Administrator |

## Linux/macOS Support

The current implementation is Windows-only due to DbgHelp dependency.
For Linux/macOS, alternative implementations using:
- `ptrace` system call
- `gdb` batch mode
- `lldb` scripting

Would need to be developed separately.
