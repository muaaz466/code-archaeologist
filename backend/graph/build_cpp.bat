@echo off
REM Build script for the fast C++ graph library

echo Building fast_graph.dll...

REM Try cl.exe (MSVC) first
where cl >nul 2>nul
if %errorlevel% == 0 goto msvc

REM Try g++ (MinGW)
where g++ >nul 2>nul
if %errorlevel% == 0 goto mingw

echo Error: No C++ compiler found.
echo Please install Visual Studio Build Tools or MinGW.
goto end

:msvc
echo Using MSVC (cl.exe)...
cl /LD /EHsc /std:c++17 fast_graph.cpp /link /out:fast_graph.dll
goto success

:mingw
echo Using MinGW (g++)...
g++ -shared -std=c++17 -o fast_graph.dll fast_graph.cpp
goto success

:success
echo Build completed successfully!
dir fast_graph.dll
goto end

:end