"""Runtime validation tests for the devices/search endpoint."""

import os
import time

import pytest
import requests


BASE_URL = os.getenv("NETALERTX_BASE_URL", "http://localhost:20212")
REQUEST_TIMEOUT = float(os.getenv("NETALERTX_REQUEST_TIMEOUT", "5"))
SERVER_RETRIES = int(os.getenv("NETALERTX_SERVER_RETRIES", "5"))

API_TOKEN = os.getenv("API_TOKEN") or os.getenv("NETALERTX_API_TOKEN")
if not API_TOKEN:
    pytest.skip("API_TOKEN not found; skipping runtime validation tests", allow_module_level=True)

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}


def wait_for_server() -> bool:
    """Probe the backend GraphQL endpoint with paced retries."""
    for _ in range(SERVER_RETRIES):
        try:
            resp = requests.get(f"{BASE_URL}/graphql", timeout=2)
            if 200 <= resp.status_code < 300:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


if not wait_for_server():
    pytest.skip("NetAlertX backend is unreachable; skipping runtime validation tests", allow_module_level=True)


def test_search_valid():
    """Valid payloads should return 200/404 but never 422."""
    payload = {"query": "Router"}
    resp = requests.post(
        f"{BASE_URL}/devices/search",
        json=payload,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code in (200, 404), f"Unexpected status {resp.status_code}: {resp.text}"
    assert resp.status_code != 422, f"Validation failed for valid payload: {resp.text}"


def test_search_invalid_schema():
    """Missing required fields must trigger a 422 validation error."""
    resp = requests.post(
        f"{BASE_URL}/devices/search",
        json={},
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code in (401, 403):
        pytest.fail(f"Authorization failed: {resp.status_code} {resp.text}")
    assert resp.status_code == 422, f"Expected 422 for missing query: {resp.status_code} {resp.text}"


def test_search_invalid_type():
    """Invalid field types must also result in HTTP 422."""
    payload = {"query": 1234, "limit": "invalid"}
    resp = requests.post(
        f"{BASE_URL}/devices/search",
        json=payload,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code in (401, 403):
        pytest.fail(f"Authorization failed: {resp.status_code} {resp.text}")
    assert resp.status_code == 422, f"Expected 422 for invalid types: {resp.status_code} {resp.text}"
