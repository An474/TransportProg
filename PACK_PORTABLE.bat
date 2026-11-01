@echo off
title Packaging Portable Distribution
cd /d "%~dp0"

echo ========================================================
echo   Creating portable zip distribution...
echo ========================================================
echo.

if exist "python_runtime\python.exe" (
    "python_runtime\python.exe" pack_for_mom.py
) else (
    python pack_for_mom.py
)

echo.
pause
