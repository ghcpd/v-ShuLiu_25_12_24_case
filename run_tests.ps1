# run_tests.ps1 - One-click test runner for Windows

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run performance test
python perf_test.py

# Deactivate
deactivate