#!/usr/bin/env bash
set -euo pipefail
export OMEGA_LOGLEVEL=INFO

if [ -d venv ]; then
  source venv/bin/activate || true
fi

echo "🔎 Running smoke tests..."
pytest -q -m smoke

echo "🚀 Running main dry-run..."
python3 main.py --dry-run --limit 5

echo "✅ CI local OK"


