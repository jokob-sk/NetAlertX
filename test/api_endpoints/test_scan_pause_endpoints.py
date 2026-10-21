import pytest
from unittest.mock import patch, MagicMock

from api_server.api_server_start import app
from helper import get_setting_value


@pytest.fixture(scope="session")
def api_token():
    return get_setting_value("API_TOKEN")


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# --- /scan/pause ---


@patch("api_server.api_server_start.updateState")
def test_pause_scan_success(mock_update_state, client, api_token):
    """Valid minutes value pauses scans and returns a future pause_until timestamp."""
    mock_update_state.return_value = MagicMock()

    response = client.post("/scan/pause", json={"minutes": 10}, headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "pause_until" in data and data["pause_until"]

    mock_update_state.assert_called_once()
    args, kwargs = mock_update_state.call_args
    assert args[0] == "Process: Paused for 10 min"
    assert kwargs["pause_until"] == data["pause_until"]


@patch("api_server.api_server_start.updateState")
def test_pause_scan_default_minutes_used(mock_update_state, client, api_token):
    """The header button's default 10-minute pause request is accepted."""
    mock_update_state.return_value = MagicMock()

    response = client.post("/scan/pause", json={"minutes": 10}, headers=auth_headers(api_token))

    assert response.status_code == 200
    assert response.get_json()["success"] is True


@pytest.mark.parametrize("minutes", [0, -5, 1441, "ten"])
def test_pause_scan_invalid_minutes(client, api_token, minutes):
    """Out-of-bounds or non-integer minutes values are rejected with a 400."""
    response = client.post("/scan/pause", json={"minutes": minutes}, headers=auth_headers(api_token))

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_pause_scan_missing_minutes(client, api_token):
    """Missing 'minutes' field is rejected with a 400."""
    response = client.post("/scan/pause", json={}, headers=auth_headers(api_token))

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_pause_scan_requires_auth(client):
    """Unauthenticated requests are rejected."""
    response = client.post("/scan/pause", json={"minutes": 10})

    assert response.status_code == 403


# --- /scan/resume ---


@patch("api_server.api_server_start.updateState")
def test_resume_scan_success(mock_update_state, client, api_token):
    """Resume clears the pause and reports pause_until as empty."""
    mock_update_state.return_value = MagicMock()

    response = client.post("/scan/resume", headers=auth_headers(api_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["pause_until"] == ""

    mock_update_state.assert_called_once_with("Process: Idle", pause_until="")


@patch("api_server.api_server_start.updateState")
def test_resume_scan_idempotent_when_not_paused(mock_update_state, client, api_token):
    """Calling resume when scans are not paused still succeeds (idempotent)."""
    mock_update_state.return_value = MagicMock()

    response = client.post("/scan/resume", headers=auth_headers(api_token))
    response2 = client.post("/scan/resume", headers=auth_headers(api_token))

    assert response.status_code == 200
    assert response2.status_code == 200
    assert response.get_json()["success"] is True
    assert response2.get_json()["success"] is True


def test_resume_scan_requires_auth(client):
    """Unauthenticated requests are rejected."""
    response = client.post("/scan/resume")

    assert response.status_code == 403
