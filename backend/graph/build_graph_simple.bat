@echo off
echo Building fast_graph.dll...
echo.

REM Compile the graph DLL
cl.exe /LD /EHsc /std:c++17 /O2 /favor:INTEL64 ^
    fast_graph.cpp ^
    /link /OUT:fast_graph.dll

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo Build successful!
    echo DLL: fast_graph.dll
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
)

pause
