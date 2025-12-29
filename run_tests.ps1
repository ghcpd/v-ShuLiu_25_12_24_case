#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt -r requirements-dev.txt
pytest -q --maxfail=1
