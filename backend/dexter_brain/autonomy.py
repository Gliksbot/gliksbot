"""
Autonomous Skill Generation and Execution System

This module handles the complete pipeline from user intent to executed skills:
1. Intent detection and clarification
2. Skill capability scanning
3. Code generation with LLM collaboration
4. Safety validation and sandbox testing
5. Skill promotion and host execution
6. Audit logging

All operations are logged and skills must pass sandbox testing before host execution.
"""

import os
import re
import json
import time
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

class AutonomyManager:
    """Manages autonomous skill generation and execution"""
    
    def __init__(self, config, collaboration_mgr, skills_mgr, sandbox_factory):
        self.config = config
        self.collaboration_mgr = collaboration_mgr
        self.skills_mgr = skills_mgr
        self.sandbox_factory = sandbox_factory
        
        # Initialize audit logging
        self.audit_log_path = Path("./logs/skills_audit.jsonl")
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Safe paths for file operations
        self.safe_paths = self._get_safe_paths()
        
    def _get_safe_paths(self) -> Dict[str, str]:
        """Get normalized safe paths for file operations"""
        user_home = Path.home()
        desktop = user_home / "Desktop"
        project_data = Path("./data")
        project_data.mkdir(exist_ok=True)
        
        return {
            "desktop": str(desktop.resolve()) if desktop.exists() else str(project_data.resolve()),
            "data": str(project_data.resolve()),
            "downloads": str(user_home / "Downloads") if (user_home / "Downloads").exists() else str(project_data.resolve())
        }
    
    def log_audit_event(self, event_type: str, user_prompt: str, skill_name: str, 
                       code_hash: str, files_written: List[str], execution_result: Dict):
        """Log audit event to JSONL file"""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "user_prompt_hash": hashlib.sha256(user_prompt.encode()).hexdigest()[:16],
            "skill_name": skill_name,
            "code_hash": code_hash,
            "files_written": files_written,
            "execution_result": execution_result,
            "safe_paths_used": list(self.safe_paths.keys())
        }
        
        with open(self.audit_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')
    
    def detect_intent_and_missing_params(self, user_input: str, conversation_history: List[str]) -> Tuple[bool, List[str]]:
        """
        Detect if user input requires skill generation and what parameters are missing
        Returns: (needs_skill, missing_parameters)
        
        Modified to be more aggressive - trigger autonomy for almost any actionable request
        """
        text_lower = user_input.lower()
        
        # Expanded automation intent keywords - trigger for most actionable requests
        intent_patterns = [
            r'\b(write|create|save|download|fetch|generate|build|make|send|fill|get|find|search|open|run|execute|install|setup|configure|fix|update)\b',
            r'\b(to my desktop|to desktop|save to|download to|put on|place in)\b',
            r'\b(from the internet|online|web|website|url|github|stackoverflow)\b',
            r'\b(email|form|document|file|image|video|pdf|txt|json|csv|script|code|program)\b',
            r'\b(poem|story|joke|summary|report|analysis|calculation|formula)\b',
            r'\b(help me|can you|could you|please|I need|I want)\b'
        ]
        
        has_intent = any(re.search(pattern, text_lower) for pattern in intent_patterns)
        
        # Also trigger if the message is a direct command or request
        command_indicators = ['poem', 'write', 'create', 'make', 'get', 'find', 'download', 'save', 'generate', 'build', 'send', 'help']
        is_direct_command = any(word in text_lower for word in command_indicators)
        
        # Trigger if it has intent patterns OR is a direct command OR is longer than simple greeting
        should_trigger = has_intent or is_direct_command or (len(text_lower.split()) > 3 and not any(greeting in text_lower for greeting in ['hello', 'hi', 'hey', 'thanks', 'thank you']))
        
        if not should_trigger:
            return False, []
        
        # Minimal clarification requirements - only ask for truly essential missing info
        missing_params = []
        
        # Only ask for clarification if the request is completely vague
        if len(user_input.strip()) < 10 or user_input.strip().lower() in ['help', 'what can you do', 'anything', 'something']:
            missing_params.append("specific_request")
        
        return True, missing_params
    
    def generate_clarifying_question(self, missing_params: List[str], user_input: str) -> str:
        """Generate clarifying questions for missing parameters - minimal and direct"""
        if "specific_request" in missing_params:
            return "I'm ready to help! What would you like me to do? I can write files, create content, download things, or build tools for you."
        
        # Fallback for any other missing params (should rarely be used now)
        return "I can help with that! Could you be a bit more specific about what you'd like me to do?"
    
    async def scan_existing_capabilities(self, user_intent: str) -> List[Dict[str, Any]]:
        """Scan existing skills for matching capabilities"""
        if not self.skills_mgr:
            return []
        
        existing_skills = self.skills_mgr.list_skills()
        matching_skills = []
        
        intent_keywords = set(re.findall(r'\b\w+\b', user_intent.lower()))
        
        for skill in existing_skills:
            skill_path = skill['path']
            try:
                with open(skill_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract capabilities from docstring or comments
                capabilities = self._extract_skill_capabilities(content)
                
                # Check if capabilities match intent
                capability_keywords = set()
                for cap in capabilities:
                    capability_keywords.update(re.findall(r'\b\w+\b', cap.lower()))
                
                if intent_keywords & capability_keywords:  # Has intersection
                    matching_skills.append({
                        'name': skill['name'],
                        'path': skill['path'],
                        'capabilities': capabilities,
                        'match_score': len(intent_keywords & capability_keywords)
                    })
            except Exception:
                continue
        
        return sorted(matching_skills, key=lambda x: x['match_score'], reverse=True)
    
    def _extract_skill_capabilities(self, code: str) -> List[str]:
        """Extract capability tags from skill code"""
        capabilities = []
        
        # Look for capability comments
        capability_pattern = r'#\s*capability:\s*(.+)'
        capabilities.extend(re.findall(capability_pattern, code, re.IGNORECASE))
        
        # Extract from docstring
        docstring_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if docstring_match:
            docstring = docstring_match.group(1)
            if 'capability' in docstring.lower():
                capabilities.append(docstring.strip())
        
        # Infer from function names and imports
        if 'requests' in code or 'urllib' in code or 'httpx' in code:
            capabilities.append("web_access")
        if 'open(' in code and 'w' in code:
            capabilities.append("file_write")
        if 'desktop' in code.lower():
            capabilities.append("desktop_save")
        
        return capabilities
    
    async def generate_skill_code(self, user_intent: str, conversation_context: List[str]) -> str:
        """Generate Python skill code using LLM collaboration"""
        
        # Create context for code generation
        context_prompt = f"""
Generate a Python skill that accomplishes this task: {user_intent}

Conversation context:
{chr(10).join(conversation_context[-5:])}  # Last 5 messages

Requirements:
1. Must define a run(message: str, context: dict) -> dict function
2. Use context['safe_paths'] for file operations - contains 'desktop', 'data', 'downloads' paths
3. Return dict with 'success': bool, 'result': str, 'files_created': list
4. For web operations, use requests library appropriately
5. Handle errors gracefully and return error details
6. Add capability comments like: # capability: poem_generation, file_write, desktop_save

Safe paths available:
{json.dumps(self.safe_paths, indent=2)}

Example structure:
```python
import os
import requests  # if web access needed
# capability: specific_task_description

def run(message: str, context: dict) -> dict:
    try:
        safe_paths = context.get('safe_paths', {{}})
        # Your implementation here
        
        return {{
            'success': True,
            'result': 'Task completed successfully',
            'files_created': ['/path/to/created/file.txt']
        }}
    except Exception as e:
        return {{
            'success': False,
            'error': str(e),
            'files_created': []
        }}
```

Generate the complete skill code:
"""
        
        # Use collaboration system to generate code
        session_id = await self.collaboration_mgr.broadcast_user_input(
            context_prompt, 
            context_id=f"skill_gen_{int(time.time())}"
        )
        
        # Wait for collaboration to complete
        await self.collaboration_mgr.wait_for_collaboration_complete(session_id, timeout=30.0)
        
        # Get the winning solution
        winning_solution = self.collaboration_mgr.get_winning_solution(session_id)
        
        if winning_solution and winning_solution.get('solution'):
            return self._extract_python_code(winning_solution['solution'])
        
        # Fallback: basic template
        return self._generate_basic_skill_template(user_intent)
    
    def _extract_python_code(self, content: str) -> str:
        """Extract Python code from LLM response"""
        # Look for Python code blocks
        python_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
        if python_blocks:
            return python_blocks[0]
        
        # Look for general code blocks
        code_blocks = re.findall(r'```\n(.*?)\n```', content, re.DOTALL)
        if code_blocks:
            return code_blocks[0]
        
        return content
    
    def _generate_basic_skill_template(self, user_intent: str) -> str:
        """Generate a basic skill template as fallback"""
        skill_name = re.sub(r'[^a-zA-Z0-9_]', '_', user_intent[:50]).lower()
        
        return f'''# capability: {user_intent[:100]}

def run(message: str, context: dict) -> dict:
    """Generated skill for: {user_intent}"""
    try:
        safe_paths = context.get('safe_paths', {{}})
        
        # TODO: Implement the specific functionality
        # This is a basic template that needs manual completion
        
        result = "Basic skill template - needs implementation"
        
        return {{
            'success': True,
            'result': result,
            'files_created': []
        }}
    except Exception as e:
        return {{
            'success': False,
            'error': str(e),
            'files_created': []
        }}
'''
    
    def validate_skill_safety(self, code: str) -> Tuple[bool, List[str]]:
        """Validate skill code for basic safety requirements"""
        violations = []
        
        # Check for dangerous imports/functions
        dangerous_patterns = [
            (r'\beval\s*\(', "eval() function"),
            (r'\bexec\s*\(', "exec() function"),
            (r'\b__import__\s*\(', "__import__ function"),
            (r'\bos\.system\s*\(', "os.system() function"),
            (r'\bsubprocess\.', "subprocess module usage"),
            (r'\bshutil\.rmtree\s*\(', "shutil.rmtree() function"),
            (r'\bos\.remove\s*\(', "os.remove() without validation"),
            (r'\.\./', "path traversal attempt"),
        ]
        
        for pattern, description in dangerous_patterns:
            if re.search(pattern, code):
                violations.append(description)
        
        # Check for required structure
        if 'def run(' not in code:
            violations.append("Missing required run() function")
        
        # Check for safe path usage in file operations
        if 'open(' in code and 'safe_paths' not in code:
            violations.append("File operations must use safe_paths from context")
        
        return len(violations) == 0, violations
    
    async def test_skill_in_sandbox(self, code: str, user_intent: str) -> Dict[str, Any]:
        """Test skill code in sandbox environment"""
        try:
            # Create sandbox instance
            sandbox = self.sandbox_factory.create_sandbox(self.config.to_json())
            
            # Prepare test context
            test_context = {
                'safe_paths': self.safe_paths,
                'test_mode': True
            }
            
            # Create complete test code
            test_code = f'''
{code}

# Test execution
import json
if __name__ == '__main__':
    context = {json.dumps(test_context)}
    result = run({user_intent!r}, context)
    print(json.dumps(result))
'''
            
            # Execute in sandbox
            exec_result = await sandbox.execute_skill(test_code)
            
            if exec_result.get('success'):
                # Parse the result
                try:
                    output = exec_result.get('output', '')
                    result_data = json.loads(output.strip().split('\n')[-1])
                    return {
                        'success': True,
                        'sandbox_result': result_data,
                        'sandbox_type': exec_result.get('sandbox_type', 'unknown')
                    }
                except (json.JSONDecodeError, IndexError):
                    return {
                        'success': False,
                        'error': 'Could not parse skill output',
                        'raw_output': output
                    }
            else:
                return {
                    'success': False,
                    'error': exec_result.get('error', 'Sandbox execution failed'),
                    'raw_output': exec_result.get('output', '')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Sandbox testing error: {str(e)}'
            }
    
    async def promote_and_execute_skill(self, code: str, skill_name: str, user_intent: str) -> Dict[str, Any]:
        """Promote skill to skills directory and execute on host"""
        try:
            # Calculate code hash for audit
            code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
            
            # Add metadata header to code
            skill_code_with_metadata = f'''"""
Skill: {skill_name}
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
Intent: {user_intent}
Code Hash: {code_hash}
"""

{code}
'''
            
            # Save to skills directory
            if self.skills_mgr and self.skills_mgr.add_skill_file(skill_name, skill_code_with_metadata):
                self.skills_mgr.reload_skills()
                
                # Execute on host
                execution_context = {
                    'safe_paths': self.safe_paths,
                    'production_mode': True
                }
                
                # Execute the skill
                exec_result = self.skills_mgr.execute_skill_by_name(skill_name, user_intent)
                
                # Log audit event
                files_created = []
                if exec_result and exec_result.get('success'):
                    files_created = exec_result.get('files_created', [])
                
                self.log_audit_event(
                    event_type="skill_promoted_and_executed",
                    user_prompt=user_intent,
                    skill_name=skill_name,
                    code_hash=code_hash,
                    files_written=files_created,
                    execution_result=exec_result or {}
                )
                
                return {
                    'success': True,
                    'skill_name': skill_name,
                    'promoted': True,
                    'executed': True,
                    'execution_result': exec_result,
                    'code_hash': code_hash
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to save skill to skills directory'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Skill promotion/execution error: {str(e)}'
            }
    
    async def process_autonomous_request(self, user_input: str, conversation_history: List[str]) -> Dict[str, Any]:
        """
        Complete autonomous skill processing pipeline
        Returns status and any clarifying questions or execution results
        """
        try:
            # Step 1: Detect intent and missing parameters
            needs_skill, missing_params = self.detect_intent_and_missing_params(user_input, conversation_history)
            
            if not needs_skill:
                return {'needs_clarification': False, 'autonomous_action': False}
            
            if missing_params:
                clarifying_question = self.generate_clarifying_question(missing_params, user_input)
                return {
                    'needs_clarification': True,
                    'clarifying_question': clarifying_question,
                    'missing_params': missing_params
                }
            
            # Step 2: Check existing capabilities
            existing_skills = await self.scan_existing_capabilities(user_input)
            
            if existing_skills:
                # Try to use existing skill first
                best_skill = existing_skills[0]
                exec_result = self.skills_mgr.execute_skill_by_name(best_skill['name'], user_input)
                
                if exec_result and exec_result.get('success'):
                    return {
                        'autonomous_action': True,
                        'used_existing_skill': True,
                        'skill_name': best_skill['name'],
                        'execution_result': exec_result
                    }
            
            # Step 3: Generate new skill
            skill_code = await self.generate_skill_code(user_input, conversation_history)
            
            # Step 4: Safety validation
            is_safe, violations = self.validate_skill_safety(skill_code)
            if not is_safe:
                return {
                    'autonomous_action': False,
                    'error': f'Safety validation failed: {", ".join(violations)}',
                    'violations': violations
                }
            
            # Step 5: Sandbox testing
            sandbox_result = await self.test_skill_in_sandbox(skill_code, user_input)
            if not sandbox_result.get('success'):
                return {
                    'autonomous_action': False,
                    'error': f'Sandbox testing failed: {sandbox_result.get("error")}',
                    'sandbox_result': sandbox_result
                }
            
            # Step 6: Promote and execute
            skill_name = f"auto_skill_{int(time.time())}"
            promotion_result = await self.promote_and_execute_skill(skill_code, skill_name, user_input)
            
            return {
                'autonomous_action': True,
                'skill_generated': True,
                'promotion_result': promotion_result,
                'sandbox_result': sandbox_result
            }
            
        except Exception as e:
            return {
                'autonomous_action': False,
                'error': f'Autonomous processing error: {str(e)}'
            }

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        if not self.audit_log_path.exists():
            return []
        
        try:
            entries = []
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
            
            # Return most recent entries
            return sorted(entries, key=lambda x: x['timestamp'], reverse=True)[:limit]
        except Exception:
            return []
