@echo off
title Transport Department System
cd /d "%~dp0"

if exist "python_runtime\python.exe" (
    "python_runtime\python.exe" run.py
) else if exist "backend\venv\Scripts\python.exe" (
    "backend\venv\Scripts\python.exe" run.py
) else (
    python run.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while starting the application.
    pause
)
