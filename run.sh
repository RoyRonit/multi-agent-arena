#!/usr/bin/env bash
# One-command local dev: backend on :8000, frontend on :5173 (proxied).
set -euo pipefail
cd "$(dirname "$0")"

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  if [[ -f .env ]]; then
    set -a; source .env; set +a
  fi
fi
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "ERROR: OPENROUTER_API_KEY not set. Copy .env.example -> .env and add your key." >&2
  exit 1
fi

# Python venv
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  ./.venv/bin/pip install -q -r requirements.txt
fi

# Frontend deps
if [[ ! -d frontend/node_modules ]]; then
  (cd frontend && npm install)
fi

echo "→ backend  http://localhost:8000"
echo "→ frontend http://localhost:5173"
./.venv/bin/uvicorn backend.main:app --port 8000 --reload &
BACK=$!
trap 'kill $BACK 2>/dev/null || true' EXIT
(cd frontend && npm run dev)
