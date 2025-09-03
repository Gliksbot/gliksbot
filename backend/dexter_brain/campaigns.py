from __future__ import annotations
import json
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from .db import BrainDB

@dataclass
class Objective:
    id: str
    description: str
    status: str  # "pending", "in_progress", "completed", "failed"
    created_ts: float
    completed_ts: Optional[float] = None
    assigned_skills: List[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    
    def __post_init__(self):
        if self.assigned_skills is None:
            self.assigned_skills = []

@dataclass
class Campaign:
    id: str
    name: str
    description: str
    status: str  # "active", "paused", "completed", "failed"
    created_ts: float
    objectives: List[Objective]
    skills_generated: List[str]
    progress: Dict[str, Any]
    mode: str = "autonomous"  # "autonomous" or "guided"
    
    def __post_init__(self):
        if not self.objectives:
            self.objectives = []
        if not self.skills_generated:
            self.skills_generated = []
        if not self.progress:
            self.progress = {"overall": 0.0, "objectives_completed": 0, "skills_created": 0}

class CampaignManager:
    def __init__(self, db: BrainDB):
        self.db = db
        self._ensure_tables()
        
    def _ensure_tables(self):
        """Create campaign tables if they don't exist"""
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            mode TEXT DEFAULT 'autonomous',
            created_ts REAL,
            data TEXT,
            updated_ts REAL
        )""")
        
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS campaign_objectives (
            id TEXT PRIMARY KEY,
            campaign_id TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_ts REAL,
            completed_ts REAL,
            assigned_skills TEXT,
            progress REAL DEFAULT 0.0,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )""")
        
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS campaign_skills (
            campaign_id TEXT,
            skill_name TEXT,
            created_ts REAL,
            status TEXT DEFAULT 'active',
            PRIMARY KEY (campaign_id, skill_name),
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        )""")

    def create_campaign(self, name: str, description: str, initial_request: str = "") -> Campaign:
        """Create a new campaign"""
        campaign_id = str(uuid.uuid4())
        now = time.time()
        
        campaign = Campaign(
            id=campaign_id,
            name=name,
            description=description,
            status="active",
            created_ts=now,
            objectives=[],
            skills_generated=[],
            progress={"overall": 0.0, "objectives_completed": 0, "skills_created": 0}
        )
        
        # If initial request provided, create first objective
        if initial_request:
            objective = self.add_objective(campaign_id, initial_request)
            campaign.objectives.append(objective)
        
        # Store in database
        self.db.execute("""
        INSERT INTO campaigns (id, name, description, status, created_ts, data, updated_ts)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (campaign_id, name, description, "active", now, json.dumps(asdict(campaign)), now))
        
        return campaign

    def add_objective(self, campaign_id: str, description: str) -> Objective:
        """Add a new objective to a campaign"""
        objective_id = str(uuid.uuid4())
        now = time.time()
        
        objective = Objective(
            id=objective_id,
            description=description,
            status="pending",
            created_ts=now
        )
        
        self.db.execute("""
        INSERT INTO campaign_objectives (id, campaign_id, description, status, created_ts, assigned_skills, progress)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (objective_id, campaign_id, description, "pending", now, json.dumps([]), 0.0))
        
        return objective

    def update_objective_status(self, objective_id: str, status: str, progress: float = None):
        """Update objective status and progress"""
        updates = ["status = ?"]
        params = [status, objective_id]
        
        if progress is not None:
            updates.append("progress = ?")
            params.insert(-1, progress)
        
        if status == "completed":
            updates.append("completed_ts = ?")
            params.insert(-1, time.time())
        
        sql = f"UPDATE campaign_objectives SET {', '.join(updates)} WHERE id = ?"
        self.db.execute(sql, params)

    def add_skill_to_campaign(self, campaign_id: str, skill_name: str):
        """Associate a promoted skill with a campaign"""
        now = time.time()
        self.db.execute("""
        INSERT OR REPLACE INTO campaign_skills (campaign_id, skill_name, created_ts, status)
        VALUES (?, ?, ?, ?)
        """, (campaign_id, skill_name, now, "active"))

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign with all objectives and skills"""
        cursor = self.db.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        # Get objectives
        cursor = self.db.execute("""
        SELECT id, description, status, created_ts, completed_ts, assigned_skills, progress 
        FROM campaign_objectives WHERE campaign_id = ? ORDER BY created_ts
        """, (campaign_id,))
        
        objectives = []
        for obj_row in cursor.fetchall():
            objectives.append(Objective(
                id=obj_row[0],
                description=obj_row[1],
                status=obj_row[2],
                created_ts=obj_row[3],
                completed_ts=obj_row[4],
                assigned_skills=json.loads(obj_row[5] or "[]"),
                progress=obj_row[6] or 0.0
            ))
        
        # Get skills
        cursor = self.db.execute("""
        SELECT skill_name FROM campaign_skills WHERE campaign_id = ? AND status = 'active'
        """, (campaign_id,))
        skills = [row[0] for row in cursor.fetchall()]
        
        # Calculate progress
        total_objectives = len(objectives)
        completed_objectives = len([obj for obj in objectives if obj.status == "completed"])
        overall_progress = completed_objectives / total_objectives if total_objectives > 0 else 0.0
        
        return Campaign(
            id=row[0],
            name=row[1],
            description=row[2],
            status=row[3],
            created_ts=row[5],
            objectives=objectives,
            skills_generated=skills,
            progress={
                "overall": overall_progress,
                "objectives_completed": completed_objectives,
                "skills_created": len(skills)
            },
            mode=row[4] or "autonomous"
        )

    def list_campaigns(self, status: str = None) -> List[Campaign]:
        """List all campaigns, optionally filtered by status"""
        if status:
            cursor = self.db.execute("SELECT id FROM campaigns WHERE status = ? ORDER BY created_ts DESC", (status,))
        else:
            cursor = self.db.execute("SELECT id FROM campaigns ORDER BY created_ts DESC")
        
        campaigns = []
        for (campaign_id,) in cursor.fetchall():
            campaign = self.get_campaign(campaign_id)
            if campaign:
                campaigns.append(campaign)
        
        return campaigns

    def update_campaign_status(self, campaign_id: str, status: str):
        """Update campaign status"""
        self.db.execute("""
        UPDATE campaigns SET status = ?, updated_ts = ? WHERE id = ?
        """, (status, time.time(), campaign_id))
