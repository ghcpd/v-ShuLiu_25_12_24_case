# PowerShell one-click test runner
Set-StrictMode -Version Latest
python -m pip install --upgrade pip
if (Test-Path requirements-dev.txt) { pip install -r requirements-dev.txt }
pytest -q
