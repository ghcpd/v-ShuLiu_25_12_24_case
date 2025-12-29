@echo off
REM One-click test runner for todo_advanced (Windows PowerShell)

echo ==========================================
echo TODO Advanced - Test Runner (Windows)
echo ==========================================
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements-dev.txt

REM Run tests
echo.
echo Running test suite...
echo.
python -m pytest tests\ -v --tb=short --cov=todo_advanced --cov-report=term-missing

REM Run performance tests
echo.
echo Running performance benchmarks...
echo.
python perf_test.py

echo.
echo ==========================================
echo Test suite complete!
echo ==========================================
pause
