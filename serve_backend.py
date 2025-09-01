#!/usr/bin/env python3
"""
Convenience launcher for the FastAPI backend.

Run from repo root:
  python serve_backend.py

This avoids ModuleNotFoundError by ensuring the repo root is on sys.path
and delegates to uvicorn programmatically.
"""
import os
import sys
import uvicorn

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8080, reload=True)

if __name__ == "__main__":
    main()
