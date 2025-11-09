import sys
import random
import pytest

INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from helper import get_setting_value
from api_server.api_server_start import app

# ----------------------------
# Fixtures
# ----------------------------
@pytest.fixture(scope="session")
def api_token():
    return get_setting_value("API_TOKEN")

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

# ----------------------------
# Logs Endpoint Tests
# ----------------------------
def test_clean_log(client, api_token):
    resp = client.delete("/logs?file=app.log", headers=auth_headers(api_token))
    assert resp.status_code == 200
    assert resp.json.get("success") is True

def test_clean_log_not_allowed(client, api_token):
    resp = client.delete("/logs?file=not_allowed.log", headers=auth_headers(api_token))
    assert resp.status_code == 400
    assert resp.json.get("success") is False

# ----------------------------
# Execution Queue Endpoint Tests
# ----------------------------
def test_add_to_execution_queue(client, api_token):
    action_name = f"test_action_{random.randint(0,9999)}"
    resp = client.post(
        "/logs/add-to-execution-queue",
        json={"action": action_name},
        headers=auth_headers(api_token)
    )
    assert resp.status_code == 200
    assert resp.json.get("success") is True
    assert action_name in resp.json.get("message", "")

def test_add_to_execution_queue_missing_action(client, api_token):
    resp = client.post(
        "/logs/add-to-execution-queue",
        json={},
        headers=auth_headers(api_token)
    )
    assert resp.status_code == 400
    assert resp.json.get("success") is False
    assert "Missing required 'action'" in resp.json.get("error", "")
