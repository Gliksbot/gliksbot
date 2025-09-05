#!/usr/bin/env python3
"""
Test script for Gliksbot CLI interface

This script verifies that the CLI interface loads correctly and can handle
basic operations without requiring actual LLM providers.
"""

import asyncio
import os
import sys
import tempfile
import json
from pathlib import Path

# Add the backend directory to path for imports
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Import only the modules we need directly
import importlib.util

def load_module(module_path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location("module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load config module
config_module = load_module(os.path.join(backend_path, 'dexter_brain', 'config.py'))
Config = config_module.Config


def create_test_config():
    """Create a test configuration for CLI testing."""
    test_config = {
        "models": {
            "dexter": {
                "enabled": True,
                "provider": "mock",
                "model": "test-model",
                "endpoint": "http://localhost:11434",
                "identity": "You are Dexter, the test orchestrator",
                "role": "Chief Test Orchestrator",
                "prompt": "You coordinate test multi-LLM teams.",
                "api_key_env": "",
                "params": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            },
            "analyst": {
                "enabled": False,
                "provider": "mock",
                "model": "test-analyst",
                "endpoint": "",
                "api_key_env": "",
                "identity": "You are the test analyst specialist",
                "role": "Test Analyst Specialist",
                "prompt": "",
                "params": {}
            },
            "engineer": {
                "enabled": False,
                "provider": "mock", 
                "model": "test-engineer",
                "endpoint": "",
                "api_key_env": "",
                "identity": "You are the test engineer specialist",
                "role": "Test Engineer Specialist",
                "prompt": "",
                "params": {}
            },
            "researcher": {
                "enabled": False,
                "provider": "mock",
                "model": "test-researcher", 
                "endpoint": "",
                "api_key_env": "",
                "identity": "You are the test researcher specialist",
                "role": "Test Researcher Specialist",
                "prompt": "",
                "params": {}
            },
            "specialist": {
                "enabled": False,
                "provider": "mock",
                "model": "test-specialist",
                "endpoint": "",
                "api_key_env": "",
                "identity": "You are the test specialist",
                "role": "Test Specialist",
                "prompt": "",
                "params": {}
            }
        },
        "runtime": {
            "db_path": "./test_dexter.db",
            "enable_fts": True,
            "stm_ratio": 0.5
        },
        "collaboration": {
            "enabled": True,
            "base_directory": "./test_collaboration",
            "file_sync_interval": 5
        },
        "campaigns": {
            "enabled": True,
            "max_active": 10,
            "auto_objective_creation": True
        }
    }
    
    return test_config


def test_config_loading():
    """Test that configuration loading works correctly."""
    print("Testing configuration loading...")
    
    # Create test config
    test_data = create_test_config()
    
    # Test Config class initialization
    try:
        config = Config(test_data)
        print("✓ Config class initialization successful")
        
        # Test property access
        models = config.models
        print(f"✓ Models loaded: {list(models.keys())}")
        
        # Test Dexter config
        dexter_config = models.get('dexter', {})
        if dexter_config.get('enabled'):
            print("✓ Dexter configuration is enabled")
        else:
            print("✗ Dexter configuration not enabled")
            
        return True
        
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False


def test_skills_folder():
    """Test skills folder detection."""
    print("\nTesting skills folder detection...")
    
    skills_dir = Path("./skills")
    if skills_dir.exists():
        skill_files = list(skills_dir.glob("*.py"))
        print(f"✓ Skills folder found with {len(skill_files)} Python files")
        for skill_file in skill_files:
            print(f"  - {skill_file.name}")
    else:
        print("⚠ Skills folder not found - will be created when needed")
        # Create an empty skills folder for testing
        skills_dir.mkdir(exist_ok=True)
        print("✓ Created empty skills folder")
    
    return True


def test_cli_imports():
    """Test that CLI modules can be imported correctly."""
    print("\nTesting CLI imports...")
    
    try:
        # Test textual import
        import textual
        print("✓ Textual library available")
        
        # Test httpx import
        import httpx
        print("✓ HTTPX library available")
        
        # Test backend imports
        config_module = load_module(os.path.join(backend_path, 'dexter_brain', 'config.py'))
        print("✓ Config module loaded")
        
        llm_module = load_module(os.path.join(backend_path, 'dexter_brain', 'llm.py'))
        print("✓ LLM module loaded")
        
        utils_module = load_module(os.path.join(backend_path, 'dexter_brain', 'utils.py'))
        print("✓ Utils module loaded")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def create_test_config_file():
    """Create a test config.json file."""
    print("\nCreating test configuration file...")
    
    test_config = create_test_config()
    
    # Save to config.json
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(test_config, f, indent=2)
    
    print("✓ Test config.json created")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Gliksbot CLI Interface Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    tests = [
        test_cli_imports,
        test_config_loading,
        test_skills_folder,
        create_test_config_file
    ]
    
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! CLI interface should work correctly.")
        print("\nTo run the CLI interface:")
        print("  python3 cli_ui_simple.py")
    else:
        print("✗ Some tests failed. Check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())