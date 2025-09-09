"""
Skills Manager for Dexter v3

This module provides dynamic loading and execution of skill modules.
Skills are Python files that implement a run(message) function.
"""

import os
import sys
import importlib
import importlib.util
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillsManager:
    """Manages dynamic loading and execution of skill modules"""
    
    def __init__(self, skills_directory: str):
        """
        Initialize the SkillsManager
        
        Args:
            skills_directory: Path to the directory containing skill modules
        """
        self.skills_directory = Path(skills_directory)
        self.skills_directory.mkdir(parents=True, exist_ok=True)
        self.loaded_skills: Dict[str, Any] = {}
        self.reload_skills()
    
    def reload_skills(self) -> None:
        """Reload all skills from the skills directory"""
        self.loaded_skills.clear()
        
        if not self.skills_directory.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_directory}")
            return
        
        # Scan for Python files in the skills directory
        for file_path in self.skills_directory.glob("*.py"):
            # Skip __init__.py and skills_manager.py
            if file_path.name in ['__init__.py', 'skills_manager.py']:
                continue
                
            try:
                self._load_skill(file_path)
            except Exception as e:
                logger.error(f"Failed to load skill {file_path.name}: {e}")

        # Register built-in skills that do not come from files
        self._register_system_info_skill()
    
    def _load_skill(self, file_path: Path) -> None:
        """Load a single skill module from file"""
        skill_name = file_path.stem
        
        try:
            # Create module spec
            spec = importlib.util.spec_from_file_location(skill_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create spec for {file_path}")
            
            # Load the module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Validate that the module has a run function
            if not hasattr(module, 'run'):
                raise AttributeError(f"Skill {skill_name} does not have a 'run' function")
            
            if not callable(module.run):
                raise AttributeError(f"Skill {skill_name} 'run' is not callable")
            
            # Store the loaded skill
            self.loaded_skills[skill_name] = {
                'module': module,
                'path': str(file_path),
                'name': skill_name,
                'run_function': module.run
            }
            
            logger.info(f"Successfully loaded skill: {skill_name}")
            
        except Exception as e:
            logger.error(f"Error loading skill {skill_name} from {file_path}: {e}")
            raise
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """Get a list of all loaded skills"""
        return [
            {
                'name': skill_info['name'],
                'path': skill_info['path']
            }
            for skill_info in self.loaded_skills.values()
        ]
    
    async def execute_all_skills(self, message: str) -> List[Dict[str, Any]]:
        """
        Execute all loaded skills on the given message
        
        Args:
            message: The user message to process
            
        Returns:
            List of results from all skills
        """
        results = []
        
        for skill_name, skill_info in self.loaded_skills.items():
            try:
                result = await self._execute_skill(skill_info, message)
                results.append(result)
            except Exception as e:
                error_result = {
                    'success': False,
                    'error': str(e),
                    'skill_name': skill_name
                }
                results.append(error_result)
                logger.error(f"Error executing skill {skill_name}: {e}")
        
        return results
    
    async def _execute_skill(self, skill_info: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Execute a single skill safely"""
        skill_name = skill_info['name']
        run_function = skill_info['run_function']
        
        try:
            # Check if the run function is async
            if asyncio.iscoroutinefunction(run_function):
                result = await run_function(message)
            else:
                # Run sync function in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, run_function, message)
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                result = {
                    'success': True,
                    'result': result,
                    'skill_name': skill_name
                }
            else:
                # Ensure skill_name is set
                result.setdefault('skill_name', skill_name)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'skill_name': skill_name
            }
    
    def execute_skill_by_name(self, skill_name: str, message: str) -> Optional[Dict[str, Any]]:
        """Execute a specific skill by name"""
        if skill_name not in self.loaded_skills:
            return {
                'success': False,
                'error': f"Skill '{skill_name}' not found",
                'skill_name': skill_name
            }
        
        skill_info = self.loaded_skills[skill_name]
        try:
            # For sync execution of single skill
            run_function = skill_info['run_function']
            result = run_function(message)
            
            if not isinstance(result, dict):
                result = {
                    'success': True,
                    'result': result,
                    'skill_name': skill_name
                }
            else:
                result.setdefault('skill_name', skill_name)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'skill_name': skill_name
            }
    
    def add_skill_file(self, skill_name: str, skill_code: str) -> bool:
        """
        Add a new skill file to the skills directory
        
        Args:
            skill_name: Name of the skill (without .py extension)
            skill_code: Python code for the skill
            
        Returns:
            True if skill was added successfully, False otherwise
        """
        try:
            safe_name = Path(skill_name).stem
            if safe_name != skill_name or any(sep in skill_name for sep in ("/", "\\")):
                raise ValueError("Invalid skill name")

            skill_file = (self.skills_directory / f"{safe_name}.py").resolve()
            if skill_file.parent != self.skills_directory.resolve():
                raise ValueError("Invalid skill path")

            skill_file.write_text(skill_code, encoding='utf-8')

            # Try to load the new skill
            self._load_skill(skill_file)
            
            logger.info(f"Successfully added skill: {skill_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add skill {skill_name}: {e}")
            return False
    
    def remove_skill(self, skill_name: str) -> bool:
        """
        Remove a skill from the manager and delete its file
        
        Args:
            skill_name: Name of the skill to remove
            
        Returns:
            True if skill was removed successfully, False otherwise
        """
        try:
            # Remove from loaded skills
            if skill_name in self.loaded_skills:
                del self.loaded_skills[skill_name]
            
            # Remove file
            skill_file = self.skills_directory / f"{skill_name}.py"
            if skill_file.exists():
                skill_file.unlink()
            
            logger.info(f"Successfully removed skill: {skill_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove skill {skill_name}: {e}")
            return False

    def skill_exists(self, skill_name: str) -> bool:
        """Check if a skill exists"""
        return skill_name in self.loaded_skills

    def _register_system_info_skill(self) -> None:
        """Register a built-in skill exposing basic OS and Python info"""

        def _system_info(_message: str) -> Dict[str, Any]:
            return {
                'success': True,
                'skill_name': 'system_info',
                'platform': sys.platform,
                'cwd': os.getcwd(),
                'python_version': sys.version,
            }

        self.loaded_skills['system_info'] = {
            'module': None,
            'path': 'builtin',
            'name': 'system_info',
            'run_function': _system_info,
        }
