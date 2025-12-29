#!/bin/bash
# One-click test runner for todo_advanced

set -e

echo "=========================================="
echo "TODO Advanced - Test Runner"
echo "=========================================="
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements-dev.txt

# Run tests
echo ""
echo "Running test suite..."
echo ""
python3 -m pytest tests/ -v --tb=short --cov=todo_advanced --cov-report=term-missing

# Run performance tests
echo ""
echo "Running performance benchmarks..."
echo ""
python3 perf_test.py

echo ""
echo "=========================================="
echo "Test suite complete!"
echo "=========================================="
