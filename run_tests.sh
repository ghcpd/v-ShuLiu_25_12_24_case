#!/bin/bash
# Test runner for Linux/macOS
# Creates environment, installs dependencies, and runs test suite

set -e  # Exit on first error

echo "============================================================"
echo "Advanced TODO System - Test Runner (Unix/Linux/macOS)"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "[1/4] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

echo ""
echo "[2/4] Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -q -r requirements-dev.txt

echo ""
echo "[3/4] Running test suite..."
python -m pytest tests/test_advanced_todo.py -v --tb=short

echo ""
echo "[4/4] Running performance tests..."
python perf_test.py

echo ""
echo "============================================================"
echo "All tests completed successfully!"
echo "============================================================"
