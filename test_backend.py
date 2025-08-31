#!/usr/bin/env python3
"""
Quick test script for the updated Dexter backend API
"""
import json
import sys
import os

# Add backend to path
sys.path.insert(0, '/workspaces/gliksbot/backend')

def test_config_loading():
    """Test if the config can be loaded successfully"""
    try:
        from dexter_brain.config import Config
        config = Config.load('/workspaces/gliksbot/config.json')
        print("✓ Config loaded successfully")
        print(f"  Models configured: {list(config.models.keys())}")
        return config
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return None

def test_collaboration_manager(config):
    """Test if CollaborationManager can be initialized"""
    try:
        from dexter_brain.collaboration import CollaborationManager
        collab_mgr = CollaborationManager(config)
        print("✓ CollaborationManager initialized successfully")
        
        # Test active sessions method
        active_sessions = collab_mgr.get_active_sessions()
        print(f"  Active sessions: {len(active_sessions)}")
        return collab_mgr
    except Exception as e:
        print(f"✗ Failed to initialize CollaborationManager: {e}")
        return None

def test_api_imports():
    """Test if the main API module imports correctly"""
    try:
        # Set required environment variables
        os.environ.setdefault("DEXTER_CONFIG_FILE", "/workspaces/gliksbot/config.json")
        os.environ.setdefault("DEXTER_DOWNLOADS_DIR", "/tmp/dexter_downloads")
        
        # Create downloads directory
        os.makedirs("/tmp/dexter_downloads", exist_ok=True)
        
        from main import app
        print("✓ Main API module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import main API: {e}")
        return False

if __name__ == "__main__":
    print("Testing Dexter backend updates...")
    print("-" * 40)
    
    # Test config loading
    config = test_config_loading()
    if not config:
        sys.exit(1)
    
    # Test collaboration manager
    collab_mgr = test_collaboration_manager(config)
    if not collab_mgr:
        sys.exit(1)
    
    # Test API imports
    if not test_api_imports():
        sys.exit(1)
    
    print("-" * 40)
    print("✓ All tests passed! Backend should be ready to run.")
