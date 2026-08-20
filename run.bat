@echo off
setlocal enabledelayedexpansion

title S K E W C T L — Data Skew Intelligence Engine

set PYTHON=.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    set PYTHON=python
)

"%PYTHON%" run.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Pipeline execution exited with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)
