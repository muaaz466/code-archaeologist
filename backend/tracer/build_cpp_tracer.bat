@echo off
echo Building C++ Tracer (Windows Debug API)...

REM Check for Visual Studio compiler
where cl >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Visual Studio C++ compiler (cl.exe) not found!
    echo Please run this from "Developer Command Prompt for VS"
    pause
    exit /b 1
)

REM Compile the tracer DLL
cl.exe /LD /EHsc /std:c++17 ^
    /I"C:\Python312\include" ^
    fast_ast.cpp ^
    /link /OUT:cpp_tracer.dll ^
    /LIBPATH:"C:\Python312\libs" ^
    dbghelp.lib kernel32.lib

if %errorlevel% == 0 (
    echo Build successful!
    echo DLL location: backend\tracer\cpp_tracer.dll
) else (
    echo Build failed!
)

pause