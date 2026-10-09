@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\e3402020\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe"

echo ========================================================
echo [Dallas College Bloomberg Trading Challenge]
echo SYNC TERMINAL DATA & BROADCAST TO TEAM
echo ========================================================

echo.
echo [1/4] Pulling live market quotes from Bloomberg API...
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%SCRIPT_DIR%sync_remote_excel.py"
    "%PYTHON_EXE%" "%SCRIPT_DIR%generate_web_dashboard.py"
) else (
    python "%SCRIPT_DIR%sync_remote_excel.py"
    python "%SCRIPT_DIR%generate_web_dashboard.py"
)

echo.
echo [2/4] Staging updated market snapshot for Git...
cd /d "%SCRIPT_DIR%"
git add bloomberg_live_remote_dashboard.xlsx bloomberg_live_remote_screener.csv index.html dashboard.html generate_web_dashboard.py sync_remote_excel.py .gitignore

echo.
echo [3/4] Pushing updates to GitHub (so your friend's dashboard updates)...
git commit -m "Live market sync from Bloomberg terminal: %date% %time%"
git push origin main

echo.
echo [4/4] Opening updated dashboard in your browser...
start "" "%SCRIPT_DIR%index.html"

echo.
echo ========================================================
echo SUCCESS! Your dashboard and your friend's feed are synced.
echo ========================================================
exit /b 0
