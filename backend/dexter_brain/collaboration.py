from __future__ import annotations
import asyncio
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Callable
from backend.dexter_brain.llm import call_slot
from backend.dexter_brain.events import emit

class CollaborationManager:
    def __init__(self, config, collaboration_folder: str | None = None):
        self.config = config
        # Use config.collaboration.base_directory by default
        base_dir = getattr(self.config, 'collaboration', {}).get('base_directory', './collaboration')
        self.collaboration_folder = collaboration_folder or base_dir
        self.active_sessions: Dict[str, Dict] = {}
        os.makedirs(self.collaboration_folder, exist_ok=True)
        
        # Ensure all model collaboration directories exist
        self.ensure_collaboration_directories()
        
    async def broadcast_user_input(self, user_input: str, session_id: str = None) -> str:
        """Immediately broadcast user input to all enabled LLMs"""
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        # Get all enabled LLMs except Dexter
        enabled_llms = [name for name, model in self.config.models.items() 
                       if model.get('enabled') and name != 'dexter']
        
        # Create collaboration session
        session = {
            "id": session_id,
            "user_input": user_input,
            "started_ts": time.time(),
            "llms": enabled_llms,
            "status": "active",
            "proposals": {},
            "votes": {},
            "consensus": None
        }
        self.active_sessions[session_id] = session
        
        # Emit collaboration start event
        await emit({
            "slot": "system", 
            "event": "collaboration.started", 
            "text": f"Started collaboration with {len(enabled_llms)} LLMs: {', '.join(enabled_llms)}",
            "session_id": session_id,
            "llms": enabled_llms
        })
        
        # Start all LLMs working in parallel
        tasks = []
        for llm_name in enabled_llms:
            # Emit LLM start event
            await emit({
                "slot": llm_name,
                "event": "llm.started", 
                "text": f"Starting work on: {user_input[:50]}...",
                "session_id": session_id
            })
            task = asyncio.create_task(self._llm_collaboration_worker(session_id, llm_name, user_input))
            tasks.append(task)
        
        # Let them work in background
        return session_id

    async def _llm_collaboration_worker(self, session_id: str, llm_name: str, user_input: str):
        """Background worker for individual LLM collaboration"""
        try:
            # Phase 1: Initial proposal
            await emit({
                "slot": llm_name,
                "event": "phase.proposal", 
                "text": "Creating initial proposal...",
                "session_id": session_id
            })
            
            proposal = await self._get_llm_proposal(llm_name, user_input, session_id)
            await self._write_collaboration_file(session_id, llm_name, "proposal", proposal)
            
            await emit({
                "slot": llm_name,
                "event": "proposal.completed", 
                "text": f"Proposal complete: {proposal[:60]}...",
                "session_id": session_id
            })
            
            # Phase 2: Read peers and refine
            await asyncio.sleep(2)  # Give others time to write proposals
            peer_proposals = await self._read_peer_proposals(session_id, llm_name)
            
            if peer_proposals:
                await emit({
                    "slot": llm_name,
                    "event": "phase.refinement", 
                    "text": f"Reading {len(peer_proposals)} peer proposals, refining...",
                    "session_id": session_id
                })
                
                refinement = await self._get_llm_refinement(llm_name, user_input, proposal, peer_proposals)
                await self._write_collaboration_file(session_id, llm_name, "refinement", refinement)
                
                await emit({
                    "slot": llm_name,
                    "event": "refinement.completed", 
                    "text": f"Refinement complete: {refinement[:60]}...",
                    "session_id": session_id
                })
            
            # Phase 3: Vote on best solution
            await asyncio.sleep(1)  # Give time for refinements
            await emit({
                "slot": llm_name,
                "event": "phase.voting", 
                "text": "Analyzing all solutions and voting...",
                "session_id": session_id
            })
            
            all_solutions = await self._read_all_solutions(session_id)
            vote = await self._get_llm_vote(llm_name, user_input, all_solutions)
            await self._write_collaboration_file(session_id, llm_name, "vote", vote)
            
            await emit({
                "slot": llm_name,
                "event": "vote.completed", 
                "text": f"Vote cast: {vote[:40]}...",
                "session_id": session_id
            })
            
        except Exception as e:
            await emit({
                "slot": llm_name,
                "event": "error", 
                "text": f"Error: {str(e)}",
                "session_id": session_id
            })
            await self._write_collaboration_file(session_id, llm_name, "error", str(e))

    async def _get_llm_proposal(self, llm_name: str, user_input: str, session_id: str) -> str:
        """Get initial proposal from LLM"""
        prompt = f"""User request: {user_input}

Collaboration Session ID: {session_id}

You are working with a team of LLMs to solve this request. Create your initial proposal:

1. Analyze the request
2. Propose a solution approach
3. If this requires a new skill, provide a SKILL_SPEC and code
4. Be concise but thorough

Format your response clearly with sections for Analysis, Approach, and Implementation."""
        
        return await call_slot(self.config, llm_name, prompt)

    async def _get_llm_refinement(self, llm_name: str, user_input: str, original_proposal: str, peer_proposals: List[Dict]) -> str:
        """Get refined proposal after reading peers"""
        peer_text = "\n\n".join([f"=== {p['llm']} ===\n{p['content']}" for p in peer_proposals])
        
        prompt = f"""User request: {user_input}

Your original proposal:
{original_proposal}

Peer proposals:
{peer_text}

After reviewing your peers' proposals, refine your solution. Consider:
1. What good ideas can you incorporate from peers?
2. What weaknesses do you see in other approaches?
3. How can you improve your original proposal?

Provide your refined solution:"""
        
        return await call_slot(self.config, llm_name, prompt)

    async def _get_llm_vote(self, llm_name: str, user_input: str, all_solutions: Dict[str, str]) -> str:
        """Get LLM's vote on best solution"""
        solutions_text = "\n\n".join([f"=== {llm} ===\n{content}" 
                                     for llm, content in all_solutions.items() 
                                     if llm != llm_name])
        
        prompt = f"""User request: {user_input}

All team solutions (including refinements):
{solutions_text}

Vote for the BEST solution (including your own if appropriate). Consider:
1. Correctness and safety
2. Completeness 
3. Code quality (if applicable)
4. Likelihood of success

Respond with just: VOTE: <llm_name>"""
        
        return await call_slot(self.config, llm_name, prompt)

    async def _write_collaboration_file(self, session_id: str, llm_name: str, phase: str, content: str):
        """Write LLM output to collaboration file as JSON in per-model directory"""
        # Resolve per-model directory from config
        base_dir = getattr(self.config, 'collaboration', {}).get('base_directory', './collaboration')
        model_cfg = self.config.models.get(llm_name, {})
        model_dir = model_cfg.get('collaboration_directory', f"{base_dir}/{llm_name}")
        os.makedirs(model_dir, exist_ok=True)
        
        # Build filename and JSON payload
        filename = f"{session_id}_{llm_name}_{phase}.json"
        file_path = os.path.join(model_dir, filename)
        payload = {
            "timestamp": time.time(),
            "llm": llm_name,
            "phase": phase,
            "session": session_id,
            "content": content,
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        # Update session
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if phase not in session:
                session[phase] = {}
            session[phase][llm_name] = content

    async def _read_peer_proposals(self, session_id: str, exclude_llm: str) -> List[Dict]:
        """Read proposals from peer LLMs"""
        proposals = []
        session = self.active_sessions.get(session_id, {})
        
        for llm_name, content in session.get("proposals", {}).items():
            if llm_name != exclude_llm:
                proposals.append({"llm": llm_name, "content": content})
        
        return proposals

    async def _read_all_solutions(self, session_id: str) -> Dict[str, str]:
        """Read all solutions (proposals + refinements) for voting"""
        solutions = {}
        session = self.active_sessions.get(session_id, {})
        
        # Start with proposals
        for llm_name, content in session.get("proposals", {}).items():
            solutions[llm_name] = content
        
        # Override with refinements if available
        for llm_name, content in session.get("refinements", {}).items():
            solutions[llm_name] = content
        
        return solutions

    def get_collaboration_results(self, session_id: str) -> Dict[str, Any]:
        """Get final collaboration results"""
        return self.active_sessions.get(session_id, {})

    def count_votes(self, session_id: str) -> Dict[str, int]:
        """Count votes and determine winner"""
        session = self.active_sessions.get(session_id, {})
        votes = session.get("votes", {})
        
        vote_counts = {}
        for voter, vote_content in votes.items():
            # Extract vote from content (looking for "VOTE: <name>")
            import re
            match = re.search(r"VOTE:\s*(\w+)", vote_content, re.IGNORECASE)
            if match:
                voted_for = match.group(1).lower()
                vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1
        
        return vote_counts

    def get_winning_solution(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the winning solution based on votes"""
        vote_counts = self.count_votes(session_id)
        if not vote_counts:
            return None
        
        winner = max(vote_counts.items(), key=lambda x: x[1])
        winner_name = winner[0]
        
        session = self.active_sessions.get(session_id, {})
        all_solutions = {}
        
        # Get final solutions (refinements preferred over proposals)
        for llm_name, content in session.get("proposals", {}).items():
            all_solutions[llm_name] = content
        for llm_name, content in session.get("refinements", {}).items():
            all_solutions[llm_name] = content
        
        winning_solution = all_solutions.get(winner_name)
        
        return {
            "winner": winner_name,
            "vote_count": winner[1],
            "total_votes": sum(vote_counts.values()),
            "solution": winning_solution,
            "all_vote_counts": vote_counts
        }

    async def wait_for_collaboration_complete(self, session_id: str, timeout: float = 30.0) -> bool:
        """Wait for collaboration to complete with timeout"""
        start_time = time.time()
        session = self.active_sessions.get(session_id, {})
        expected_llms = set(session.get("llms", []))
        
        while time.time() - start_time < timeout:
            # Check if all LLMs have voted
            votes = session.get("votes", {})
            if set(votes.keys()) >= expected_llms:
                return True
            
            await asyncio.sleep(0.5)
        
        return False  # Timeout

    def get_active_sessions(self) -> List[Dict]:
        """Get list of currently active collaboration sessions"""
        current_time = time.time()
        active = []
        
        for session_id, session in self.active_sessions.items():
            # Consider sessions active for up to 5 minutes
            if current_time - session.get("started_ts", 0) < 300:
                # Add participant information based on LLM names
                participants = []
                for llm_name in session.get("llms", []):
                    # Map LLM names to slot names
                    if llm_name.startswith('slot_') or llm_name.startswith('llm_'):
                        participants.append(llm_name)
                    else:
                        # Try to find a matching slot for named LLMs
                        for slot_name, config in self.config.models.items():
                            if config.get('identity', '') == llm_name or slot_name == llm_name:
                                participants.append(slot_name)
                                break
                
                session_copy = session.copy()
                session_copy['participants'] = participants
                session_copy['original_request'] = session.get('user_input', '')
                
                # Add latest results for each participant
                session_copy['results'] = {}
                for llm_name in session.get("llms", []):
                    slot_results = {}
                    if llm_name in session.get("proposals", {}):
                        slot_results['proposal'] = session["proposals"][llm_name]
                    if llm_name in session.get("refinements", {}):
                        slot_results['latest_output'] = session["refinements"][llm_name]
                    if llm_name in session.get("votes", {}):
                        slot_results['vote'] = session["votes"][llm_name]
                    
                    # Map to slot name
                    slot_name = llm_name
                    for sname, config in self.config.models.items():
                        if config.get('identity', '') == llm_name or sname == llm_name:
                            slot_name = sname
                            break
                    
                    if slot_results:
                        session_copy['results'][slot_name] = slot_results
                
                active.append(session_copy)
        
        return active

    def get_model_collaboration_files(self, model_name: str) -> List[Dict[str, Any]]:
        """Get all collaboration files for a specific model"""
        files = []
        model_config = self.config.models.get(model_name, {})
        
        if not model_config.get('collaboration_enabled', True):
            return files
        
        base_dir = self.config.collaboration.get('base_directory', './collaboration')
        model_dir = model_config.get('collaboration_directory', f'{base_dir}/{model_name}')
        
        if os.path.exists(model_dir):
            for filename in os.listdir(model_dir):
                filepath = os.path.join(model_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'path': filepath
                    })
        
        return sorted(files, key=lambda x: x['modified'], reverse=True)

    def read_collaboration_file(self, model_name: str, filename: str) -> str:
        """Read content of a specific collaboration file"""
        model_config = self.config.models.get(model_name, {})
        base_dir = self.config.collaboration.get('base_directory', './collaboration')
        model_dir = model_config.get('collaboration_directory', f'{base_dir}/{model_name}')
        filepath = os.path.join(model_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filename} not found for model {model_name}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Error reading file {filename}: {str(e)}")

    def write_model_collaboration_file(self, model_name: str, filename: str, content: str):
        """Write content to a model's collaboration file"""
        model_config = self.config.models.get(model_name, {})
        base_dir = self.config.collaboration.get('base_directory', './collaboration')
        model_dir = model_config.get('collaboration_directory', f'{base_dir}/{model_name}')
        
        # Ensure directory exists
        os.makedirs(model_dir, exist_ok=True)
        
        filepath = os.path.join(model_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Error writing file {filename}: {str(e)}")

    def get_all_collaboration_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get collaboration files for all models"""
        all_files = {}
        
        for model_name in self.config.models.keys():
            all_files[model_name] = self.get_model_collaboration_files(model_name)
        
        return all_files

    def ensure_collaboration_directories(self):
        """Ensure all model collaboration directories exist"""
        base_dir = self.config.collaboration.get('base_directory', './collaboration')
        
        for model_name, model_config in self.config.models.items():
            if model_config.get('collaboration_enabled', True):
                model_dir = model_config.get('collaboration_directory', f'{base_dir}/{model_name}')
                os.makedirs(model_dir, exist_ok=True)
