from backend.dexter_brain.db import BrainDB
from backend.dexter_brain.memory import MemoryManager
from backend.dexter_brain.knowledge_graph import KnowledgeGraph


def test_memory_manager_stm_and_recall():
    db = BrainDB(":memory:")
    mgr = MemoryManager(db, stm_capacity=2)
    mgr.remember("alpha")
    mgr.remember("beta")
    mgr.remember("gamma")  # Should push out oldest due to capacity
    recent = mgr.get_recent(2)
    assert len(recent) == 2
    assert recent[-1]["content"] == "gamma"
    results = mgr.recall("beta")
    assert any(r["content"] == "beta" for r in results)


def test_knowledge_graph_nodes_and_edges():
    db = BrainDB(":memory:")
    kg = KnowledgeGraph(db)
    n1 = kg.add_node("node1", {"type": "test"})
    n2 = kg.add_node("node2")
    edge = kg.add_edge(n1["id"], n2["id"], "related")
    neighbors = kg.get_neighbors(n1["id"])
    assert edge in neighbors
