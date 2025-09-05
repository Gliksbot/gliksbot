from __future__ import annotations
import os
import json
import asyncio
import uuid
import time
import traceback
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Bootstrap when running as top‑level module
#
# When this file is executed via ``python backend/main.py`` or imported through
# ``uvicorn main:app`` while the current working directory is ``backend``, the
# module is treated as a top‑level module and ``__package__`` is empty.  In that
# case, relative imports like ``from .dexter_brain.config`` will fail with
# ``ImportError: No module named 'dexter_brain'``.  To allow this file to be
# executed directly and still support relative imports, detect the empty
# ``__package__`` and adjust ``sys.path`` and ``__package__`` accordingly.
import pathlib
import sys
if __package__ in (None, ""):
    current_dir = pathlib.Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    # Prepend the project root so that ``backend`` becomes importable as a
    # package.  Without this, importing ``backend.dexter_brain`` would fail.
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    __package__ = "backend"

# Import from backend package using relative imports
from .auth import (
    router as auth_router,
    get_current_user,
    verify_token_optional,
    auth_manager,
)
from .dexter_brain.config import Config
from .dexter_brain.campaigns import CampaignManager
from .dexter_brain.collaboration import CollaborationManager
from .dexter_brain.llm import call_slot
# NEW: BrainDB for STM/LTM
from .dexter_brain.db import BrainDB
# NEW: SkillsManager for dynamic skill execution
from .skills.skills_manager import SkillsManager
# NEW: Error tracking and healing
from .dexter_brain.error_tracker import ErrorTracker, ErrorSeverity
from .dexter_brain.error_healer import ErrorHealer
from .dexter_brain.enhanced_skills import create_and_test_skill_with_healing, get_sandbox_health_status
# NEW: Autonomous skill generation
from .dexter_brain.autonomy import AutonomyManager

# Get the directory where this script is located and find project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Go up one level from backend/ to project root

CONFIG_PATH = os.environ.get("DEXTER_CONFIG_FILE", os.path.join(PROJECT_ROOT, "config.json"))
DOWNLOADS_DIR = os.environ.get("DEXTER_DOWNLOADS_DIR", "/tmp/dexter_downloads")
SKILLS_DIR = os.environ.get("DEXTER_SKILLS_DIR", os.path.join(SCRIPT_DIR, "skills"))

# Load config
_app_cfg: Config = Config.load(CONFIG_PATH)

# Initialize DB for memories (STM/LTM)
_db: Optional[BrainDB] = None
try:
    _db = BrainDB(
        db_path=_app_cfg.runtime.get('db_path', './dexter.db'),
        enable_fts=_app_cfg.runtime.get('enable_fts', True)
    )
except Exception:
    _db = None  # Fail open; endpoints continue to work without memory

# Initialize managers
_campaign_mgr: CampaignManager = None  # Will be initialized after DB setup
_collab_mgr: CollaborationManager = CollaborationManager(_app_cfg)
# NEW: Initialize SkillsManager for dynamic skill execution
_skills_mgr: Optional[SkillsManager] = None
try:
    _skills_mgr = SkillsManager(SKILLS_DIR)
except Exception as e:
    print(f"Warning: Failed to initialize SkillsManager: {e}")
    _skills_mgr = None

# NEW: Initialize error tracking and healing system
_error_tracker = ErrorTracker(max_errors=1000, persist_path="./logs/errors.jsonl")
_error_healer: Optional[ErrorHealer] = None

# NEW: Autonomous skill generation system  
_autonomy_mgr: Optional['AutonomyManager'] = None

app = FastAPI(title="Dexter API v3", version="3.0", docs_url="/docs", redoc_url="/redoc")

