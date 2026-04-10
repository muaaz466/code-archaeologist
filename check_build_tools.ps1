# Check if Visual Studio Build Tools is installed
Write-Host "Checking for C++ compiler..." -ForegroundColor Cyan

# Check for cl.exe (MSVC)
$cl = Get-Command cl.exe -ErrorAction SilentlyContinue
if ($cl) {
    Write-Host "[OK] MSVC (cl.exe) found at: $($cl.Source)" -ForegroundColor Green
    & cl.exe 2>&1 | Select-String "Microsoft" | Select-Object -First 1
} else {
    Write-Host "[MISSING] MSVC (cl.exe) not found" -ForegroundColor Red
}

# Check for g++ (MinGW)
$gpp = Get-Command g++.exe -ErrorAction SilentlyContinue
if ($gpp) {
    Write-Host "[OK] MinGW (g++) found at: $($gpp.Source)" -ForegroundColor Green
    & g++.exe --version | Select-Object -First 1
} else {
    Write-Host "[MISSING] MinGW (g++) not found" -ForegroundColor Red
}

# Check existing DLLs
Write-Host "`nChecking existing DLLs..." -ForegroundColor Cyan

$graphDll = "backend\graph\fast_graph.dll"
$tracerDll = "backend\tracer\cpp_tracer.dll"

if (Test-Path $graphDll) {
    $size = (Get-Item $graphDll).Length / 1KB
    $sizeFormatted = "{0:N1}" -f $size
    Write-Host "[OK] fast_graph.dll found ($sizeFormatted KB)" -ForegroundColor Green
} else {
    Write-Host "[MISSING] fast_graph.dll not found" -ForegroundColor Red
}

if (Test-Path $tracerDll) {
    $size = (Get-Item $tracerDll).Length / 1KB
    $sizeFormatted = "{0:N1}" -f $size
    Write-Host "[OK] cpp_tracer.dll found ($sizeFormatted KB)" -ForegroundColor Green
} else {
    Write-Host "[MISSING] cpp_tracer.dll not found" -ForegroundColor Red
}

# Recommendations
Write-Host "`n========================================" -ForegroundColor Yellow
if (-not $cl -and -not $gpp) {
    Write-Host "ACTION REQUIRED:" -ForegroundColor Red
    Write-Host "Install Visual Studio Build Tools:" -ForegroundColor White
    Write-Host "1. Download: https://visualstudio.microsoft.com/downloads/" -ForegroundColor Cyan
    Write-Host "2. Run installer, select 'Desktop development with C++'" -ForegroundColor Cyan
    Write-Host "3. Open 'Developer Command Prompt for VS'" -ForegroundColor Cyan
    Write-Host "4. Run: cd backend\graph && build_cpp.bat" -ForegroundColor Cyan
    Write-Host "5. Run: cd backend\tracer && build_cpp_tracer.bat" -ForegroundColor Cyan
} else {
    Write-Host "Compilers found! Ready to build." -ForegroundColor Green
    Write-Host "Run these commands in Developer Command Prompt:" -ForegroundColor White
    Write-Host "  cd backend\graph && build_cpp.bat" -ForegroundColor Cyan
    Write-Host "  cd backend\tracer && build_cpp_tracer.bat" -ForegroundColor Cyan
}
Write-Host "========================================" -ForegroundColor Yellow
