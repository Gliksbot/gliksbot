import asyncio
import time
from typing import AsyncIterator, Dict, Any

# Simple in-process event bus for SSE
bus: asyncio.Queue = asyncio.Queue(maxsize=50000)

async def emit(event: Dict[str, Any]):
    event.setdefault("ts", time.time())
    event.setdefault("source", "real")
    await bus.put(event)

async def consume() -> AsyncIterator[Dict[str, Any]]:
    while True:
        e = await bus.get()
        yield e

