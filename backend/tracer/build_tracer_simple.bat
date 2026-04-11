@echo off
echo Building C++ Tracer (Windows Debug API)...
echo.

REM Compile the tracer DLL
cl.exe /LD /EHsc /std:c++17 /O2 ^
    /I"C:\Python312\include" ^
    fast_ast.cpp ^
    /link /OUT:cpp_tracer.dll ^
    /LIBPATH:"C:\Python312\libs" ^
    dbghelp.lib kernel32.lib

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo Build successful!
    echo DLL: cpp_tracer.dll
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
)

pause
