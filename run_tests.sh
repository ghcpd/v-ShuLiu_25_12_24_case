#!/bin/bash
# run_tests.sh - One-click test runner

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run performance test
python perf_test.py

# Deactivate
deactivate