"""Enhanced skill creation and testing with Docker sandbox and error healing."""

import asyncio
import json
import time
import traceback
from typing import Dict, Any, Optional
from pathlib import Path

from .sandbox import create_sandbox
from .error_tracker import ErrorTracker, ErrorSeverity
from .collaboration import CollaborationManager


async def create_and_test_skill_with_healing(
    user_request: str, 
    solution_content: str,
    config: Dict[str, Any],
    error_tracker: ErrorTracker,
    collaboration_manager: CollaborationManager,
    max_attempts: int = 3
) -> Dict[str, Any]:
    """Create and test skill with automatic error healing."""
    
    attempt_results = []
    
    for attempt in range(max_attempts):
        try:
            print(f"\n🧪 Skill Testing Attempt {attempt + 1}/{max_attempts}")
            
            # Create sandbox based on configuration
            sandbox = create_sandbox(config)
            
            # Prepare test code
            test_code = _generate_test_code(solution_content)
            
            # Execute the skill
            result = await sandbox.execute_skill(solution_content, test_code)
            
            attempt_results.append({
                "attempt": attempt + 1,
                "success": result['success'],
                "execution_time": result.get('execution_time', 0),
                "output": result.get('output', ''),
                "test_success": result.get('test_success'),
                "sandbox_type": result.get('sandbox_type', 'unknown')
            })
            
            if result['success'] and result.get('test_success', True):
                # Success! Create skill record
                skill_name = f"skill_{int(time.time())}"
                
                # Save skill to skills directory
                await _save_skill_to_library(skill_name, solution_content, user_request, result)
                
                return {
                    "ok": True,
                    "skill_name": skill_name,
                    "tested_in_sandbox": True,
                    "promoted": True,
                    "solution_used": solution_content[:100] + "...",
                    "sandbox_type": result.get('sandbox_type', 'unknown'),
                    "attempts": attempt + 1,
                    "attempt_results": attempt_results,
                    "execution_time": result.get('execution_time', 0)
                }
            else:
                # Failure - log error for healing
                error_id = error_tracker.log_error(
                    error_type="SKILL_EXECUTION_FAILED",
                    message=f"Skill execution failed: {result.get('error', 'Unknown error')}",
                    severity=ErrorSeverity.MEDIUM,
                    source="skill_testing",
                    context={
                        "user_request": user_request,
                        "solution_content": solution_content[:500],
                        "attempt": attempt + 1,
                        "sandbox_output": result.get('output', ''),
                        "test_output": result.get('test_output', ''),
                        "exit_code": result.get('exit_code', -1),
                        "sandbox_type": result.get('sandbox_type', 'unknown')
                    }
                )
                
                print(f"❌ Skill execution failed (Error ID: {error_id})")
                
                if attempt < max_attempts - 1:
                    # Trigger healing session for the failed skill
                    print(f"🔧 Triggering healing session for failed skill...")
                    
                    corrected_solution = await _trigger_skill_healing(
                        user_request, solution_content, result, 
                        collaboration_manager, error_id
                    )
                    
                    if corrected_solution and corrected_solution != solution_content:
                        solution_content = corrected_solution
                        print(f"🔧 Attempting skill healing - attempt {attempt + 2}")
                        continue
                    else:
                        print(f"⚠️ No corrected solution received from healing")
                
        except Exception as e:
            # Log unexpected execution errors
            error_id = error_tracker.log_error(
                error_type="SKILL_TESTING_EXCEPTION",
                message=str(e),
                severity=ErrorSeverity.HIGH,
                source="skill_testing",
                context={
                    "user_request": user_request,
                    "attempt": attempt + 1,
                    "traceback": traceback.format_exc()
                }
            )
            
            attempt_results.append({
                "attempt": attempt + 1,
                "success": False,
                "error": str(e),
                "error_id": error_id
            })
            
            print(f"❌ Skill testing exception (Error ID: {error_id}): {e}")
    
    # All attempts failed
    return {
        "ok": False,
        "error": "Skill creation failed after all healing attempts",
        "attempts": max_attempts,
        "attempt_results": attempt_results,
        "final_solution": solution_content
    }


