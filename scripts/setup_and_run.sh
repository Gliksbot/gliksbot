#!/usr/bin/env bash
set -euo pipefail

# Dexter v3 Setup and Run (macOS/Linux)
# Starts backend on 127.0.0.1:8080 and frontend on 3000

BLUE='\033[0;34m'; YELLOW='\033[0;33m'; NC='\033[0m'
info(){ echo -e "${BLUE}[INFO]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

has(){ command -v "$1" >/dev/null 2>&1; }

if ! has python3 && ! has python; then
  warn "Python 3.11+ not found. Install and re-run."; exit 1
fi
if ! has docker; then
  warn "Docker not found. Install Docker Desktop/Engine."
fi
if ! has node || ! has npm; then
  warn "Node.js/npm not found. Install Node.js LTS (e.g., via nvm)."
fi

# Python venv + deps
info "Creating venv and installing requirements..."
PY=$(command -v python3 || command -v python)
[ -d .venv ] || "$PY" -m venv .venv
. ./.venv/bin/activate
python -m pip install --upgrade pip
[ -f requirements.txt ] && pip install -r requirements.txt || true

# Frontend deps
if [ -d frontend ] && has npm; then
  info "Installing frontend deps..."
  (cd frontend && npm install)
fi

# Start backend (127.0.0.1:8080)
info "Starting backend..."
(./.venv/bin/python serve_backend.py) & echo $! > .backend.pid

# Start frontend (3000)
if [ -d frontend ] && has npm; then
  info "Starting frontend..."
  (cd frontend && npm run dev) & echo $! > .frontend.pid
fi

# Open browser
URL="http://localhost:3000"
info "Opening ${URL}"
if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" || true; fi
if command -v open >/dev/null 2>&1; then open "$URL" || true; fi

info "Backend PID: $(cat .backend.pid 2>/dev/null || echo 'n/a'), Frontend PID: $(cat .frontend.pid 2>/dev/null || echo 'n/a')"

