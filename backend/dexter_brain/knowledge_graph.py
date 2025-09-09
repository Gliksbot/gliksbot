from __future__ import annotations
from typing import Any, Dict, List

from .db import BrainDB


class KnowledgeGraph:
    """In-memory cache of the knowledge graph backed by BrainDB."""

    def __init__(self, db: BrainDB):
        self.db = db
        self.nodes: Dict[int, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self._load_from_db()

    def _load_from_db(self) -> None:
        for row in self.db.fetchall("SELECT * FROM knowledge_nodes"):
            node = self.db._row_to_dict(row)
            self.nodes[node['id']] = node
        for row in self.db.fetchall("SELECT * FROM knowledge_edges"):
            self.edges.append(self.db._row_to_dict(row))

    def add_node(self, label: str, data: Dict[str, Any] | None = None,
                 embedding: List[float] | None = None) -> Dict[str, Any]:
        node_id = self.db.add_knowledge_node(label, data, embedding)
        node = self.db.get_knowledge_node(node_id)
        self.nodes[node_id] = node
        return node

    def add_edge(self, source_id: int, target_id: int, relation: str,
                 weight: float = 1.0, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        edge_id = self.db.add_knowledge_edge(source_id, target_id, relation, weight, metadata)
        row = self.db.fetchone("SELECT * FROM knowledge_edges WHERE id = ?", (edge_id,))
        edge = self.db._row_to_dict(row)
        self.edges.append(edge)
        return edge

    def get_node(self, node_id: int) -> Dict[str, Any] | None:
        node = self.nodes.get(node_id)
        if node is None:
            node = self.db.get_knowledge_node(node_id)
            if node:
                self.nodes[node_id] = node
        return node

    def get_neighbors(self, node_id: int) -> List[Dict[str, Any]]:
        neighbors = [e for e in self.edges if e['source_id'] == node_id or e['target_id'] == node_id]
        if not neighbors:
            neighbors = self.db.get_neighbors(node_id)
            self.edges.extend(neighbors)
        return neighbors
