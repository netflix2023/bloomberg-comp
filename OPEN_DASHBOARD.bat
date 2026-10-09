@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\e3402020\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe"

echo [Bloomberg Dashboard] Launching localhost terminal server...
if exist "%PYTHON_EXE%" (
    start "" /b "%PYTHON_EXE%" "%SCRIPT_DIR%server.py" --open
) else (
    start "" /b python "%SCRIPT_DIR%server.py" --open
)
exit /b 0
