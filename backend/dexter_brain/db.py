"""
Database abstraction layer for Dexter v3.
Handles SQLite operations, memory management, and full-text search.
"""

from __future__ import annotations
import json
import sqlite3
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

class BrainDB:
    """Database abstraction layer for Dexter's brain."""
    
    def __init__(self, db_path: str = "./dexter.db", enable_fts: bool = True):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to SQLite database file
            enable_fts: Whether to enable full-text search capabilities
        """
        self.db_path = db_path
        self.enable_fts = enable_fts
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Initialize tables
        self._init_core_tables()
        if enable_fts:
            self._init_fts_tables()
    
    def _init_core_tables(self):
        """Initialize core database tables."""
        # Memory table for STM/LTM
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK (type IN ('stm', 'ltm')),
            content TEXT NOT NULL,
            metadata TEXT,  -- JSON metadata
            created_ts REAL NOT NULL,
            accessed_ts REAL NOT NULL,
            access_count INTEGER DEFAULT 1,
            importance REAL DEFAULT 0.5,
            tags TEXT  -- JSON array of tags
        )
        """)
        
        # Skills table
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            code TEXT NOT NULL,
            created_ts REAL NOT NULL,
            updated_ts REAL NOT NULL,
            version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'failed')),
            test_results TEXT,  -- JSON test results
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            tags TEXT  -- JSON array of tags
        )
        """)
        
        # Patterns table for learning
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pattern_type TEXT NOT NULL,
            pattern_data TEXT NOT NULL,  -- JSON pattern data
            confidence REAL DEFAULT 0.5,
            created_ts REAL NOT NULL,
            updated_ts REAL NOT NULL,
            usage_count INTEGER DEFAULT 0
        )
        """)
        
        # Collaboration sessions
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS collaboration_sessions (
            id TEXT PRIMARY KEY,
            user_input TEXT NOT NULL,
            started_ts REAL NOT NULL,
            completed_ts REAL,
            status TEXT DEFAULT 'active',
            winning_solution TEXT,  -- JSON winning solution data
            all_solutions TEXT,  -- JSON all solutions data
            vote_results TEXT  -- JSON vote results
        )
        """)
        
        # Create indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_ts)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_skills_status ON skills(status)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_collaboration_status ON collaboration_sessions(status)")
        
        self.conn.commit()
    
    def _init_fts_tables(self):
        """Initialize full-text search tables."""
        try:
            # FTS table for memories
            self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content,
                tags,
                content='memories',
                content_rowid='id'
            )
            """)
            
            # FTS table for skills
            self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
                name,
                description,
                code,
                tags,
                content='skills',
                content_rowid='id'
            )
            """)
            
            # Triggers to keep FTS in sync
            self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_fts_insert AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content, tags) VALUES (new.id, new.content, new.tags);
            END
            """)
            
            self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_fts_update AFTER UPDATE ON memories BEGIN
                UPDATE memories_fts SET content = new.content, tags = new.tags WHERE rowid = new.id;
            END
            """)
            
            self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_fts_delete AFTER DELETE ON memories BEGIN
                DELETE FROM memories_fts WHERE rowid = old.id;
            END
            """)
            
            self.conn.commit()
        except sqlite3.OperationalError:
            # FTS5 not available, disable FTS
            self.enable_fts = False
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL with parameters."""
        return self.conn.execute(sql, params)
    
    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute SQL and fetch one row."""
        cursor = self.conn.execute(sql, params)
        return cursor.fetchone()
    
    def fetchall(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute SQL and fetch all rows."""
        cursor = self.conn.execute(sql, params)
        return cursor.fetchall()
    
    def commit(self):
        """Commit pending transactions."""
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    # Memory management methods
    def add_memory(self, content: str, memory_type: str = 'stm', 
                   metadata: Dict[str, Any] = None, tags: List[str] = None,
                   importance: float = 0.5) -> int:
        """Add a memory to the database."""
        now = time.time()
        metadata_json = json.dumps(metadata or {})
        tags_json = json.dumps(tags or [])
        
        cursor = self.conn.execute("""
        INSERT INTO memories (type, content, metadata, created_ts, accessed_ts, importance, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (memory_type, content, metadata_json, now, now, importance, tags_json))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_memories(self, memory_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve memories from database."""
        sql = "SELECT * FROM memories"
        params = []
        
        if memory_type:
            sql += " WHERE type = ?"
            params.append(memory_type)
        
        sql += " ORDER BY accessed_ts DESC LIMIT ?"
        params.append(limit)
        
        rows = self.fetchall(sql, tuple(params))
        return [self._row_to_dict(row) for row in rows]
    
    def search_memories(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search memories using full-text search."""
        if not self.enable_fts:
            # Fallback to LIKE search
            rows = self.fetchall("""
            SELECT * FROM memories 
            WHERE content LIKE ? OR tags LIKE ?
            ORDER BY accessed_ts DESC LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
        else:
            rows = self.fetchall("""
            SELECT memories.* FROM memories
            JOIN memories_fts ON memories.id = memories_fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank LIMIT ?
            """, (query, limit))
        
        return [self._row_to_dict(row) for row in rows]
    
    def update_memory_access(self, memory_id: int):
        """Update memory access timestamp and count."""
        now = time.time()
        self.conn.execute("""
        UPDATE memories 
        SET accessed_ts = ?, access_count = access_count + 1
        WHERE id = ?
        """, (now, memory_id))
        self.conn.commit()
    
    # Skill management methods
    def add_skill(self, name: str, description: str, code: str, 
                  test_results: Dict[str, Any] = None, tags: List[str] = None) -> int:
        """Add a skill to the database."""
        now = time.time()
        test_results_json = json.dumps(test_results or {})
        tags_json = json.dumps(tags or [])
        
        cursor = self.conn.execute("""
        INSERT INTO skills (name, description, code, created_ts, updated_ts, test_results, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, description, code, now, now, test_results_json, tags_json))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a skill by name."""
        row = self.fetchone("SELECT * FROM skills WHERE name = ?", (name,))
        return self._row_to_dict(row) if row else None
    
    def list_skills(self, status: str = 'active') -> List[Dict[str, Any]]:
        """List skills by status."""
        rows = self.fetchall("SELECT * FROM skills WHERE status = ? ORDER BY name", (status,))
        return [self._row_to_dict(row) for row in rows]
    
    def update_skill_usage(self, skill_id: int, success: bool = True):
        """Update skill usage statistics."""
        skill = self.fetchone("SELECT usage_count, success_rate FROM skills WHERE id = ?", (skill_id,))
        if skill:
            usage_count = skill['usage_count'] + 1
            success_rate = skill['success_rate']
            
            # Update success rate
            if success:
                success_rate = ((success_rate * (usage_count - 1)) + 1) / usage_count
            else:
                success_rate = (success_rate * (usage_count - 1)) / usage_count
            
            self.conn.execute("""
            UPDATE skills 
            SET usage_count = ?, success_rate = ?
            WHERE id = ?
            """, (usage_count, success_rate, skill_id))
            self.conn.commit()
    
    # Collaboration methods
    def save_collaboration_session(self, session_id: str, user_input: str, 
                                   winning_solution: Dict[str, Any] = None,
                                   all_solutions: Dict[str, Any] = None,
                                   vote_results: Dict[str, Any] = None):
        """Save collaboration session results."""
        now = time.time()
        
        self.conn.execute("""
        INSERT OR REPLACE INTO collaboration_sessions 
        (id, user_input, started_ts, completed_ts, status, winning_solution, all_solutions, vote_results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, user_input, now, now, 'completed',
            json.dumps(winning_solution or {}),
            json.dumps(all_solutions or {}),
            json.dumps(vote_results or {})
        ))
        self.conn.commit()
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary."""
        if not row:
            return None
        
        result = dict(row)
        
        # Parse JSON fields
        for field in ['metadata', 'tags', 'test_results', 'pattern_data', 
                      'winning_solution', 'all_solutions', 'vote_results']:
            if field in result and result[field]:
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return result
    
    # Maintenance methods
    def cleanup_old_memories(self, days: int = 30, memory_type: str = 'stm'):
        """Clean up old memories."""
        cutoff = time.time() - (days * 24 * 60 * 60)
        self.conn.execute("""
        DELETE FROM memories 
        WHERE type = ? AND created_ts < ? AND access_count <= 1
        """, (memory_type, cutoff))
        self.conn.commit()
    
    def get_db_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        # Memory stats
        memory_stats = self.fetchone("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN type = 'stm' THEN 1 ELSE 0 END) as stm_count,
            SUM(CASE WHEN type = 'ltm' THEN 1 ELSE 0 END) as ltm_count
        FROM memories
        """)
        stats['memories'] = dict(memory_stats) if memory_stats else {}
        
        # Skill stats
        skill_stats = self.fetchone("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
            SUM(usage_count) as total_usage
        FROM skills
        """)
        stats['skills'] = dict(skill_stats) if skill_stats else {}
        
        # Collaboration stats
        collab_stats = self.fetchone("""
        SELECT 
            COUNT(*) as total_sessions,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_sessions
        FROM collaboration_sessions
        """)
        stats['collaboration'] = dict(collab_stats) if collab_stats else {}
        
        return stats