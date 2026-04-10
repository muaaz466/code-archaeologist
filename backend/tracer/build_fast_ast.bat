@echo off
REM Build script for the fast AST C++ extension
REM Requires Python development headers and C++ compiler

echo Building fast_ast extension...

REM Try to build with setup.py
python setup_fast_ast.py build_ext --inplace

if %errorlevel% == 0 (
    echo Build completed successfully!
    dir backend\tracer\fast_ast*.pyd
    goto end
)

echo Setup.py build failed, trying manual compilation...

REM Manual compilation with cl.exe (MSVC)
where cl >nul 2>nul
if %errorlevel% == 0 (
    echo Using MSVC (cl.exe)...
    REM This would require finding Python include paths, etc.
    REM For now, just show the command that would be used
    echo cl /LD /EHsc /std:c++17 /I"C:\Python312\include" fast_ast.cpp /link /out:fast_ast.pyd /libpath:"C:\Python312\libs"
    goto end
)

REM Manual compilation with g++ (MinGW)
where g++ >nul 2>nul
if %errorlevel% == 0 (
    echo Using MinGW (g++)...
    REM This would require finding Python include paths, etc.
    echo g++ -shared -std=c++17 -I"C:\Python312\include" fast_ast.cpp -o fast_ast.pyd -L"C:\Python312\libs" -lpython312
    goto end
)

echo Error: No suitable compiler found and setup.py build failed.
echo Please ensure you have:
echo 1. Python development headers installed
echo 2. A C++ compiler (MSVC or MinGW)
echo 3. Run: pip install setuptools wheel
goto end

:end