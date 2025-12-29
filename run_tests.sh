#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip
if [ -f requirements-dev.txt ]; then
  pip install -r requirements-dev.txt
fi
pytest -q
