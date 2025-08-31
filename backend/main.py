from __future__ import annotations
import os
import json
import asyncio
import uuid
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Placeholder imports - you'll replace these with actual implementations
from dexter_brain.config import Config
from dexter_brain.campaigns import CampaignManager
from dexter_brain.collaboration import CollaborationManager

CONFIG_PATH = os.environ.get("DEXTER_CONFIG_FILE", "/workspaces/gliksbot/config.json")
DOWNLOADS_DIR = os.environ.get("DEXTER_DOWNLOADS_DIR", "/tmp/dexter_downloads")

# Load config
_app_cfg: Config = Config.load(CONFIG_PATH)

# Initialize managers
_campaign_mgr: CampaignManager = None  # Will be initialized after DB setup
_collab_mgr: CollaborationManager = CollaborationManager(_app_cfg)

app = FastAPI(title="Dexter API v3", version="3.0", docs_url="/docs", redoc_url="/redoc")

ALLOWED_ORIGINS = ["http://localhost:3000","http://127.0.0.1:3000","https://gliksbot.com","https://www.gliksbot.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthOut(BaseModel):
    ok: bool = True
    version: str = "3.0"

class CampaignIn(BaseModel):
    name: str
    description: str
    initial_request: str = ""

class CampaignOut(BaseModel):
    id: str
    name: str
    description: str
    status: str
    objectives: List[Dict[str, Any]]
    skills_generated: List[str]
    progress: Dict[str, Any]

class ChatIn(BaseModel):
    message: str
    campaign_id: Optional[str] = None

class ChatOut(BaseModel):
    reply: str
    executed: Optional[Dict[str, Any]] = None
    campaign_updated: Optional[str] = None
    collaboration_session: Optional[str] = None

class ConfigOut(BaseModel):
    config: Dict[str, Any]

# Basic routes
@app.get("/health", response_model=HealthOut)
def health():
    return HealthOut()

@app.get("/config", response_model=ConfigOut)
def get_config():
    return ConfigOut(config=_app_cfg.to_json())

@app.put("/config", response_model=ConfigOut)
def put_config(payload: Dict[str, Any]):
    global _app_cfg, _collab_mgr
    if "api_key" in json.dumps(payload).lower():
        raise HTTPException(400, "Do not store API keys in config; use api_key_env names and env vars.")
    
    # Update config file
    current = json.load(open(CONFIG_PATH, "r", encoding="utf-8"))
    def merge(dst, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                merge(dst[k], v)
            else:
                dst[k] = v
    merge(current, payload)
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    
    # Reload config and managers
    _app_cfg = Config.load(CONFIG_PATH)
    _collab_mgr = CollaborationManager(_app_cfg)
    
    return ConfigOut(config=_app_cfg.to_json())

# Campaign routes
@app.post("/campaigns", response_model=CampaignOut)
async def create_campaign(payload: CampaignIn):
    """Create a new campaign and broadcast to LLMs for planning"""
    if not _campaign_mgr:
        raise HTTPException(500, "Campaign manager not initialized")
    
    campaign = _campaign_mgr.create_campaign(
        payload.name, 
        payload.description, 
        payload.initial_request
    )
    
    # Broadcast to LLMs for initial planning if there's a request
    if payload.initial_request:
        session_id = await _collab_mgr.broadcast_user_input(
            f"Campaign: {payload.name}\nRequest: {payload.initial_request}",
            f"campaign_{campaign.id}"
        )
    
    return CampaignOut(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        objectives=[{
            "id": obj.id,
            "description": obj.description,
            "status": obj.status,
            "progress": obj.progress
        } for obj in campaign.objectives],
        skills_generated=campaign.skills_generated,
        progress=campaign.progress
    )

@app.get("/campaigns")
async def list_campaigns(status: Optional[str] = None):
    """List all campaigns"""
    if not _campaign_mgr:
        raise HTTPException(500, "Campaign manager not initialized")
    
    campaigns = _campaign_mgr.list_campaigns(status)
    return [CampaignOut(
        id=c.id,
        name=c.name,
        description=c.description,
        status=c.status,
        objectives=[{
            "id": obj.id,
            "description": obj.description,
            "status": obj.status,
            "progress": obj.progress
        } for obj in c.objectives],
        skills_generated=c.skills_generated,
        progress=c.progress
    ) for c in campaigns]

@app.get("/campaigns/{campaign_id}", response_model=CampaignOut)
async def get_campaign(campaign_id: str):
    """Get specific campaign details"""
    if not _campaign_mgr:
        raise HTTPException(500, "Campaign manager not initialized")
    
    campaign = _campaign_mgr.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    
    return CampaignOut(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        status=campaign.status,
        objectives=[{
            "id": obj.id,
            "description": obj.description,
            "status": obj.status,
            "progress": obj.progress,
            "assigned_skills": obj.assigned_skills
        } for obj in campaign.objectives],
        skills_generated=campaign.skills_generated,
        progress=campaign.progress
    )

# Enhanced chat with immediate LLM broadcast
@app.post("/chat", response_model=ChatOut)
async def chat(payload: ChatIn):
    """Enhanced chat with immediate LLM collaboration"""
    msg = payload.message or ""
    
    # 1. IMMEDIATELY broadcast to all LLMs (don't wait for Dexter)
    session_id = await _collab_mgr.broadcast_user_input(msg)
    
    # 2. If this is part of a campaign, add as objective
    campaign_updated = None
    if payload.campaign_id and _campaign_mgr:
        try:
            _campaign_mgr.add_objective(payload.campaign_id, msg)
            campaign_updated = payload.campaign_id
        except Exception:
            pass  # Campaign might not exist, continue anyway
    
    # 3. Dexter provides immediate response while LLMs work in background
    dexter_reply = await _get_dexter_response(msg)
    
    # 4. Check if this requires skill creation
    executed = None
    if _intent_implies_skill_creation(msg):
        # Wait briefly for LLM collaboration, then proceed with skill creation
        collaboration_complete = await _collab_mgr.wait_for_collaboration_complete(session_id, timeout=10.0)
        
        if collaboration_complete:
            winning_solution = _collab_mgr.get_winning_solution(session_id)
            if winning_solution:
                # Use LLM collaboration result for skill creation
                executed = await _create_and_test_skill(msg, winning_solution["solution"])
        
        # Fallback: Dexter creates skill if LLM collaboration didn't produce usable result
        if not executed or not executed.get("ok"):
            executed = await _create_and_test_skill(msg, dexter_reply)
    
    return ChatOut(
        reply=dexter_reply,
        executed=executed,
        campaign_updated=campaign_updated,
        collaboration_session=session_id
    )

@app.get("/collaboration/{session_id}")
async def get_collaboration_status(session_id: str):
    """Get status of LLM collaboration session"""
    results = _collab_mgr.get_collaboration_results(session_id)
    vote_counts = _collab_mgr.count_votes(session_id)
    winning_solution = _collab_mgr.get_winning_solution(session_id)
    
    return {
        "session_id": session_id,
        "status": results.get("status", "unknown"),
        "llms_participating": results.get("llms", []),
        "proposals_count": len(results.get("proposals", {})),
        "refinements_count": len(results.get("refinements", {})),
        "votes_count": len(results.get("votes", {})),
        "vote_counts": vote_counts,
        "winning_solution": winning_solution
    }

@app.get("/collaboration/status")
async def get_collaboration_overview():
    """Get overview of all LLM slots and their current status"""
    models = _app_cfg.models
    
    # Get active collaboration sessions
    active_sessions = _collab_mgr.get_active_sessions() if hasattr(_collab_mgr, 'get_active_sessions') else []
    
    slots = {}
    
    # Add Dexter status (always slot 0 / main)
    dexter_config = models.get('dexter', {})
    
    # Add other numbered slots
    for i in range(1, 6):  # Slots 1-5
        slot_key = f"slot_{i}"
        slot_config = models.get(slot_key) or models.get(f"llm_{i}")
        
        if slot_config:
            error = None
            if not slot_config.get('enabled'):
                error = "Slot disabled"
            elif not slot_config.get('api_key'):
                error = "Missing API key"
            elif not slot_config.get('provider'):
                error = "Missing provider"
            elif not slot_config.get('model'):
                error = "Missing model name"
            
            # Check if this slot is currently active in any collaboration
            active = any(slot_key in session.get('participants', []) for session in active_sessions)
            current_task = None
            output = None
            
            if active:
                # Get the most recent output for this slot
                for session in active_sessions:
                    if slot_key in session.get('participants', []):
                        current_task = session.get('original_request', 'Working on collaboration...')
                        # Get latest output from this slot
                        slot_results = session.get('results', {}).get(slot_key, {})
                        if slot_results:
                            output = slot_results.get('latest_output', slot_results.get('proposal', ''))
                        break
            
            slots[slot_key] = {
                'name': slot_config.get('identity', f'LLM {i}'),
                'error': error,
                'active': active,
                'currentTask': current_task,
                'output': output,
                'provider': slot_config.get('provider'),
                'model': slot_config.get('model'),
                'enabled': slot_config.get('enabled', False)
            }
        # If no config, slot will be None and handled by frontend as "not configured"
    
    return {
        'active': len(active_sessions) > 0,
        'sessions': len(active_sessions),
        'slots': slots
    }

@app.post("/models/{slot_id}/config")
async def update_model_config(slot_id: str, payload: dict):
    """Update a specific parameter for a model slot"""
    parameter = payload.get('parameter')
    value = payload.get('value')
    
    if not parameter:
        raise HTTPException(400, "Parameter name required")
    
    # Load current config
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception as e:
        raise HTTPException(500, f"Failed to load config: {str(e)}")
    
    # Ensure models section exists
    if 'models' not in config_data:
        config_data['models'] = {}
    
    # Ensure slot exists
    if slot_id not in config_data['models']:
        config_data['models'][slot_id] = {}
    
    slot_config = config_data['models'][slot_id]
    
    # Update the parameter
    if parameter == 'temperature':
        if 'params' not in slot_config:
            slot_config['params'] = {}
        slot_config['params']['temperature'] = value
    else:
        slot_config[parameter] = value
    
    # Save config
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        raise HTTPException(500, f"Failed to save config: {str(e)}")
    
    # Reload app config
    global _app_cfg, _collab_mgr
    _app_cfg = Config.load(CONFIG_PATH)
    _collab_mgr = CollaborationManager(_app_cfg)
    
    return {"ok": True, "message": f"Updated {parameter} for {slot_id}"}

# Helper functions
async def _get_dexter_response(user_input: str) -> str:
    """Get Dexter's immediate response"""
    # Placeholder - implement actual Dexter LLM call
    return f"I'm working on: {user_input}. My team is collaborating in the background to find the best solution."

def _intent_implies_skill_creation(text: str) -> bool:
    """Check if user input implies need for new skill"""
    import re
    return bool(re.search(r"\b(create|build|make|generate|write|develop|code|script|tool|skill)\b", text, re.IGNORECASE))

async def _create_and_test_skill(user_request: str, solution_content: str) -> Dict[str, Any]:
    """Create and test skill based on solution"""
    # Placeholder - implement actual skill creation and VM testing
    return {
        "ok": True,
        "skill_name": f"skill_{int(time.time())}",
        "tested_in_vm": True,
        "promoted": True,
        "solution_used": solution_content[:100] + "..."
    }

# Downloads route
@app.get("/downloads/list")
def list_downloads():
    path = DOWNLOADS_DIR
    if not os.path.isdir(path):
        return {"ok": False, "error": f"Downloads folder not found: {path}"}
    
    files = []
    for fn in os.listdir(path):
        full = os.path.join(path, fn)
        if os.path.isfile(full):
            files.append({
                "name": fn, 
                "size_kb": round(os.path.getsize(full)/1024,1), 
                "url": f"/api/downloads/get/{fn}"
            })
    return {"ok": True, "files": files}

@app.get("/downloads/get/{filename}")
def get_download(filename: str):
    full = os.path.join(DOWNLOADS_DIR, filename)
    if not os.path.isfile(full):
        raise HTTPException(404, f"File not found: {filename}")
    return FileResponse(full, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
