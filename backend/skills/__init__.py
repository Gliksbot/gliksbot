"""
Dexter v3 Skills Package

This package contains dynamically loaded skill modules that extend Dexter's capabilities.
Each skill module should implement a run(message) function that takes a user message
and returns results or performs actions.

Usage:
    from backend.skills.skills_manager import SkillsManager
    
    # Initialize the skills manager
    skills_mgr = SkillsManager("/path/to/skills")
    
    # Execute all skills on a message
    results = await skills_mgr.execute_all_skills("user message")
    
    # Get list of available skills
    available = skills_mgr.list_skills()
    
    # Reload skills after adding new ones
    skills_mgr.reload_skills()

Skill Module Requirements:
    - Each skill module must be a .py file in the skills directory
    - Each skill must implement a run(message: str) -> dict function
    - The run function should return a dictionary with:
        - success: bool - whether the skill executed successfully
        - result: Any - the result of the skill execution
        - error: str (optional) - error message if execution failed
        - skill_name: str - name of the skill that executed

Example skill module (example_skill.py):
    def run(message: str) -> dict:
        '''Example skill that processes a message'''
        try:
            # Skill logic here
            processed = message.upper()
            return {
                "success": True,
                "result": f"Processed: {processed}",
                "skill_name": "example_skill"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "skill_name": "example_skill"
            }

Security Notes:
    - Skills are loaded dynamically and execute in the main process
    - For production, consider implementing sandboxing for skill execution
    - Validate skill code before promotion to the skills directory
    - Skills should handle errors gracefully and not crash the system
"""

from .skills_manager import SkillsManager

__all__ = ['SkillsManager']