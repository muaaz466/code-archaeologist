@echo off
echo Building C++ Tracer (Windows Debug API) - Week 2...

REM Check for Visual Studio compiler
where cl >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Visual Studio C++ compiler (cl.exe) not found!
    echo Please run this from "Developer Command Prompt for VS"
    pause
    exit /b 1
)

echo.
echo Building Week 2 C++ Binary Tracer with DbgHelp API...
echo.

REM Compile the tracer DLL
cl.exe /LD /EHsc /std:c++17 ^
    /I"C:\Python312\include" ^
    cpp_tracer.cpp ^
    /link /OUT:cpp_tracer.dll ^
    /LIBPATH:"C:\Python312\libs" ^
    dbghelp.lib kernel32.lib

if %errorlevel% == 0 (
    echo.
    echo =========================================
    echo Build successful! (Week 2 Complete)
    echo =========================================
    echo DLL location: backend\tracer\cpp_tracer.dll
    echo Features:
    echo   - Windows Debug API integration
    echo   - Symbol resolution with DbgHelp
    echo   - Binary process debugging
    echo   - Week 2 Data Flow tracing
    echo =========================================
) else (
    echo Build failed!
)

pause