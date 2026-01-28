import pytest
import requests
import os

# Nginx listens on PORT, default 20211
PORT = os.environ.get("PORT", "20211")
BACKEND_PORT = os.environ.get("BACKEND_PORT", "20212")
BASE_URL = f"http://localhost:{PORT}/server/"


def test_nginx_proxy_security_modern_check():
    """
    Test that access is allowed when Sec-Fetch-Site is 'same-origin'.
    """
    headers = {
        "Sec-Fetch-Site": "same-origin"
    }
    try:
        response = requests.get(BASE_URL, headers=headers)
        # 200 (OK), 401 (Auth), 404 (Not Found on backend), or 502 (Bad Gateway) means Nginx let it through.
        # 403 means Nginx blocked it.
        assert response.status_code in [200, 401, 404, 502], f"Expected access allowed, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Nginx. Is it running?")


def test_nginx_proxy_security_legacy_check():
    """
    Test that access is allowed when Sec-Fetch-Site is missing but Referer matches host.
    This is for old tablets/phones which are not updated in the last few years.
    """
    headers = {
        # No Sec-Fetch-Site
        "Referer": f"http://localhost:{PORT}/some/page"
    }
    try:
        response = requests.get(BASE_URL, headers=headers)
        assert response.status_code in [200, 401, 404, 502], f"Expected access allowed, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Nginx. Is it running?")


def test_nginx_proxy_security_block_cross_site():
    """
    Test that access is BLOCKED when Sec-Fetch-Site is 'cross-site'.
    """
    headers = {
        "Sec-Fetch-Site": "cross-site"
    }
    response = requests.get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"


def test_nginx_proxy_security_block_no_headers():
    """
    Test that access is BLOCKED when no security headers are present.
    """
    headers = {}
    response = requests.get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"


def test_nginx_proxy_security_block_same_site():
    """
    Test that access is BLOCKED when Sec-Fetch-Site is 'same-site'.
    (Strict same-origin enforcement)
    """
    headers = {"Sec-Fetch-Site": "same-site"}
    response = requests.get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 for same-site, got {response.status_code}"


def test_nginx_proxy_security_block_referer_suffix_spoof():
    """
    Test that access is BLOCKED when Referer merely ends with the valid host.
    """
    headers = {"Referer": f"http://attacker.com/path?target=localhost:{PORT}"}
    response = requests.get(BASE_URL, headers=headers)
    assert response.status_code == 403


def test_nginx_proxy_security_block_bad_referer():
    """
    Test that access is BLOCKED when Sec-Fetch-Site is missing and Referer is external.
    """
    headers = {
        "Referer": "http://evil.com/page"
    }
    response = requests.get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"


def test_nginx_proxy_security_block_subdomain_referer():
    """
    Test that access is BLOCKED when Referer is a subdomain (same-site, not same-origin).
    """
    headers = {
        "Referer": f"http://subdomain.localhost:{PORT}/"
    }
    response = requests.get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 for subdomain referer, got {response.status_code}"


def test_nginx_proxy_security_legacy_protocol_agnostic():
    """
    Test that the legacy check allows both http and https referers.
    """
    headers = {"Referer": f"https://localhost:{PORT}/path"}
    response = requests.get(BASE_URL, headers=headers)
    assert response.status_code in [200, 401, 404, 502]


def test_nginx_proxy_security_block_server_docs():
    """
    Test that access to `/server/docs` is BLOCKED when navigating with browser (no referrer)
    """
    url = f"http://localhost:{PORT}/server/docs"
    try:
        response = requests.get(url)
        # Backend may return 404 if it doesn't have the path; Nginx should never allow a 200 here.
        assert response.status_code == 403, f"Expected 403 for /server/docs, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Nginx. Is it running?")


def test_nginx_proxy_security_allow_port():
    """
    Test that access to `:20212/docs` is allowed by Nginx (should return 200).
    """
    headers = {"Referer": f"https://localhost:{BACKEND_PORT}/path"}
    url = f"http://localhost:{BACKEND_PORT}/docs"
    try:
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, f"Expected 200 for /server/docs on allowed port, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Nginx. Is it running?")
