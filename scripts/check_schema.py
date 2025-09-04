#!/usr/bin/env python3
"""
Quick schema check for Dexter DB. Ensures core tables exist and prints simple stats.
Usage: python scripts/check_schema.py
"""
from pathlib import Path
import json
import sqlite3
import time


def load_cfg():
    try:
        import sys
        import os
        # Add backend to path to access utils
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        backend_dir = os.path.join(project_root, 'backend')
        sys.path.insert(0, backend_dir)
        
        from dexter_brain.utils import get_config_path
        return json.load(open(get_config_path(),'r',encoding='utf-8'))
    except Exception:
        return {}


def ensure_core(db_path: str):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    # Ensure minimal skills table exists
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            code TEXT,
            created_ts REAL NOT NULL,
            updated_ts REAL NOT NULL,
            version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'draft',
            test_results TEXT,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            tags TEXT
        )
        """
    )
    con.commit()
    return con


def main():
    cfg = load_cfg()
    db_path = cfg.get('runtime',{}).get('db_path', './dexter.db')
    print(f"[schema-check] Using DB: {db_path}")
    con = ensure_core(db_path)
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print("[schema-check] Tables:", ', '.join(tables))
    # skills columns
    cols = con.execute("PRAGMA table_info(skills)").fetchall()
    print("[schema-check] skills columns:", [c[1] for c in cols])
    # simple counts
    try:
        total_skills = con.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    except Exception:
        total_skills = 'n/a'
    print("[schema-check] skills count:", total_skills)
    con.close()


if __name__ == '__main__':
    main()