# NEW: Global exception handler for error tracking
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that logs errors for healing. Redacts auth headers."""
    safe_headers = {}
    for k, v in request.headers.items():
        lk = k.lower()
        if lk in {"authorization", "proxy-authorization"}:
            safe_headers[k] = "REDACTED"
        else:
            safe_headers[k] = v
    error_id = _error_tracker.log_error(
        error_type=type(exc).__name__,
        message=str(exc),
        severity=ErrorSeverity.HIGH,
        source="api",
        context={
            "endpoint": str(request.url),
            "method": request.method,
            "headers": safe_headers,
            "user_agent": request.headers.get("user-agent", "unknown")
        },
        stack_trace=traceback.format_exc()
    )
    return JSONResponse(status_code=500, content={"error": "Internal server error", "error_id": error_id, "message": "Error has been logged"})

# NEW: Startup event to initialize error healer
startup_time = time.time()

@app.on_event("startup")
async def startup_event():
    """Initialize error healing system when the application starts."""
    global _error_healer, _campaign_mgr, _autonomy_mgr
    try:
        # Initialize campaign manager if database is available
        if _db:
            _campaign_mgr = CampaignManager(_db)
            print("✅ Campaign manager initialized")
        else:
            print("⚠️  Campaign manager not initialized - database unavailable")
        
        # Initialize error healer
        _error_healer = ErrorHealer(_app_cfg, _error_tracker, _collab_mgr)
        
        # Initialize autonomy manager
        if _skills_mgr and _collab_mgr:
            from .dexter_brain.sandbox import create_sandbox
            _autonomy_mgr = AutonomyManager(_app_cfg, _collab_mgr, _skills_mgr, create_sandbox)
            print("✅ Autonomous skill generation system initialized")
        else:
            print("⚠️  Autonomy manager not initialized - missing dependencies")
        
        # Start error monitoring task
        asyncio.create_task(_error_healer.start_error_monitoring())
        
        print("✅ Error tracking and healing system initialized")
        
        # Log successful startup
        _error_tracker.log_error(
            "SYSTEM_STARTUP",
            "Dexter v3 system started successfully with autonomous skill generation",
            ErrorSeverity.LOW,
            "system",
            {
                "sandbox_provider": _app_cfg.runtime.get('sandbox', {}).get('provider', 'unknown'),
                "error_tracking_enabled": True,
                "error_healing_enabled": True,
                "autonomy_enabled": _autonomy_mgr is not None
            },
            auto_capture_traceback=False
        )
        
    except Exception as e:
        print(f"❌ Failed to initialize systems: {e}")
        _error_tracker.log_error(
            "STARTUP_ERROR",
            f"Failed to initialize systems: {e}",
            ErrorSeverity.CRITICAL,
            "system"
        )

# Include API routers
app.include_router(auth_router)
from .dexter_brain import events_api, collaboration_api, skills_api
app.include_router(events_api.router)
app.include_router(collaboration_api.router)
app.include_router(skills_api.router)

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

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

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
    skills_results: Optional[List[Dict[str, Any]]] = None

class ConfigOut(BaseModel):
    config: Dict[str, Any]

# Enhanced health endpoint with sandbox status
@app.get("/health", response_model=HealthOut)
def health():
    return HealthOut()

# NEW: Detailed system health endpoint
@app.get("/health/detailed")
def detailed_health(current_user: dict = Depends(get_current_user)):
    """Get detailed system health including sandbox and error tracking status."""
    
    # Get sandbox health
    sandbox_health = get_sandbox_health_status(_app_cfg.to_json())
    
    # Get error statistics
    error_stats = _error_tracker.get_error_statistics()
    
    # Get healing statistics
    healing_stats = {}
    if _error_healer:
        healing_stats = _error_healer.get_healing_statistics()
    
    return {
        "system": {
            "status": "healthy",
            "version": "3.0",
            "uptime_seconds": time.time() - startup_time if 'startup_time' in globals() else 0
        },
        "sandbox": sandbox_health,
        "error_tracking": {
            "enabled": True,
            "stats": error_stats
        },
        "error_healing": {
            "enabled": _error_healer is not None,
            "stats": healing_stats
        },
        "collaboration": {
            "active_sessions": len(_collab_mgr.get_active_sessions())
        }
    }

# NEW: Error tracking endpoints
@app.get("/errors/recent")
def get_recent_errors(
    minutes: int = Query(60, description="Get errors from last N minutes"),
    current_user: dict = Depends(get_current_user)
):
    """Get recent system errors."""
    errors = _error_tracker.get_recent_errors(minutes)
    return {
        "errors": [error.to_dict() for error in errors],
        "count": len(errors),
        "time_range_minutes": minutes
    }

@app.get("/errors/statistics")
def get_error_statistics(current_user: dict = Depends(get_current_user)):
    """Get error statistics and trends."""
    return _error_tracker.get_error_statistics()

@app.post("/errors/{error_id}/resolve")
def mark_error_resolved(
    error_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Manually mark an error as resolved."""
    success = _error_tracker.mark_resolved(error_id)
    if success:
        return {"message": f"Error {error_id} marked as resolved"}
    else:
        raise HTTPException(status_code=404, detail="Error not found")

# NEW: Sandbox testing endpoint
@app.post("/sandbox/test")
async def test_sandbox(
    test_code: str,
    current_user: dict = Depends(get_current_user)
):
    """Test code execution in the sandbox."""
    try:
        from .dexter_brain.sandbox import create_sandbox
        
        sandbox = create_sandbox(_app_cfg.to_json())
        result = await sandbox.execute_skill(test_code)
        
        return {
            "success": result.get('success', False),
            "output": result.get('output', ''),
            "execution_time": result.get('execution_time', 0),
            "sandbox_type": result.get('sandbox_type', 'unknown')
        }
        
    except Exception as e:
        _error_tracker.log_error(
            "SANDBOX_TEST_FAILED",
            str(e),
            ErrorSeverity.MEDIUM,
            "api",
            {"test_code": test_code[:200]}
        )
        raise HTTPException(status_code=500, detail=f"Sandbox test failed: {e}")

