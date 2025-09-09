#!/usr/bin/env python3
"""Set up and launch Dexter backend and frontend.

This script installs Python and Node dependencies and runs the
FastAPI backend alongside the React frontend.  It mirrors the
functionality of the PowerShell helper but works cross-platform.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def run(cmd, cwd=None):
    info("Running: " + " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)


def ensure_python_deps() -> Path:
    """Create venv and install backend requirements.  Returns path to venv python."""
    if not VENV_DIR.exists():
        info("Creating virtual environment (.venv)...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    python = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    pip = VENV_DIR / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
    run([str(pip), "install", "--upgrade", "pip"])
    req = PROJECT_ROOT / "requirements.txt"
    if req.exists():
        run([str(pip), "install", "-r", str(req)])
    else:
        warn("requirements.txt not found; skipping backend dependency installation")
    return python


def ensure_node_deps() -> bool:
    """Install frontend dependencies if npm is available."""
    if shutil.which("npm") is None:
        warn("npm is not installed; frontend will not be started")
        return False
    run(["npm", "install"], cwd=str(FRONTEND_DIR))
    return True


def start_backend(python: Path) -> subprocess.Popen:
    cmd = [str(python), "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
    return subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))


def start_frontend() -> subprocess.Popen | None:
    if shutil.which("npm") is None:
        return None
    return subprocess.Popen(["npm", "run", "dev"], cwd=str(FRONTEND_DIR))


def main() -> None:
    python = ensure_python_deps()
    have_frontend = ensure_node_deps()
    procs = [start_backend(python)]
    if have_frontend:
        procs.append(start_frontend())
        info("Backend running on http://127.0.0.1:8080")
        info("Frontend running on http://127.0.0.1:5173")
    try:
        while True:
            time.sleep(1)
            for p in procs:
                if p.poll() is not None:
                    raise SystemExit("A process exited")
    except KeyboardInterrupt:
        info("Shutting down...")
    finally:
        for p in procs:
            if p and p.poll() is None:
                p.terminate()


if __name__ == "__main__":
    main()
