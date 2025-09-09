import os
import pytest

from backend.dexter_brain.config import Config
from backend.dexter_brain.collaboration import CollaborationManager
from backend.dexter_brain.utils import get_config_path


@pytest.fixture(scope="module")
def config():
    """Load the Dexter configuration used in backend tests."""
    return Config.load(get_config_path())


def test_config_loading(config):
    """Ensure configuration loads and contains model definitions."""
    assert isinstance(config.models, dict)
    assert config.models, "No models configured"


def test_collaboration_manager(config):
    """Verify CollaborationManager initializes and exposes session API."""
    collab_mgr = CollaborationManager(config)
    assert collab_mgr.get_active_sessions() == []


def test_api_imports(monkeypatch):
    """Check that the FastAPI app can be imported with required env vars."""
    downloads_dir = "/tmp/dexter_downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    monkeypatch.setenv("DEXTER_CONFIG_FILE", get_config_path())
    monkeypatch.setenv("DEXTER_DOWNLOADS_DIR", downloads_dir)

    from backend.main import app
    assert hasattr(app, "router")