# Authentication routes
@app.post("/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """Login with hardcoded credentials and return a JWT token."""
    user_info = auth_manager.authenticate_user(credentials.username, credentials.password)
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Generate a JWT token.  Use the backwards‑compatible alias on the
    # AuthManager which encodes the username into the subject (sub) claim.
    token = auth_manager.create_jwt_token(user_info)

    # The response_model specifies ``access_token`` and ``token_type`` fields.
    return LoginResponse(access_token=token, token_type="bearer")

@app.post("/auth/logout")
def logout():
    """Logout endpoint (token invalidation handled client-side)"""
    return {"message": "Logged out successfully"}

@app.get("/auth/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.get("/config", response_model=ConfigOut)
def get_config(current_user: dict = Depends(get_current_user)):
    return ConfigOut(config=_app_cfg.to_json())

@app.get("/config/public", response_model=ConfigOut)
def get_config_public():
    """Public config endpoint for frontend sync (no auth required)"""
    return ConfigOut(config=_app_cfg.to_json())

@app.put("/config", response_model=ConfigOut)
def put_config(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
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
async def create_campaign(payload: CampaignIn, current_user: dict = Depends(get_current_user)):
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
async def list_campaigns(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
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
async def get_campaign(campaign_id: str, current_user: dict = Depends(get_current_user)):
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

# Enhanced chat with autonomous skill generation
@app.post("/chat", response_model=ChatOut)
async def chat(payload: ChatIn, current_user: dict = Depends(get_current_user)):
    """Enhanced chat with autonomous skill generation and execution"""
    msg = payload.message or ""
    
    # Check if Dexter is properly configured
    dexter_config = _app_cfg.models.get('dexter', {})
    dexter_errors = validate_model_config('dexter', dexter_config)
    
    if dexter_errors:
        error_msg = f"Dexter is not properly configured: {', '.join(dexter_errors)}"
        return ChatOut(
            reply=error_msg,
            executed=None,
            campaign_updated=None,
            collaboration_session=None
        )

    # Build conversation history for context (last 10 messages)
    conversation_history = []
    if _db:
        try:
            recent_memories = _db.get_memories('stm', limit=10)
            conversation_history = [m.get('content', '') for m in recent_memories if m.get('content')]
        except Exception:
            pass

    # 1. IMMEDIATELY broadcast to all LLMs and start autonomous processing
    session_id = await _collab_mgr.broadcast_user_input(msg)
    
    # 2. Process autonomous skill request in parallel
    autonomous_result = None
    if _autonomy_mgr:
        try:
            autonomous_result = await _autonomy_mgr.process_autonomous_request(msg, conversation_history)
        except Exception as e:
            print(f"Warning: Autonomous processing error: {e}")
            autonomous_result = {'autonomous_action': False, 'error': str(e)}

    # 3. Handle campaign integration
    campaign_updated = None
    if payload.campaign_id and _campaign_mgr:
        try:
            _campaign_mgr.add_objective(payload.campaign_id, msg)
            campaign_updated = payload.campaign_id
        except Exception:
            pass

    # 4. Get Dexter's response - may include clarifying questions
    dexter_reply = ""
    if autonomous_result and autonomous_result.get('needs_clarification'):
        # Dexter asks clarifying questions
        dexter_reply = autonomous_result.get('clarifying_question', 'Could you provide more details?')
    else:
        # Normal Dexter response
        try:
            dexter_reply = await _get_dexter_response(msg)
        except Exception as e:
            return ChatOut(
                reply=f"Error communicating with Dexter: {str(e)}. Please check Dexter's configuration in the Models tab.",
                executed=None,
                campaign_updated=campaign_updated,
                collaboration_session=session_id,
                skills_results=None
            )

    # 5. Execute existing skills on the message
    skills_results = None
    if _skills_mgr:
        try:
            skills_results = await _skills_mgr.execute_all_skills(msg)
        except Exception as e:
            print(f"Warning: Error executing existing skills: {e}")
            skills_results = [{
                'success': False,
                'error': f"Skills execution failed: {str(e)}",
                'skill_name': 'system'
            }]

    # 6. Handle autonomous skill generation results
    executed = None
    if autonomous_result and autonomous_result.get('autonomous_action'):
        if autonomous_result.get('skill_generated'):
            executed = autonomous_result.get('promotion_result', {})
        elif autonomous_result.get('used_existing_skill'):
            executed = {
                'ok': True,
                'used_existing': True,
                'skill_name': autonomous_result.get('skill_name'),
                'execution_result': autonomous_result.get('execution_result')
            }

    # 7. Persist conversation for future context
    try:
        if _db is not None:
            conversation_content = f"User: {msg}\nDexter: {dexter_reply}"
            if autonomous_result and autonomous_result.get('autonomous_action'):
                conversation_content += f"\nAutonomous Action: {autonomous_result.get('skill_name', 'skill executed')}"
            
            _db.add_memory(
                content=conversation_content,
                memory_type='stm',
                tags=['chat', 'conversation'],
                metadata={'timestamp': time.time(), 'session_id': session_id}
            )
    except Exception:
        pass

    return ChatOut(
        reply=dexter_reply,
        executed=executed,
        campaign_updated=campaign_updated,
        collaboration_session=session_id,
        skills_results=skills_results
    )

# Individual LLM Chat Model
class LLMChatIn(BaseModel):
    message: str
    model: str
    config: Optional[Dict[str, Any]] = None

class LLMChatOut(BaseModel):
    response: str
    model: str
    success: bool
    error: Optional[str] = None

# TTS Configuration Models
class TTSSettingsIn(BaseModel):
    enabled: bool = True
    rate: float = 1.0
    pitch: float = 1.0
    volume: float = 0.8
    voice: Optional[str] = None

class TTSSettingsOut(BaseModel):
    settings: Dict[str, Any]

# Individual LLM chat endpoint
@app.post("/llm/chat", response_model=LLMChatOut)
async def llm_chat(payload: LLMChatIn, current_user: dict = Depends(get_current_user)):
    """Chat with a specific LLM model"""
    try:
        # Use provided config or fall back to global config
        if payload.config:
            # Create a temporary config using the provided settings
            temp_config = type('obj', (object,), {
                'models': {payload.model: payload.config}
            })()
            response = await call_slot(temp_config, payload.model, payload.message)
        else:
            # Use global config
            if payload.model not in _app_cfg.models:
                return LLMChatOut(
                    response="",
                    model=payload.model,
                    success=False,
                    error=f"Model '{payload.model}' not found in configuration"
                )
            
            response = await call_slot(_app_cfg, payload.model, payload.message)
        
        return LLMChatOut(
            response=response,
            model=payload.model,
            success=True,
            error=None
        )
    
    except Exception as e:
        return LLMChatOut(
            response="",
            model=payload.model,
            success=False,
            error=str(e)
        )

# TTS Configuration endpoints
@app.get("/tts/settings")
async def get_tts_settings():
    """Get global TTS settings"""
    tts_config = _app_cfg.to_json().get('tts', {
        'enabled': True,
        'global_settings': {
            'rate': 1.0,
            'pitch': 1.0,
            'volume': 0.8,
            'voice': None
        },
        'per_model_settings': {}
    })
    return TTSSettingsOut(settings=tts_config)

@app.post("/tts/settings")
async def update_tts_settings(payload: TTSSettingsIn, current_user: dict = Depends(get_current_user)):
    """Update global TTS settings"""
    global _app_cfg
    
    # Load current config
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        current = json.load(f)
    
    # Ensure tts section exists
    if 'tts' not in current:
        current['tts'] = {
            'enabled': True,
            'global_settings': {},
            'per_model_settings': {}
        }
    
    # Update global settings
    current['tts']['global_settings'] = {
        'rate': payload.rate,
        'pitch': payload.pitch,
        'volume': payload.volume,
        'voice': payload.voice
    }
    current['tts']['enabled'] = payload.enabled
    
    # Save config
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=2)
    
    # Reload config
    _app_cfg = Config.load(CONFIG_PATH)
    
    return TTSSettingsOut(settings=current['tts'])

@app.get("/tts/settings/{model_name}")
async def get_model_tts_settings(model_name: str):
    """Get TTS settings for a specific model"""
    tts_config = _app_cfg.to_json().get('tts', {})
    model_settings = tts_config.get('per_model_settings', {}).get(model_name, 
        tts_config.get('global_settings', {
            'rate': 1.0,
            'pitch': 1.0,
            'volume': 0.8,
            'voice': None,
            'enabled': True
        })
    )
    return TTSSettingsOut(settings=model_settings)

@app.post("/tts/settings/{model_name}")
async def update_model_tts_settings(model_name: str, payload: TTSSettingsIn, current_user: dict = Depends(get_current_user)):
    """Update TTS settings for a specific model"""
    global _app_cfg
    
    # Load current config
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        current = json.load(f)
    
    # Ensure tts section exists
    if 'tts' not in current:
        current['tts'] = {
            'enabled': True,
            'global_settings': {},
            'per_model_settings': {}
        }
    
    if 'per_model_settings' not in current['tts']:
        current['tts']['per_model_settings'] = {}
    
    # Update model-specific settings
    current['tts']['per_model_settings'][model_name] = {
        'enabled': payload.enabled,
        'rate': payload.rate,
        'pitch': payload.pitch,
        'volume': payload.volume,
        'voice': payload.voice
    }
    
    # Save config
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=2)
    
    # Reload config
    _app_cfg = Config.load(CONFIG_PATH)
    
    return TTSSettingsOut(settings=current['tts']['per_model_settings'][model_name])

@app.get("/collaboration/files")
async def get_collaboration_files():
    """Get all collaboration files for all models with status and errors"""
    response = {}
    base_collab_dir = _app_cfg.collaboration.get('base_directory', './collaboration')
    
    for model_name, model_config in _app_cfg.models.items():
        # Get model validation status
        validation_errors = validate_model_config(model_name, model_config)
        model_status = {
            'enabled': model_config.get('enabled', False),
            'status': 'ready' if not validation_errors else 'error',
            'errors': validation_errors,
            'provider': model_config.get('provider'),
            'model': model_config.get('model'),
            'collaboration_enabled': model_config.get('collaboration_enabled', True)
        }
        
        # Get collaboration files
        model_files = []
        if model_config.get('collaboration_enabled', True):
            model_dir = model_config.get('collaboration_directory', f'{base_collab_dir}/{model_name}')
            if os.path.exists(model_dir):
                for filename in os.listdir(model_dir):
                    filepath = os.path.join(model_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        file_info = {
                            'name': filename,
                            'size': stat.st_size,
                            'modified': stat.st_mtime
                        }
                        
                        # Determine file type and priority (supports JSON and legacy TXT)
                        fname = filename.lower()
                        ftype = 'unknown'
                        priority = 'low'
                        if fname.endswith('.json') or fname.endswith('.txt'):
                            if '_error.' in fname:
                                ftype, priority = 'error', 'high'
                            elif '_proposal.' in fname:
                                ftype, priority = 'proposal', 'medium'
                            elif '_refinement.' in fname:
                                ftype, priority = 'refinement', 'medium'
                            elif '_vote.' in fname:
                                ftype, priority = 'vote', 'low'
                        file_info['type'] = ftype
                        file_info['priority'] = priority
                        
                        model_files.append(file_info)
                
                # Sort files by priority (errors first) and then by modification time
                priority_order = {'high': 0, 'medium': 1, 'low': 2}
                model_files.sort(key=lambda x: (priority_order.get(x['priority'], 3), -x['modified']))
        
        response[model_name] = {
            'status': model_status,
            'files': model_files
        }
    return response

@app.get("/collaboration/files/{model_name}/{filename}")
async def get_collaboration_file_content(model_name: str, filename: str):
    """Get content of a specific collaboration file"""
    model_config = _app_cfg.models.get(model_name)
    if not model_config:
        raise HTTPException(404, f"Model {model_name} not found")
    
    base_collab_dir = _app_cfg.collaboration.get('base_directory', './collaboration')
    model_dir = model_config.get('collaboration_directory', f'{base_collab_dir}/{model_name}')
    filepath = os.path.join(model_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(404, f"File {filename} not found for model {model_name}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {str(e)}")

@app.get("/api/collaboration/head")
async def get_collaboration_head(slot: str, n: int = 1):
    """Get recent collaboration data for a specific LLM slot"""
    try:
        # Map slot names to model names  
        model_name = slot
        if slot.startswith('slot_'):
            # Handle slot_1, slot_2, etc.
            slot_num = slot.split('_')[1]
            model_name = f"slot_{slot_num}"
        
        # Check if model exists in config
        if model_name not in _app_cfg.models:
            return {"items": []}
        
        model_config = _app_cfg.models[model_name]
        if not model_config.get('enabled', False):
            return {"items": []}
        
        # Get active sessions and find latest content for this model
        active_sessions = _collab_mgr.get_active_sessions() if hasattr(_collab_mgr, 'get_active_sessions') else []
        items = []
        
        # Check active session data first
        for session in active_sessions:
            slot_results = session.get('results', {}).get(model_name, {})
            if slot_results:
                # Get the latest output (refinement > proposal > vote)
                latest_content = None
                if 'latest_output' in slot_results:
                    latest_content = slot_results['latest_output']
                elif 'proposal' in slot_results:
                    latest_content = slot_results['proposal']
                elif 'vote' in slot_results:
                    latest_content = slot_results['vote']
                
                if latest_content:
                    items.append({
                        'text': latest_content,
                        'timestamp': session.get('started_ts', time.time()),
                        'session_id': session.get('id', ''),
                        'source': 'active_session'
                    })
        
        # If no active session data, check collaboration files
        if not items:
            base_collab_dir = _app_cfg.collaboration.get('base_directory', './collaboration')
            
            # Check both main collaboration folder and model-specific folder
            file_locations = [
                base_collab_dir,  # Main folder with session_id_model_phase.txt format
                model_config.get('collaboration_directory', f'{base_collab_dir}/{model_name}')  # Model folder
            ]
            
            for location in file_locations:
                if os.path.exists(location):
                    files = []
                    for filename in os.listdir(location):
                        if model_name in filename or (location.endswith(model_name) and filename.endswith(('.json', '.txt'))):
                            filepath = os.path.join(location, filename)
                            if os.path.isfile(filepath):
                                files.append((filepath, os.path.getmtime(filepath)))
                    
                    # Sort by modification time (newest first) and take top n
                    files.sort(key=lambda x: x[1], reverse=True)
                    for filepath, mtime in files[:n]:
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Handle both JSON and TXT formats
                            text_content = content
                            if filepath.endswith('.json'):
                                try:
                                    json_data = json.loads(content)
                                    text_content = json_data.get('content', content)
                                except:
                                    text_content = content
                            else:
                                # For .txt files, extract the content after the header
                                lines = content.split('\n')
                                content_start = -1
                                for i, line in enumerate(lines):
                                    if '=====' in line:
                                        content_start = i + 1
                                        break
                                if content_start > 0:
                                    text_content = '\n'.join(lines[content_start:])
                            
                            items.append({
                                'text': text_content,
                                'timestamp': mtime,
                                'filename': os.path.basename(filepath),
                                'source': 'file'
                            })
                        except Exception as e:
                            continue
                    
                    if items:
                        break
        
        # Limit results to n items
        items = items[:n]
        
        return {"items": items}
        
    except Exception as e:
        return {"items": [], "error": str(e)}

@app.post("/api/collaboration/input/{slot}")
async def send_input_to_slot(slot: str, message: dict):
    """Send user input directly to a specific LLM slot"""
    try:
        user_message = message.get('message', '')
        if not user_message:
            raise HTTPException(400, "Message content is required")
        
        # Map slot to model name
        model_name = slot
        if slot.startswith('slot_'):
            model_name = slot
        
        # Check if model exists and is enabled
        if model_name not in _app_cfg.models:
            raise HTTPException(404, f"Model {model_name} not found")
        
        model_config = _app_cfg.models[model_name]
        if not model_config.get('enabled', False):
            raise HTTPException(400, f"Model {model_name} is not enabled")
        
        # Create a direct chat with the LLM (bypass collaboration for direct user input)
        try:
            # Attempt relative import first.  When this module is executed as part of the
            # ``backend`` package, ``__package__`` is set and this will succeed.
            from .dexter_brain.llm import call_slot
        except ImportError:
            # Fallback for execution contexts where ``__package__`` is not set or relative
            # imports are not allowed.  Import the fully qualified name via the
            # ``backend`` package rather than ``dexter_brain`` to avoid ``ModuleNotFoundError``.
            from backend.dexter_brain.llm import call_slot
        response = await call_slot(_app_cfg, model_name, user_message)
        
        # Also write this interaction to collaboration files for visibility
        session_id = f"user_input_{int(time.time())}"
        await _collab_mgr._write_collaboration_file(session_id, model_name, "user_response", response)
        
        return {
            "success": True,
            "model": model_name,
            "response": response,
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
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

@app.post("/models/{model_name}/config")
async def update_model_config(model_name: str, payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Update configuration for a specific model (authenticated)"""
    global _app_cfg, _collab_mgr
    
    # Load current config
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        current = json.load(f)
    
    # Ensure models section exists
    if 'models' not in current:
        current['models'] = {}
    
    # Update the specific model
    current['models'][model_name] = payload
    
    # Save config
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=2)
    
    # Reload config and managers
    _app_cfg = Config.load(CONFIG_PATH)
    _collab_mgr = CollaborationManager(_app_cfg)
    
    return {"message": f"Model {model_name} configuration updated", "config": payload}

