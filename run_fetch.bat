@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\e3402020\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe"

echo [Bloomberg Data Fetcher] Running data extraction pipeline...
"%PYTHON_EXE%" "%SCRIPT_DIR%bloomberg_fetch.py" %*
pause
