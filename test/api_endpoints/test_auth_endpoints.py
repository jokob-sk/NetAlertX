# tests/test_auth.py

import sys
import os
import pytest

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from helper import get_setting_value  # noqa: E402
from api_server.api_server_start import app  # noqa: E402


@pytest.fixture(scope="session")
def api_token():
    """Load API token from system settings (same as other tests)."""
    return get_setting_value("API_TOKEN")


@pytest.fixture
def client():
    """Flask test client."""
    with app.test_client() as client:
        yield client


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# -------------------------
# AUTH ENDPOINT TESTS
# -------------------------

def test_auth_ok(client, api_token):
    """Valid token should allow access."""
    resp = client.get("/auth", headers=auth_headers(api_token))
    assert resp.status_code == 200

    data = resp.get_json()
    assert data is not None
    assert data.get("success") is True
    assert "successful" in data.get("message", "").lower()


def test_auth_missing_token(client):
    """Missing token should be forbidden."""
    resp = client.get("/auth")
    assert resp.status_code == 403

    data = resp.get_json()
    assert data is not None
    assert data.get("success") is False
    assert "not authorized" in data.get("message", "").lower()


def test_auth_invalid_token(client):
    """Invalid bearer token should be forbidden."""
    resp = client.get("/auth", headers=auth_headers("INVALID-TOKEN"))
    assert resp.status_code == 403

    data = resp.get_json()
    assert data is not None
    assert data.get("success") is False
    assert "not authorized" in data.get("message", "").lower()