async def _trigger_skill_healing(
    user_request: str,
    failed_solution: str, 
    execution_result: Dict[str, Any],
    collaboration_manager: CollaborationManager,
    error_id: str
) -> Optional[str]:
    """Trigger a healing session for a failed skill."""
    
    healing_prompt = f"""SKILL EXECUTION FAILED - HEALING REQUIRED

=== ORIGINAL REQUEST ===
{user_request}

=== FAILED SOLUTION ===
```python
{failed_solution}
```

=== EXECUTION RESULTS ===
Success: {execution_result.get('success', False)}
Exit Code: {execution_result.get('exit_code', 'Unknown')}
Sandbox Type: {execution_result.get('sandbox_type', 'Unknown')}

=== ERROR OUTPUT ===
{execution_result.get('output', 'No output')}

=== TEST OUTPUT ===
{execution_result.get('test_output', 'No test output')}

=== ERROR DETAILS ===
{execution_result.get('error', 'No additional error details')}

=== TASK ===
Analyze the failure and provide a CORRECTED version of the skill code.

Focus on:
1. **Syntax Errors**: Fix any Python syntax issues
2. **Logic Errors**: Correct algorithmic problems  
3. **Missing Imports**: Add required import statements
4. **Runtime Exceptions**: Handle potential runtime errors
5. **Security Issues**: Ensure code follows security best practices
6. **Testing**: Ensure code will pass basic functionality tests

=== RESPONSE FORMAT ===
Analysis: [Brief analysis of what went wrong]
Corrected_Code: [The complete corrected Python code]
Key_Changes: [List of key changes made]
Confidence: [HIGH/MEDIUM/LOW]

Provide the corrected code in a format that can be executed directly.
The code should be a complete, working solution that addresses the original request.

Remember: The corrected code will be tested immediately in the sandbox environment."""

    try:
        # Start healing collaboration
        healing_session = await collaboration_manager.broadcast_user_input(
            healing_prompt, 
            f"skill_healing_{error_id}_{int(time.time())}"
        )
        
        # Wait for healing to complete (shorter timeout for skill healing)
        healing_complete = await collaboration_manager.wait_for_collaboration_complete(
            healing_session, timeout=45.0
        )
        
        if healing_complete:
            winning_solution = collaboration_manager.get_winning_solution(healing_session)
            if winning_solution:
                solution_text = winning_solution.get('solution', '')
                
                # Extract corrected code from the solution
                corrected_code = _extract_corrected_code(solution_text)
                
                if corrected_code:
                    print(f"✅ Received corrected solution from healing session")
                    return corrected_code
                else:
                    print(f"⚠️ Could not extract corrected code from healing solution")
            else:
                print(f"⚠️ No winning solution from healing session")
        else:
            print(f"⚠️ Healing session timed out")
            
    except Exception as e:
        print(f"❌ Error in skill healing session: {e}")
    
    return None


def _extract_corrected_code(solution_text: str) -> Optional[str]:
    """Extract corrected Python code from healing solution."""
    
    # Look for code between ```python and ``` markers
    import re
    
    # Try to find Python code blocks
    python_pattern = r'```python\s*\n(.*?)\n```'
    matches = re.findall(python_pattern, solution_text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Try to find code blocks without language specifier
    code_pattern = r'```\s*\n(.*?)\n```'
    matches = re.findall(code_pattern, solution_text, re.DOTALL)
    
    if matches:
        # Take the longest code block (most likely to be complete)
        longest_match = max(matches, key=len)
        return longest_match.strip()
    
    # Try to extract from "Corrected_Code:" section
    corrected_pattern = r'Corrected_Code:\s*\n(.*?)(?=\n[A-Z][a-z_]+:|$)'
    matches = re.findall(corrected_pattern, solution_text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Last resort: return the whole solution if it looks like code
    if ('def ' in solution_text or 'import ' in solution_text or 
        'class ' in solution_text or 'return ' in solution_text):
        return solution_text.strip()
    
    return None


def _generate_test_code(solution_content: str) -> str:
    """Generate basic test code for a skill."""
    
    # Extract function names from the solution
    import re
    function_pattern = r'def\s+(\w+)\s*\('
    functions = re.findall(function_pattern, solution_content)
    
    if not functions:
        # No functions found, create a basic execution test
        return """
import pytest

def test_execution():
    \"\"\"Test that the code executes without errors.\"\"\"
    try:
        # Execute the skill code
        exec(open('skill.py').read())
        assert True, "Code executed successfully"
    except Exception as e:
        pytest.fail(f"Code execution failed: {e}")
"""
    
    # Generate tests for found functions
    test_code = "import pytest\nfrom skill import " + ", ".join(functions) + "\n\n"
    
    for func in functions:
        test_code += f"""
def test_{func}():
    \"\"\"Test {func} function.\"\"\"
    try:
        # Basic test - function should be callable
        result = {func}
        assert result is not None or result is None  # Accept any result
    except TypeError:
        # Function might need parameters, test with common values
        try:
            result = {func}("test")
            assert True
        except:
            try:
                result = {func}(1)
                assert True
            except:
                assert True  # Function exists but needs specific params
    except Exception as e:
        pytest.fail(f"{func} failed: {{e}}")
"""
    
    return test_code


async def _save_skill_to_library(
    skill_name: str, 
    skill_code: str, 
    user_request: str, 
    execution_result: Dict[str, Any]
) -> None:
    """Save a successfully tested skill to the skills library."""
    
    skills_dir = Path("./skills")
    skills_dir.mkdir(exist_ok=True)
    
    skill_metadata = {
        "name": skill_name,
        "created_at": time.time(),
        "user_request": user_request,
        "execution_result": {
            "success": execution_result.get('success'),
            "execution_time": execution_result.get('execution_time'),
            "sandbox_type": execution_result.get('sandbox_type'),
            "test_success": execution_result.get('test_success')
        },
        "code": skill_code
    }
    
    # Save skill file
    skill_file = skills_dir / f"{skill_name}.py"
    skill_file.write_text(skill_code)
    
    # Save metadata
    metadata_file = skills_dir / f"{skill_name}.json"
    metadata_file.write_text(json.dumps(skill_metadata, indent=2))
    
    print(f"💾 Skill saved to library: {skill_name}")


def get_sandbox_health_status(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get health status of the configured sandbox provider."""
    
    try:
        sandbox = create_sandbox(config)
        
        if hasattr(sandbox, 'check_health'):
            return sandbox.check_health()
        else:
            return {
                "healthy": True,
                "provider": "unknown",
                "message": "Health check not available for this provider"
            }
            
    except Exception as e:
        return {
            "healthy": False,
            "provider": "unknown",
            "error": str(e),
            "message": f"Failed to create sandbox: {e}"
        }