@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\e3402020\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe"

echo ========================================================
echo [Bloomberg Terminal] Syncing Live Market Data...
echo ========================================================
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%SCRIPT_DIR%sync_remote_excel.py"
    "%PYTHON_EXE%" "%SCRIPT_DIR%generate_web_dashboard.py"
) else (
    python "%SCRIPT_DIR%sync_remote_excel.py"
    python "%SCRIPT_DIR%generate_web_dashboard.py"
)

echo.
echo [Bloomberg Terminal] Opening Web Dashboard...
start "" "%SCRIPT_DIR%index.html"
exit /b 0
