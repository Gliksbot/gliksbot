import json, asyncio, os
from fastapi import APIRouter, Body
from starlette.responses import StreamingResponse
from .events import consume, emit

router = APIRouter()

def _keepalive_interval() -> int:
    try:
        cfg = json.load(open('config.json','r',encoding='utf-8'))
        return int(cfg.get('events',{}).get('keepalive_sec', 20))
    except Exception:
        return 20

async def _stream():
    interval = _keepalive_interval()
    agen = consume()
    while True:
        try:
            e = await asyncio.wait_for(agen.__anext__(), timeout=interval)
            yield f"data: {json.dumps(e, ensure_ascii=False)}\n\n"
        except asyncio.TimeoutError:
            # SSE comment line as heartbeat (not delivered to onmessage)
            yield ": keepalive\n\n"
        except StopAsyncIteration:
            # End of stream
            break

@router.get("/events")
async def events():
    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/events/ping")
async def ping(slot: str = Body("dexter"), text: str = Body("UI ping"), event: str = Body("ui.ping")):
    await emit({"slot": slot, "event": event, "text": text})
    return {"ok": True}
