@echo off
REM Test runner for Windows PowerShell
REM Creates environment, installs dependencies, and runs test suite

setlocal enabledelayedexpansion

echo ============================================================
echo Advanced TODO System - Test Runner (Windows)
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo [1/4] Creating virtual environment...
if not exist "venv\" (
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        exit /b 1
    )
) else (
    echo Virtual environment already exists
)

echo.
echo [2/4] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -q -r requirements-dev.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    exit /b 1
)

echo.
echo [3/4] Running test suite...
python -m pytest tests\test_advanced_todo.py -v --tb=short
if errorlevel 1 (
    echo.
    echo Error: Some tests failed
    exit /b 1
)

echo.
echo [4/4] Running performance tests...
python perf_test.py

echo.
echo ============================================================
echo All tests completed successfully!
echo ============================================================

exit /b 0
