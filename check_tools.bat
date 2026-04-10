@echo off
echo ========================================
echo Checking C++ Build Tools
echo ========================================
echo.

where cl.exe >nul 2>nul
if %errorlevel% == 0 (
    echo [OK] MSVC (cl.exe) found
    cl.exe 2>&1 | findstr "Microsoft"
) else (
    echo [MISSING] MSVC (cl.exe) not found
)

echo.
where g++.exe >nul 2>nul
if %errorlevel% == 0 (
    echo [OK] MinGW (g++) found
) else (
    echo [MISSING] MinGW (g++) not found
)

echo.
echo ========================================
echo Checking DLLs
echo ========================================
echo.

if exist backend\graph\fast_graph.dll (
    echo [OK] fast_graph.dll found
) else (
    echo [MISSING] fast_graph.dll not found
)

if exist backend\tracer\cpp_tracer.dll (
    echo [OK] cpp_tracer.dll found
) else (
    echo [MISSING] cpp_tracer.dll not found
)

echo.
echo ========================================
if not exist backend\graph\fast_graph.dll (
    if not exist backend\tracer\cpp_tracer.dll (
        echo ACTION: Install Visual Studio Build Tools
        echo 1. Download: https://visualstudio.microsoft.com/downloads/
        echo 2. Select "Desktop development with C++"
        echo 3. Run from Developer Command Prompt:
        echo    cd backend\graph ^&^& build_cpp.bat
        echo    cd backend\tracer ^&^& build_cpp_tracer.bat
    )
)
echo ========================================
pause
