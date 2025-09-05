from __future__ import annotations
import json, os, time, sqlite3, zipfile, io, subprocess, threading
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body
from .exec_backend import ExecBackend, Limits, choose_backend
from typing import Optional
from .events import emit
from .utils import get_config_path

# Prefer config.json runtime.db_path if available; fallback to env or backend default
try:
    from .utils import get_config_path
    config_path = get_config_path()
    _cfg = json.load(open(config_path,'r',encoding='utf-8'))
    _db_path_from_cfg = _cfg.get('runtime',{}).get('db_path')
except Exception:
    _db_path_from_cfg = None

DB_PATH = _db_path_from_cfg or os.environ.get('DEXTER_DB','backend/dexter.db')
COLLAB_DIR = Path(os.environ.get('DEXTER_COLLAB','backend/collaboration'))
SANDBOX_INBOX = Path(os.environ.get('DEXTER_SANDBOX_INBOX','sandbox/inbox'))
SANDBOX_INBOX.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix='/skills', tags=['skills'])

# ---- DB helper ----
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    # Ensure skills table exists (align with BrainDB schema)
    con.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        code TEXT,
        created_ts REAL NOT NULL,
        updated_ts REAL NOT NULL,
        version INTEGER DEFAULT 1,
        status TEXT DEFAULT 'draft' CHECK (status IN ('draft','active','deprecated','failed')),
        test_results TEXT,
        usage_count INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0.0,
        tags TEXT
    )
    """)
    return con

# ---- Background log streamer ----
_run_handles = {}

def _stream_logs_background(backend: ExecBackend, handle, skill_name: str):
    for ev in backend.stream(handle):
        ev.update({"slot":"sandbox","skill": skill_name, "source":"real"})
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.create_task(emit(ev))
        except Exception:
            # Fallback (sync emit isn't available here); logs still captured in file
            pass

# ---- API ----
@router.get('')
def list_skills(q: Optional[str]=None, status: Optional[str]=None):
    with db() as con:
        sql = 'SELECT id,name,description,version,status,tags,usage_count,success_rate,updated_ts FROM skills'
        where, args = [], []
        if status:
            where.append('status=?'); args.append(status)
        if q:
            where.append('(name LIKE ? OR description LIKE ?)'); args += [f'%{q}%']*2
        if where:
            sql += ' WHERE ' + ' AND '.join(where)
        sql += ' ORDER BY updated_ts DESC'
        rows = [dict(r) for r in con.execute(sql, args)]
    return {"source":"real","items":rows}

@router.post('')
def create_skill(name: str = Body(...), description: str = Body(""), manifest: dict = Body(...), code: str = Body(""), tests: dict = Body({})):
    now = time.time()
    pkg_name = f"{name}_{int(now)}.zip"
    pkg_path = SANDBOX_INBOX / pkg_name
    # Build zip in-memory
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(manifest))
        if code:
            z.writestr('skill.py', code)
        for rel, content in (tests or {}).items():
            z.writestr(rel, content)
    pkg_path.write_bytes(mem.getvalue())
    with db() as con:
        cur = con.execute('INSERT INTO skills(name,description,code,created_ts,updated_ts,version,status,test_results,tags) VALUES(?,?,?,?,?,?,?,?,?)',
            (name, description, code, now, now, 1, 'draft', None, None))
        skill_id = cur.lastrowid
        con.commit()
    # Log
    try:
        import asyncio
        asyncio.get_event_loop().create_task(emit({"slot":"dexter","event":"skill.package","files":[str(pkg_path)],"skill":name}))
    except Exception:
        pass
    return {"source":"real","id":skill_id,"package":str(pkg_path)}

@router.post('/{skill_id}/test')
def test_skill(skill_id: int, cmd: Optional[list[str]] = Body(None), sandbox_cfg: Optional[dict]=Body(None)):
    with db() as con:
        row = con.execute('SELECT name FROM skills WHERE id=?', (skill_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'skill not found')
        name = row['name']
    pkgs = sorted(SANDBOX_INBOX.glob(f"{name}_*.zip"))
    if not pkgs:
        raise HTTPException(404, 'no package found to test')
    pkg = pkgs[-1]
    cfg = sandbox_cfg or json.load(open(get_config_path(),'r'))
    backend = choose_backend(cfg)
    limits = Limits()
    handle = backend.run(pkg_zip=pkg, cmd=(cmd or ['python','/runner.py','--package','/run/pkg.zip']), limits=limits)
    _run_handles[handle.id] = handle
    t = threading.Thread(target=_stream_logs_background, args=(backend, handle, name), daemon=True)
    t.start()
    try:
        import asyncio
        asyncio.get_event_loop().create_task(emit({"slot":"sandbox","event":"skill.test.start","skill":name,"run_id":handle.id,"source":"real"}))
    except Exception:
        pass
    return {"source":"real","run_id":handle.id}

@router.post('/{skill_id}/promote')
def promote_skill(skill_id: int, risk_score: float = Body(0.0)):
    cfg = json.load(open(get_config_path(),'r'))
    max_risk = cfg.get('policy',{}).get('autonomy',{}).get('max_risk_score', 0.5)
    if risk_score > max_risk:
        raise HTTPException(400, f'risk {risk_score} exceeds threshold {max_risk}')
    with db() as con:
        row = con.execute('SELECT status,name FROM skills WHERE id=?', (skill_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'skill not found')
        con.execute('UPDATE skills SET status="active", updated_ts=? WHERE id=?', (time.time(), skill_id))
        con.commit()
    try:
        import asyncio
        asyncio.get_event_loop().create_task(emit({"slot":"dexter","event":"skill.promote","skill":row['name'],"source":"real"}))
    except Exception:
        pass
    return {"source":"real","id":skill_id,"status":"active"}

@router.post('/{skill_id}/execute')
def execute_skill(skill_id: int, args: Optional[dict]=Body({})):
    with db() as con:
        row = con.execute('SELECT name,status,code FROM skills WHERE id=?', (skill_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'skill not found')
        if row['status'] != 'active':
            raise HTTPException(403, 'skill is not active')
        name = row['name']
        code = row['code'] or ''
    tmp = Path('skills_active')/name
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp/'skill.py').write_text(code, encoding='utf-8')
    # NOTE: Functional execution on host; for production use OS-level sandboxing.
    proc = subprocess.run(['python', str(tmp/'skill.py')], input=json.dumps(args).encode('utf-8'), timeout=60)
    try:
        import asyncio
        asyncio.get_event_loop().create_task(emit({"slot":"dexter","event":"skill.execute.host.completed","skill":name,"rc":proc.returncode,"source":"real"}))
    except Exception:
        pass
    return {"source":"real","rc":proc.returncode}

