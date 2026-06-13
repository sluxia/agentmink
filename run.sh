#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
