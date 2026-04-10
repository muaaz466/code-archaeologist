# Building C++ DLLs for Code Archaeologist

## Overview
You need to build 2 C++ DLLs:
1. **fast_graph.dll** - High-performance graph operations (backend/graph/)
2. **cpp_tracer.dll** - Windows Debug API tracer (backend/tracer/)

## Prerequisites

### Option 1: Visual Studio Build Tools (Recommended)

1. **Download**: https://visualstudio.microsoft.com/downloads/
2. Scroll down to **"Tools for Visual Studio"**
3. Download **"Build Tools for Visual Studio 2022"**
4. Run the installer
5. Select **"Desktop development with C++"** workload
6. Install (requires ~8GB disk space)

### Option 2: MinGW-w64 (Alternative)

1. **Download**: https://www.mingw-w64.org/downloads/
2. Or use MSYS2: https://www.msys2.org/
3. Install and add to PATH

## Build Steps

### Step 1: Open Developer Command Prompt

After installing VS Build Tools:

1. Press `Win` key
2. Type **"Developer Command Prompt"**
3. Run as **Administrator**
4. Navigate to project:
```cmd
cd c:\Users\HP\Documents\code-archaeologist
```

### Step 2: Build Graph Engine DLL

```cmd
cd backend\graph
build_cpp.bat
```

Expected output:
```
Building fast_graph.dll...
Using MSVC (cl.exe)...
Microsoft (R) C/C++ Optimizing Compiler Version ...
...
Build completed successfully!
fast_graph.dll
```

### Step 3: Build C++ Tracer DLL

```cmd
cd ..\tracer
build_cpp_tracer.bat
```

Expected output:
```
Building C++ Tracer (Windows Debug API)...
Using MSVC (cl.exe)...
...
Build successful!
DLL location: cpp_tracer.dll
```

### Step 4: Verify

Check both DLLs exist:
```cmd
cd ..\..
dir backend\graph\fast_graph.dll
dir backend\tracer\cpp_tracer.dll
```

## Testing

Run Python test:
```python
python -c "
import sys
sys.path.insert(0, '.')
from backend.graph.fast_graph_wrapper import FastGraphWrapper
w = FastGraphWrapper()
print('Graph DLL loaded:', w.is_available())
"
```

For tracer:
```python
python -c "
import sys
sys.path.insert(0, '.')
from backend.tracer.cpp_tracer_wrapper import CppTracerWrapper
t = CppTracerWrapper()
print('Tracer DLL loaded:', t.is_available())
"
```

## Troubleshooting

### "cl.exe not found"
- Run from **Developer Command Prompt**, not regular cmd
- Or run `vcvarsall.bat x64` first

### "dbghelp.lib not found"
- Install Windows SDK via VS Build Tools
- Or add `/link /LIBPATH:"C:\Program Files (x86)\Windows Kits\10\Lib\..."`

### DLL load errors
- Check architecture: `cl.exe` builds x86 by default, use `cl /arch:AVX2` or `cl /favor:AMD64`
- Install Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Missing headers
- Install Windows SDK through VS Build Tools installer

## Alternative: Manual Build Commands

If batch files fail, run manually from Developer Command Prompt:

### Graph DLL:
```cmd
cd backend\graph
cl /LD /EHsc /std:c++17 fast_graph.cpp /link /out:fast_graph.dll
```

### Tracer DLL:
```cmd
cd backend\tracer
cl /LD /EHsc /std:c++17 fast_ast.cpp /link /out:cpp_tracer.dll dbghelp.lib kernel32.lib
```

## Next Steps

After building DLLs:
1. Restart Streamlit: `python -m streamlit run frontend/streamlit/app.py`
2. Test with C++ file upload
3. Verify performance boost in graph operations
