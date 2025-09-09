#!/usr/bin/env bash
set -euo pipefail

# Setup and Run Script for Dexter v3 (macOS/Linux)
# - Installs/instructs for Docker, Node, Python
# - Sets up venv, installs deps
# - Starts backend (uvicorn) and frontend (npm run dev)
# - Opens browser to UI (if available)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info(){ echo -e "${BLUE}[INFO]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }
err(){  echo -e "${RED}[ERROR]${NC} $*"; }

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

has_cmd(){ command -v "$1" >/dev/null 2>&1; }

ensure_python(){
  if ! has_cmd python3 && ! has_cmd python; then
    warn "Python not found. Please install Python 3.11+ via your package manager."
    exit 1
  fi
}

ensure_docker(){
  if ! has_cmd docker; then
    warn "Docker CLI not found. Please install Docker Desktop (mac) or Docker Engine (Linux)."
    warn "macOS: https://docs.docker.com/desktop/install/mac/"
    warn "Linux: https://docs.docker.com/engine/install/"
  else
    if ! docker info >/dev/null 2>&1; then
      warn "Docker daemon not reachable. Start Docker Desktop or the docker service."
    fi
  fi
}

ensure_node(){
  if ! has_cmd node || ! has_cmd npm; then
    warn "Node.js/npm not found. Install Node.js LTS (e.g., via nvm or your package manager)."
    warn "nvm: https://github.com/nvm-sh/nvm"
  fi
}

setup_venv_install(){
  info "Creating Python venv (.venv) and installing requirements..."
  if has_cmd python3; then PY=python3; else PY=python; fi
  [ -d .venv ] || $PY -m venv .venv
  . ./.venv/bin/activate
  python -m pip install --upgrade pip
  if [ -f requirements.txt ]; then
    info "Installing requirements.txt..."
    pip install -r requirements.txt
  fi
}

install_frontend_deps(){
  if [ -d frontend ]; then
    if has_cmd npm; then
      info "Installing frontend dependencies..."
      (cd frontend && npm install)
    else
      warn "npm not found; skipping frontend dependency install."
    fi
  else
    warn "frontend directory not found."
  fi
}

start_backend(){
  info "Starting backend (uvicorn on 127.0.0.1:8080) in background..."
  (./.venv/bin/python serve_backend.py) &
  echo $! > .backend.pid
}

start_frontend(){
  if [ -d frontend ] && has_cmd npm; then
    info "Starting frontend (npm run dev) in background..."
    (cd frontend && npm run dev) &
    echo $! > .frontend.pid
  fi
}

open_browser(){
  URL="http://localhost:3000"
  info "Opening browser at $URL"
  if has_cmd xdg-open; then xdg-open "$URL" >/dev/null 2>&1 || true; fi
  if has_cmd open; then open "$URL" >/dev/null 2>&1 || true; fi
}

# --- main ---
info "Repo root: $REPO_ROOT"
ensure_python
ensure_docker
ensure_node
setup_venv_install
install_frontend_deps
start_backend
start_frontend
open_browser
info "Done. Use kill $(cat .backend.pid) / $(cat .frontend.pid) to stop processes if needed."
