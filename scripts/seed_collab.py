#!/usr/bin/env python3
"""
Seed per-slot collaboration JSONL files with a sample line so the UI shows data.
Usage: python scripts/seed_collab.py [--session-id SEED]
"""
import argparse, json, time
from pathlib import Path

def load_cfg():
    try:
        return json.load(open('config.json','r',encoding='utf-8'))
    except Exception:
        return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session-id', default='seed')
    args = ap.parse_args()
    cfg = load_cfg()
    slots = cfg.get('slots') or [
        'dexter','analyst','engineer','researcher','creative','validator','specialist1','specialist2'
    ]
    collab_dir = Path(cfg.get('collaboration_dir','backend/collaboration'))
    collab_dir.mkdir(parents=True, exist_ok=True)
    for slot in slots:
        d = collab_dir / slot
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{args.session_id}.jsonl"
        line = json.dumps({
            'ts': time.time(),
            'slot': slot,
            'event': 'seed',
            'text': f"[{slot}] Collaboration initialized — {time.strftime('%Y-%m-%d %H:%M:%S')}"
        }, ensure_ascii=False)
        with open(p, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
        print(f"wrote: {p}")

if __name__ == '__main__':
    main()
