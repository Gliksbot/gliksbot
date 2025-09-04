"""
Utility functions for path resolution and common operations.
"""
import os
from pathlib import Path
from typing import Optional


def find_project_root(start_path: Optional[str] = None) -> str:
    """
    Find the project root directory by looking for config.json.
    
    Args:
        start_path: Starting directory for search. If None, uses current file's directory.
        
    Returns:
        Path to project root directory
        
    Raises:
        FileNotFoundError: If config.json cannot be found in any parent directory
    """
    if start_path is None:
        start_path = os.path.dirname(os.path.abspath(__file__))
    
    current = Path(start_path).resolve()
    
    # Search upward for config.json
    for parent in [current] + list(current.parents):
        config_path = parent / "config.json"
        if config_path.exists():
            return str(parent)
    
    # Fallback: try relative to the dexter_brain module location
    # This handles cases where we're running from different working directories
    module_dir = Path(__file__).parent.parent.parent
    config_path = module_dir / "config.json"
    if config_path.exists():
        return str(module_dir)
    
    raise FileNotFoundError(
        f"Could not find config.json in any parent directory of {start_path}. "
        "Make sure you're running from within the project directory."
    )


def get_config_path(config_env_var: str = "DEXTER_CONFIG_FILE") -> str:
    """
    Get the path to config.json, checking environment variable first.
    
    Args:
        config_env_var: Environment variable name for config file path
        
    Returns:
        Absolute path to config.json
    """
    # Check environment variable first
    env_path = os.environ.get(config_env_var)
    if env_path and os.path.isfile(env_path):
        return env_path
    
    # Find project root and construct config path
    project_root = find_project_root()
    return os.path.join(project_root, "config.json")


def get_project_relative_path(*path_components: str) -> str:
    """
    Get a path relative to the project root.
    
    Args:
        *path_components: Path components to join with project root
        
    Returns:
        Absolute path constructed from project root
    """
    project_root = find_project_root()
    return os.path.join(project_root, *path_components)