#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt -r requirements-dev.txt
pytest -q --maxfail=1
