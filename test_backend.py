import os
import pytest

from backend.dexter_brain.config import Config
from backend.dexter_brain.collaboration import CollaborationManager
from backend.dexter_brain.utils import get_config_path
from fastapi.testclient import TestClient


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


def test_auth_and_history(monkeypatch):
    downloads_dir = "/tmp/dexter_downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    monkeypatch.setenv("DEXTER_CONFIG_FILE", get_config_path())
    monkeypatch.setenv("DEXTER_DOWNLOADS_DIR", downloads_dir)

    from backend.main import app
    client = TestClient(app)

    auth = client.post("/auth/login", json={"username": "u", "password": "p"})
    assert auth.status_code == 200
    token = auth.json()["token"]

    headers = {"Authorization": f"Bearer {token}"}
    chat = client.post("/chat", json={"message": "hello"}, headers=headers)
    assert chat.status_code == 200

    hist = client.get("/history")
    assert hist.status_code == 200
    assert "interactions" in hist.json()

