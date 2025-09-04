"""Error healing system with LLM collaboration and voting."""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from .error_tracker import ErrorTracker, SystemError, ErrorSeverity
from .collaboration import CollaborationManager
from .llm import call_slot


class ErrorHealer:
    """Intelligent error healing system using LLM collaboration."""
    
    def __init__(self, config, error_tracker: ErrorTracker, collaboration_manager: CollaborationManager):
        self.config = config
        self.error_tracker = error_tracker
        self.collaboration_manager = collaboration_manager
        self.healing_sessions: Dict[str, str] = {}  # error_id -> session_id
        self.active_healing: Dict[str, bool] = {}  # error_id -> active status
        self.healing_cooldown: Dict[str, float] = {}  # error_id -> last_attempt_time
        
        # Configuration
        self.max_healing_attempts = 3
        self.healing_cooldown_seconds = 300  # 5 minutes
        self.monitoring_interval = 30  # Check every 30 seconds
        
    async def start_error_monitoring(self):
        """Start continuous error monitoring and healing."""
        print("🔧 Starting error monitoring and healing system...")
        
        while True:
            try:
                await self._check_and_heal_errors()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                print(f"❌ Error in error monitoring: {e}")
                # Log the error monitoring error (meta!)
                self.error_tracker.log_error(
                    "ERROR_MONITORING_FAILED",
                    str(e),
                    ErrorSeverity.HIGH,
                    "error_healer"
                )
                await asyncio.sleep(60)  # Wait longer if monitoring fails
    
    async def _check_and_heal_errors(self):
        """Check for errors and trigger healing if needed."""
        # Get recent critical and high severity errors
        critical_errors = self.error_tracker.get_critical_errors()
        recent_errors = self.error_tracker.get_recent_errors(since_minutes=2)
        
        # Filter errors that need healing
        errors_to_heal = []
        
        for error in critical_errors:
            if self._should_heal_error(error):
                errors_to_heal.append(error)
        
        for error in recent_errors:
            if (error.severity in [ErrorSeverity.HIGH, ErrorSeverity.MEDIUM] and 
                self._should_heal_error(error)):
                errors_to_heal.append(error)
        
        # Trigger healing for each eligible error
        for error in errors_to_heal:
            if error.id not in self.active_healing:
                await self._initiate_healing_session(error)
    
    def _should_heal_error(self, error: SystemError) -> bool:
        """Determine if an error should be healed."""
        # Check if already resolved
        if error.resolved:
            return False
        
        # Check attempt limit
        if error.resolution_attempts >= self.max_healing_attempts:
            return False
        
        # Check cooldown
        if error.id in self.healing_cooldown:
            time_since_last = time.time() - self.healing_cooldown[error.id]
            if time_since_last < self.healing_cooldown_seconds:
                return False
        
        # Check if already being healed
        if self.active_healing.get(error.id, False):
            return False
        
        return True
    
    async def _initiate_healing_session(self, error: SystemError):
        """Start a collaborative healing session for an error."""
        session_id = f"heal_{error.id}_{int(time.time())}"
        self.healing_sessions[error.id] = session_id
        self.active_healing[error.id] = True
        self.healing_cooldown[error.id] = time.time()
        
        # Increment healing attempts
        self.error_tracker.increment_healing_attempts(error.id)
        
        # Create detailed error context for LLMs
        healing_prompt = self._create_healing_prompt(error)
        
        print(f"\n🚨 INITIATING ERROR HEALING SESSION: {session_id}")
        print(f"Error: {error.error_type} - {error.message[:100]}...")
        print(f"Severity: {error.severity.value} | Source: {error.source}")
        
        try:
            # Broadcast to LLM team for collaborative healing
            collab_session = await self.collaboration_manager.broadcast_user_input(
                healing_prompt, session_id
            )
            
            # Wait for collaboration to complete
            healing_complete = await self.collaboration_manager.wait_for_collaboration_complete(
                collab_session, timeout=90.0  # Longer timeout for complex healing
            )
            
            if healing_complete:
                await self._process_healing_results(error, collab_session)
            else:
                print(f"⚠️ Healing session timed out for error {error.id}")
                self.error_tracker.log_error(
                    "HEALING_TIMEOUT",
                    f"Healing session timed out for error {error.id}",
                    ErrorSeverity.MEDIUM,
                    "error_healer",
                    {"original_error_id": error.id, "session_id": session_id}
                )
                
        except Exception as e:
            print(f"❌ Healing session failed for error {error.id}: {e}")
            self.error_tracker.log_error(
                "HEALING_FAILED",
                f"Healing session failed: {e}",
                ErrorSeverity.HIGH,
                "error_healer",
                {"original_error_id": error.id, "session_id": session_id}
            )
        finally:
            # Clean up
            self.active_healing[error.id] = False
    
    def _create_healing_prompt(self, error: SystemError) -> str:
        """Create a detailed prompt for LLM healing collaboration."""
        # Format error context nicely
        context_str = json.dumps(error.context, indent=2) if error.context else "No context available"
        
        # Get related errors for context
        related_errors = self.error_tracker.get_errors_by_type(error.error_type, unresolved_only=True)
        related_count = len(related_errors)
        
        # Get error statistics
        stats = self.error_tracker.get_error_statistics()
        
        return f"""🚨 SYSTEM ERROR DETECTED - HEALING MODE ACTIVATED

=== ERROR DETAILS ===
ID: {error.id}
Type: {error.error_type}
Severity: {error.severity.value.upper()}
Source: {error.source}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(error.timestamp))}
Attempts: {error.resolution_attempts}/{self.max_healing_attempts}

=== ERROR MESSAGE ===
{error.message}

=== CONTEXT ===
{context_str}

=== STACK TRACE ===
{error.stack_trace or 'Not available'}

=== SYSTEM STATUS ===
Recent Errors: {stats['recent_errors']}
Critical Errors: {stats['critical_errors']}
Related '{error.error_type}' Errors: {related_count}

=== MISSION ===
Collaborate to diagnose and provide healing solutions for this system error.
Focus on root cause analysis and practical, implementable solutions.

=== ANALYSIS REQUIRED ===
1. **Root Cause**: What is the underlying cause of this error?
2. **Immediate Action**: What can be done RIGHT NOW to mitigate the issue?
3. **Permanent Fix**: What long-term solution will prevent recurrence?
4. **Prevention**: How can we detect and prevent similar errors?
5. **Risk Assessment**: What are the risks of the proposed solutions?

=== RESPONSE FORMAT ===
Analysis: [Your detailed diagnosis of the root cause]
Immediate_Action: [Specific steps to take immediately - be concrete and actionable]
Permanent_Fix: [Long-term solution with implementation details]
Prevention: [Monitoring, alerts, or code changes to prevent recurrence]
Risk_Level: [LOW/MEDIUM/HIGH - risk of implementing your solution]
Confidence: [LOW/MEDIUM/HIGH - your confidence in this solution]

=== SPECIAL CONSIDERATIONS ===
- Prioritize solutions that won't disrupt ongoing operations
- Consider the error's source system: {error.source}
- Factor in system load and available resources
- Provide specific implementation steps where possible

Remember: System stability and user experience depend on rapid, accurate error resolution.
Vote for the solution that best balances effectiveness, safety, and implementability."""
    
    async def _process_healing_results(self, error: SystemError, session_id: str):
        """Process the healing recommendations from LLM collaboration."""
        try:
            # Get collaboration results
            winning_solution = self.collaboration_manager.get_winning_solution(session_id)
            
            if winning_solution:
                solution_content = winning_solution.get('solution', '')
                winner_name = winning_solution.get('winner', 'unknown')
                vote_count = winning_solution.get('vote_count', 0)
                
                print(f"✅ HEALING SOLUTION IDENTIFIED for {error.id}")
                print(f"Winner: {winner_name} (votes: {vote_count})")
                print(f"Solution preview: {solution_content[:200]}...")
                
                # Parse the solution for actionable items
                healing_actions = self._parse_healing_solution(solution_content)
                
                # Execute safe healing actions if possible
                execution_result = await self._execute_safe_healing_actions(error, healing_actions)
                
                # Log the healing attempt
                self.error_tracker.log_error(
                    "HEALING_COMPLETED",
                    f"LLM healing session completed for {error.error_type}",
                    ErrorSeverity.LOW,
                    "error_healer",
                    {
                        "original_error_id": error.id,
                        "healing_solution": solution_content,
                        "session_id": session_id,
                        "winner": winner_name,
                        "vote_count": vote_count,
                        "actions_executed": execution_result.get('actions_executed', []),
                        "execution_success": execution_result.get('success', False)
                    },
                    auto_capture_traceback=False
                )
                
                # If healing was successful, mark original error as resolved
                if execution_result.get('success', False):
                    self.error_tracker.mark_resolved(error.id, session_id)
                    print(f"🎉 Error {error.id} marked as RESOLVED!")
                
            else:
                print(f"❌ No healing solution consensus reached for error {error.id}")
                self.error_tracker.log_error(
                    "HEALING_NO_CONSENSUS",
                    f"No healing consensus reached for error {error.id}",
                    ErrorSeverity.MEDIUM,
                    "error_healer",
                    {"original_error_id": error.id, "session_id": session_id},
                    auto_capture_traceback=False
                )
                
        except Exception as e:
            print(f"❌ Error processing healing results for {error.id}: {e}")
            self.error_tracker.log_error(
                "HEALING_PROCESSING_FAILED",
                f"Failed to process healing results: {e}",
                ErrorSeverity.HIGH,
                "error_healer",
                {"original_error_id": error.id, "session_id": session_id}
            )
    
    def _parse_healing_solution(self, solution: str) -> Dict[str, str]:
        """Parse structured healing solution from LLM response."""
        sections = {}
        current_section = None
        current_content = []
        
        lines = solution.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check if this line starts a new section
            section_markers = [
                'analysis:', 'immediate_action:', 'permanent_fix:', 
                'prevention:', 'risk_level:', 'confidence:'
            ]
            
            line_lower = line.lower()
            found_section = None
            
            for marker in section_markers:
                if line_lower.startswith(marker):
                    found_section = marker.replace(':', '')
                    break
            
            if found_section:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = ' '.join(current_content).strip()
                
                # Start new section
                current_section = found_section
                current_content = [line[len(found_section) + 1:].strip()]
            elif current_section and line:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = ' '.join(current_content).strip()
        
        return sections
    
    async def _execute_safe_healing_actions(self, error: SystemError, healing_actions: Dict[str, str]) -> Dict[str, Any]:
        """Execute safe, non-destructive healing actions."""
        immediate_action = healing_actions.get('immediate_action', '').lower()
        risk_level = healing_actions.get('risk_level', 'HIGH').upper()
        
        execution_result = {
            "success": False,
            "actions_executed": [],
            "actions_skipped": [],
            "risk_level": risk_level
        }
        
        # Only execute LOW risk actions automatically
        if risk_level != 'LOW':
            execution_result["actions_skipped"].append(f"Skipped due to {risk_level} risk level")
            print(f"⚠️ Skipping automatic healing - Risk level: {risk_level}")
            return execution_result
        
        # Define safe actions that can be executed automatically
        safe_actions = {
            'restart_service': self._safe_restart_service,
            'clear_cache': self._safe_clear_cache,
            'reset_connection': self._safe_reset_connection,
            'increase_timeout': self._safe_increase_timeout,
            'cleanup_temp': self._safe_cleanup_temp,
            'log_rotation': self._safe_log_rotation
        }
        
        executed_actions = []
        
        for action_keyword, action_func in safe_actions.items():
            if action_keyword in immediate_action:
                try:
                    result = await action_func(error, healing_actions)
                    if result.get('success', False):
                        executed_actions.append(action_keyword)
                        print(f"✅ Executed healing action: {action_keyword}")
                    else:
                        execution_result["actions_skipped"].append(f"{action_keyword}: {result.get('reason', 'Unknown')}")
                except Exception as e:
                    print(f"❌ Failed to execute {action_keyword}: {e}")
                    execution_result["actions_skipped"].append(f"{action_keyword}: {str(e)}")
        
        execution_result["actions_executed"] = executed_actions
        execution_result["success"] = len(executed_actions) > 0
        
        return execution_result
    
    # Safe healing action implementations
    async def _safe_restart_service(self, error: SystemError, actions: Dict[str, str]) -> Dict[str, Any]:
        """Safely restart relevant service components (placeholder)."""
        # This would implement safe service restart logic
        return {"success": False, "reason": "Service restart not implemented"}
    
    async def _safe_clear_cache(self, error: SystemError, actions: Dict[str, str]) -> Dict[str, Any]:
        """Clear relevant caches safely."""
        # This would implement cache clearing logic
        return {"success": False, "reason": "Cache clearing not implemented"}
    
    async def _safe_reset_connection(self, error: SystemError, actions: Dict[str, str]) -> Dict[str, Any]:
        """Reset network/database connections safely."""
        # This would implement connection reset logic
        return {"success": False, "reason": "Connection reset not implemented"}
    
    async def _safe_increase_timeout(self, error: SystemError, actions: Dict[str, str]) -> Dict[str, Any]:
        """Temporarily increase timeout values."""
        # This would implement timeout adjustment logic
        return {"success": False, "reason": "Timeout adjustment not implemented"}
    
    async def _safe_cleanup_temp(self, error: SystemError, actions: Dict[str, str]) -> Dict[str, Any]:
        """Clean up temporary files and directories."""
        try:
            import tempfile
            import shutil
            from pathlib import Path
            
            # Clean up temp directories older than 1 hour
            temp_dir = Path(tempfile.gettempdir())
            cleaned_count = 0
            
            for item in temp_dir.iterdir():
                if item.name.startswith('dexter_') or item.name.startswith('execution_'):
                    try:
                        # Check if older than 1 hour
                        if time.time() - item.stat().st_mtime > 3600:
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                            cleaned_count += 1
                    except Exception:
                        pass  # Ignore individual cleanup failures
            
            return {"success": True, "cleaned_items": cleaned_count}
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    async def _safe_log_rotation(self, error: SystemError, actions: Dict[str, str]) -> Dict[str, Any]:
        """Rotate large log files safely."""
        # This would implement log rotation logic
        return {"success": False, "reason": "Log rotation not implemented"}
    
    def get_healing_statistics(self) -> Dict[str, Any]:
        """Get healing system statistics."""
        healing_errors = self.error_tracker.get_errors_by_source("error_healer", unresolved_only=False)
        
        return {
            "active_healing_sessions": len([k for k, v in self.active_healing.items() if v]),
            "total_healing_sessions": len(self.healing_sessions),
            "healing_errors": len(healing_errors),
            "errors_in_cooldown": len(self.healing_cooldown),
            "average_healing_attempts": self._calculate_average_healing_attempts()
        }
    
    def _calculate_average_healing_attempts(self) -> float:
        """Calculate average healing attempts across all errors."""
        errors_with_attempts = [e for e in self.error_tracker.errors if e.resolution_attempts > 0]
        if not errors_with_attempts:
            return 0.0
        
        total_attempts = sum(e.resolution_attempts for e in errors_with_attempts)
        return total_attempts / len(errors_with_attempts)