@app.post("/system/models/{model_name}/config")
async def update_model_config_system(model_name: str, payload: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Update configuration for a specific model (system access, no auth required)"""
    global _app_cfg, _collab_mgr
    
    # Load current config
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        current = json.load(f)
    
    # Ensure models section exists
    if 'models' not in current:
        current['models'] = {}
    
    # Update the specific model
    current['models'][model_name] = payload
    
    # Save config
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=2)
    
    # Reload config and managers
    _app_cfg = Config.load(CONFIG_PATH)
    _collab_mgr = CollaborationManager(_app_cfg)
    
    return {"message": f"Model {model_name} configuration updated", "config": payload}

@app.get("/models")
async def get_models():
    """Get all model configurations with validation status"""
    models_list = []
    for name, config in _app_cfg.models.items():
        # Validate model configuration
        validation_errors = validate_model_config(name, config)
        
        models_list.append({
            "name": name,
            "enabled": config.get("enabled", False),
            "provider": config.get("provider", ""),
            "model": config.get("model", ""),
            "role": config.get("role", ""),
            "identity": config.get("identity", ""),
            "local_model": config.get("local_model", False),
            "collaboration_enabled": config.get("collaboration_enabled", True),
            "endpoint": config.get("endpoint", ""),
            "api_key_env": config.get("api_key_env", ""),
            "validation_errors": validation_errors,
            "status": "error" if validation_errors else ("active" if config.get("enabled") else "disabled")
        })
    return {"models": models_list}

def validate_model_config(name: str, config: Dict[str, Any]) -> List[str]:
    """Validate a model configuration and return list of errors"""
    errors = []
    
    if not config.get("enabled"):
        return errors  # Don't validate disabled models
    
    if not config.get("provider"):
        errors.append("No provider specified")
    
    if not config.get("model"):
        errors.append("No model name specified")
    
    if not config.get("endpoint") and not config.get("local_model"):
        errors.append("No endpoint URL specified for remote model")
    
    if not config.get("api_key_env") and not config.get("local_model"):
        errors.append("No API key environment variable specified for remote model")
    
    # Check if API key environment variable exists
    api_key_env = config.get("api_key_env")
    if api_key_env and not config.get("local_model"):
        if not os.environ.get(api_key_env):
            errors.append(f"Environment variable '{api_key_env}' not set")
    
    return errors

@app.get("/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    """Get chat history - placeholder implementation"""
    # TODO: Implement actual chat history storage/retrieval
    return {"interactions": []}

# Helper functions
def _build_memory_context(user_input: str) -> str:
    """Assemble memory snippets from LTM (semantic) and STM (recent) for prompt context."""
    if _db is None:
        return ""
    try:
        # Semantic search across memories, prefer LTM
        candidates = _db.search_memories(user_input, limit=10)
        ltm = [m for m in candidates if (m.get('type') == 'ltm')][:5]
        # Recent STM by recency
        stm = _db.get_memories('stm', limit=5)

        def fmt(m):
            txt = (m.get('content') or '').strip().replace('\r', '')
            return txt[:500]

        parts: List[str] = []
        if ltm:
            parts.append("Relevant long-term memories:\n" + "\n".join(f"- {fmt(m)}" for m in ltm))
        if stm:
            parts.append("Recent short-term context:\n" + "\n".join(f"- {fmt(m)}" for m in stm))
        return "\n\n".join(parts)
    except Exception:
        return ""

async def _get_dexter_response(user_input: str) -> str:
    """Get Dexter's immediate response"""
    try:
        from .dexter_brain.llm import call_slot
        # Prepend memory context if available
        mem_ctx = _build_memory_context(user_input)
        prompt = f"{mem_ctx}\n\nUser: {user_input}" if mem_ctx else user_input
        response = await call_slot(_app_cfg, 'dexter', prompt)
        return response
    except Exception as e:
        # If we can't call Dexter, return an error message instead of fake data
        raise Exception(f"Failed to communicate with Dexter: {str(e)}")

# NEW: Detect poem-to-desktop intent
_def_poem_marker = object()

def _is_poem_desktop_request(text: str) -> bool:
    t = text.lower()
    return ('poem' in t or 'poetry' in t) and 'desktop' in t and ('write' in t or 'save' in t or 'create' in t)

def _generate_poem_skill_code(user_request: str) -> str:
    """Generate safe poem skill code; writes to Desktop if it exists, otherwise to generated_poems folder."""
    import re as _re
    snippet = _re.sub(r'[^a-zA-Z0-9 .,!?-]', ' ', user_request)[:120]
    return f'''import os, time, re

def run(message: str) -> dict:
    """Auto-generated poem writer skill derived from: {snippet}"""
    # Try desktop first, fallback to local folder
    user_home = os.path.expanduser('~')
    desktop_candidate = os.path.join(user_home, 'Desktop')
    desktop_dir = desktop_candidate if os.path.isdir(desktop_candidate) else None
    target_dir = desktop_dir or os.path.join(os.getcwd(), 'generated_poems')
    os.makedirs(target_dir, exist_ok=True)
    
    base_lines = [
        'Whispers of circuits awake in the night',
        'Patterned reflections in cold phosphor light',
        'Silent intentions assemble a theme',
        'Turning a prompt into structured dream'
    ]
    cleaned = re.sub(r'[^\\w .,!?-]', ' ', message)[:120]
    if cleaned:
        base_lines.append(f'Inspired by: {{cleaned}}')
    
    poem = "\\n".join(base_lines)[:1000]
    ts = int(time.time())
    filename = f'poem_{{ts}}.txt'
    file_path = os.path.join(target_dir, filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(poem + '\\n')
    
    return {{
        'success': True,
        'skill_name': 'poem_writer',
        'desktop_write': bool(desktop_dir),
        'file_path': file_path,
        'lines': len(base_lines),
        'poem_content': poem
    }}
'''

def _extract_python_code(text: str) -> str:
    """Extract Python code from markdown or mixed content"""
    import re
    
    # Try to find code blocks first
    code_block_pattern = r'```(?:python)?\s*\n(.*?)\n```'
    matches = re.findall(code_block_pattern, text, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    
    # If no code blocks, look for function definitions
    if 'def ' in text:
        lines = text.split('\n')
        in_function = False
        code_lines = []
        indent_level = 0
        
        for line in lines:
            if line.strip().startswith('def '):
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                code_lines.append(line)
            elif in_function:
                if line.strip() == '' or (line.startswith(' ' * indent_level) and len(line) > indent_level):
                    code_lines.append(line)
                else:
                    break
        
        if code_lines:
            return '\n'.join(code_lines)
    
    # Fallback: return text as-is if it looks like code
    if any(keyword in text for keyword in ['def ', 'import ', 'return ', 'if ', 'for ']):
        return text
    
    return ""

def _indent_code(code: str, spaces: int) -> str:
    """Indent code by specified number of spaces"""
    if not code:
        return ""
    
    lines = code.split('\n')
    indent = ' ' * spaces
    return '\n'.join(indent + line if line.strip() else line for line in lines)

async def _test_skill_in_sandbox(skill_file_path: str, user_request: str) -> Dict[str, Any]:
    """Test skill in sandbox environment"""
    try:
        from .dexter_brain.sandbox import create_sandbox
        
        # Read the skill code
        with open(skill_file_path, 'r', encoding='utf-8') as f:
            skill_code = f.read()
        
        # Create sandbox instance
        sandbox = create_sandbox(_app_cfg.to_json())
        
        # Test the skill
        result = await sandbox.execute_skill(skill_code, user_request)
        
        return {
            'success': result.get('success', False),
            'output': result.get('output', ''),
            'error': result.get('error'),
            'execution_time': result.get('execution_time', 0),
            'sandbox_type': result.get('sandbox_type', 'unknown')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Sandbox testing failed: {str(e)}",
            'execution_time': 0
        }

async def _create_and_test_skill(user_request: str, solution_content: str) -> Dict[str, Any]:
    """Create and test skill based on solution"""
    import tempfile
    import shutil
    import re
    
    try:
        poem_mode = _is_poem_desktop_request(user_request)
        # Generate skill name early
        base_prefix = 'poem' if poem_mode else 'skill'
        skill_name = f"{base_prefix}_{int(time.time())}"
        
        # If poem-to-desktop request, bypass LLM code extraction and use template
        if poem_mode:
            python_code = _generate_poem_skill_code(user_request)
        else:
            # Extract Python code from solution if it contains markup
            python_code = _extract_python_code(solution_content)
            if not python_code:
                python_code = solution_content
            # Ensure the code has a run function
            if 'def run(' not in python_code:
                python_code = f'''def run(message: str) -> dict:\n    """Generated skill from: {user_request[:100]}"""\n    try:\n        # User's solution:\n{_indent_code(python_code, 8)}\n        \n        return {{\n            "success": True,\n            "result": "Skill executed successfully",\n            "skill_name": "{skill_name}"\n        }}\n    except Exception as e:\n        return {{\n            "success": False,\n            "error": str(e),\n            "skill_name": "{skill_name}"\n        }}\n'''
        
        # Optional retry loop (simple) for non-poem skills if sandbox fails due to syntax
        MAX_ATTEMPTS = 2 if not poem_mode else 1
        last_test_result: Dict[str, Any] = {}
        for attempt in range(1, MAX_ATTEMPTS+1):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = os.path.join(temp_dir, f"{skill_name}.py")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(python_code)
                last_test_result = await _test_skill_in_sandbox(temp_file, user_request)
            if last_test_result.get('success'):  # passed sandbox
                break
                
        if last_test_result.get('success', False):
            auto_promote = _app_cfg.runtime.get('sandbox', {}).get('auto_promote_skills', True)
            promoted = False
            executed_result = None
            if auto_promote and _skills_mgr:
                success = _skills_mgr.add_skill_file(skill_name, python_code)
                if success:
                    _skills_mgr.reload_skills()
                    promoted = True
                    if poem_mode:
                        executed_result = _skills_mgr.execute_skill_by_name(skill_name, user_request)
            return {
                'ok': True,
                'skill_name': skill_name,
                'tested_in_vm': True,
                'promoted': promoted,
                'solution_used': (solution_content[:100] + '...') if solution_content else ('poem_template' if poem_mode else ''),
                'test_result': last_test_result,
                'executed_result': executed_result
            }
        else:
            return {
                'ok': False,
                'skill_name': skill_name,
                'tested_in_vm': True,
                'promoted': False,
                'error': last_test_result.get('error', 'Skill testing failed'),
                'solution_used': (solution_content[:100] + '...') if solution_content else ''
            }
                
    except Exception as e:
        return {
            'ok': False,
            'skill_name': f"skill_{int(time.time())}",
            'tested_in_vm': False,
            'promoted': False,
            'error': str(e),
            'solution_used': solution_content[:100] + '...'
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

# NEW: Sandbox settings model
class SandboxSettingsIn(BaseModel):
    provider: Optional[str] = None
    auto_promote: Optional[bool] = None

@app.post("/sandbox/settings")
async def update_sandbox_settings(payload: SandboxSettingsIn, current_user: dict = Depends(get_current_user)):
    """Update sandbox runtime settings (provider, auto promotion)."""
    global _app_cfg
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        current = json.load(f)
    rt = current.setdefault('runtime', {})
    sb = rt.setdefault('sandbox', {})
    if payload.provider:
        sb['provider'] = payload.provider
    if payload.auto_promote is not None:
        sb['auto_promote_skills'] = payload.auto_promote
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=2)
    _app_cfg = Config.load(CONFIG_PATH)
    return {"ok": True, "sandbox": sb}
