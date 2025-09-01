from __future__ import annotations
import os, json
from pathlib import Path
from collections import deque
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

COLLAB_DIR = Path(os.environ.get('DEXTER_COLLAB','backend/collaboration'))
router = APIRouter(prefix='/collaboration', tags=['collaboration'])

@router.get('/head')
def head(slot: str = Query(...), n: int = Query(1, ge=1, le=500)):
    slot_dir = COLLAB_DIR / slot
    if not slot_dir.exists():
        return {"source":"real","items":[]}
    files = sorted(slot_dir.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return {"source":"real","items":[]}
    path = files[0]
    dq = deque(maxlen=n)
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if s:
                dq.append(s)
    items = []
    for s in dq:
        try:
            items.append(json.loads(s))
        except Exception:
            pass
    return {"source":"real","file": str(path), "items": items}

@router.get('/file')
def file(slot: str = Query(...), session_id: str | None = Query(None)):
    slot_dir = COLLAB_DIR / slot
    if not slot_dir.exists():
        raise HTTPException(404, 'slot not found')
    path = None
    if session_id:
        cand = slot_dir / f'{session_id}.jsonl'
        if cand.exists():
            path = cand
    if path is None:
        files = sorted(slot_dir.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            path = files[0]
    if path is None:
        raise HTTPException(404, 'no collaboration file for slot')
    def iterfile():
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    return StreamingResponse(iterfile(), media_type='application/x-ndjson', headers={
        'Content-Disposition': f'inline; filename="{path.name}"'
    })

