@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo [Dallas College Bloomberg Trading Challenge]
echo SYNCING LATEST TERMINAL QUOTES FROM GITHUB...
echo ========================================================

git pull origin main

echo.
echo Opening latest updated dashboard in your browser...
start "" "%~dp0index.html"
exit /b 0
