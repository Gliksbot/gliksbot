from __future__ import annotations
import json, os, time
from pathlib import Path
from typing import Optional, Dict, Any
from .io import append_jsonl


def _load_config() -> dict:
    try:
        return json.load(open('config.json','r',encoding='utf-8'))
    except Exception:
        return {}


def _collab_dir() -> Path:
    # Priority: env -> config.collaboration_dir -> default
    env_dir = os.environ.get('DEXTER_COLLAB')
    if env_dir:
        return Path(env_dir)
    cfg = _load_config()
    cfg_dir = cfg.get('collaboration_dir')
    if cfg_dir:
        return Path(cfg_dir)
    return Path('backend/collaboration')


def slot_file(slot: str, session_id: Optional[str] = None) -> Path:
    d = _collab_dir() / slot
    d.mkdir(parents=True, exist_ok=True)
    sid = session_id or 'dev_seed'
    return d / f"{sid}.jsonl"


def write(slot: str, obj: Dict[str, Any], session_id: Optional[str] = None) -> Path:
    obj.setdefault('ts', time.time())
    obj.setdefault('slot', slot)
    p = slot_file(slot, session_id=session_id)
    append_jsonl(str(p), obj)
    return p


def write_text(slot: str, text: str, event: str = 'note', session_id: Optional[str] = None, **extra) -> Path:
    obj = {'event': event, 'text': text}
    if extra:
        obj.update(extra)
    return write(slot, obj, session_id=session_id)

