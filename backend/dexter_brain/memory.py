from __future__ import annotations
from collections import deque
from typing import Any, Dict, List, Optional

from .db import BrainDB


class MemoryManager:
    """Runtime short-term memory backed by persistent BrainDB."""

    def __init__(self, db: BrainDB, stm_capacity: int = 100):
        self.db = db
        self.stm_capacity = stm_capacity
        self.stm = deque(maxlen=stm_capacity)
        # Preload recent short-term memories into RAM
        for mem in db.get_memories('stm', limit=stm_capacity):
            self.stm.append(mem)

    def remember(self, content: str, memory_type: str = 'stm',
                 metadata: Dict[str, Any] | None = None,
                 tags: List[str] | None = None,
                 importance: float = 0.5) -> int:
        """Store a memory and update RAM cache when appropriate."""
        mem_id = self.db.add_memory(content, memory_type, metadata, tags, importance)
        if memory_type == 'stm':
            self.stm.append({
                'id': mem_id,
                'type': memory_type,
                'content': content,
                'metadata': metadata or {},
                'tags': tags or [],
                'importance': importance,
            })
        return mem_id

    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories for context."""
        return self.db.search_memories(query, limit=limit)

    def get_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return the most recent short-term memories in RAM."""
        if limit <= 0:
            return []
        return list(self.stm)[-limit:]
