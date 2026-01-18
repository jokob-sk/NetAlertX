"""Runtime Wake-on-LAN endpoint validation tests."""

import os
import time
from typing import Dict

import pytest
import requests


BASE_URL = os.getenv("NETALERTX_BASE_URL", "http://localhost:20212")
REQUEST_TIMEOUT = float(os.getenv("NETALERTX_REQUEST_TIMEOUT", "5"))
SERVER_RETRIES = int(os.getenv("NETALERTX_SERVER_RETRIES", "5"))
SERVER_DELAY = float(os.getenv("NETALERTX_SERVER_DELAY", "1"))


def wait_for_server() -> bool:
    """Wait for the GraphQL endpoint to become ready with paced retries."""
    for _ in range(SERVER_RETRIES):
        try:
            resp = requests.get(f"{BASE_URL}/graphql", timeout=1)
            if 200 <= resp.status_code < 300:
                return True
        except requests.RequestException:
            pass
        time.sleep(SERVER_DELAY)
    return False


@pytest.fixture(scope="session", autouse=True)
def ensure_backend_ready():
    """Skip the module if the backend is not running."""
    if not wait_for_server():
        pytest.skip("NetAlertX backend is not reachable for WOL validation tests")


@pytest.fixture(scope="session")
def auth_headers() -> Dict[str, str]:
    token = os.getenv("API_TOKEN") or os.getenv("NETALERTX_API_TOKEN")
    if not token:
        pytest.skip("API_TOKEN not configured; skipping WOL validation tests")
    return {"Authorization": f"Bearer {token}"}


def test_wol_valid_mac(auth_headers):
    """Ensure a valid MAC request is accepted (anything except 422 is acceptable)."""
    payload = {"devMac": "00:11:22:33:44:55"}
    resp = requests.post(
        f"{BASE_URL}/nettools/wakeonlan",
        json=payload,
        headers=auth_headers,
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code != 422, f"Validation failed for valid MAC: {resp.text}"


def test_wol_valid_ip(auth_headers):
    """Ensure an IP-based request passes validation (404 acceptable, 422 is not)."""
    payload = {"ip": "1.2.3.4"}
    resp = requests.post(
        f"{BASE_URL}/nettools/wakeonlan",
        json=payload,
        headers=auth_headers,
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code != 422, f"Validation failed for valid IP payload: {resp.text}"


def test_wol_invalid_mac(auth_headers):
    """Invalid MAC payloads must be rejected with HTTP 422."""
    payload = {"devMac": "invalid-mac"}
    resp = requests.post(
        f"{BASE_URL}/nettools/wakeonlan",
        json=payload,
        headers=auth_headers,
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code == 422, f"Expected 422 for invalid MAC, got {resp.status_code}: {resp.text}"
