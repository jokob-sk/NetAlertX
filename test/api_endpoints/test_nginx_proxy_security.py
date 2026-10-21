import pytest
import requests
import os

# Nginx listens on PORT, default 20211
PORT = os.environ.get("PORT", "20211")
BACKEND_PORT = os.environ.get("BACKEND_PORT", "20212")
BASE_URL = f"http://localhost:{PORT}/server/"

REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", 5))


def http_get(url, headers=None):
    return requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)


def test_nginx_proxy_security_modern_check():
    """
    Test that access is allowed when Sec-Fetch-Site is 'same-origin'.
    """
    headers = {
        "Sec-Fetch-Site": "same-origin"
    }

    try:
        response = http_get(BASE_URL, headers=headers)

        print(f"BASE_URL: {BASE_URL}")
        print(f"Status: {response.status_code}")
        print("Response headers:", response.headers)
        print("Response body:")
        print(response.text)

        assert response.status_code != 403, (
            f"Expected access not blocked by Nginx, got {response.status_code}"
        )

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
        response = http_get(BASE_URL, headers=headers)
        assert response.status_code != 403, f"Expected access not blocked by Nginx, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Nginx. Is it running?")


def test_nginx_proxy_security_block_cross_site():
    """
    Test that access is BLOCKED when Sec-Fetch-Site is 'cross-site'.
    """
    headers = {
        "Sec-Fetch-Site": "cross-site"
    }
    response = http_get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"


def test_nginx_proxy_security_block_no_headers():
    """
    Test that access is BLOCKED when no security headers are present.
    """
    headers = {}
    response = http_get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"


def test_nginx_proxy_security_block_same_site():
    """
    Test that access is BLOCKED when Sec-Fetch-Site is 'same-site'.
    (Strict same-origin enforcement)
    """
    headers = {"Sec-Fetch-Site": "same-site"}
    response = http_get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 for same-site, got {response.status_code}"


def test_nginx_proxy_security_block_referer_suffix_spoof():
    """
    Test that access is BLOCKED when Referer merely ends with the valid host.
    """
    headers = {"Referer": f"http://attacker.com/path?target=localhost:{PORT}"}
    response = http_get(BASE_URL, headers=headers)
    assert response.status_code == 403


def test_nginx_proxy_security_block_bad_referer():
    """
    Test that access is BLOCKED when Sec-Fetch-Site is missing and Referer is external.
    """
    headers = {
        "Referer": "http://evil.com/page"
    }
    response = http_get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"


def test_nginx_proxy_security_block_subdomain_referer():
    """
    Test that access is BLOCKED when Referer is a subdomain (same-site, not same-origin).
    """
    headers = {
        "Referer": f"http://subdomain.localhost:{PORT}/"
    }
    response = http_get(BASE_URL, headers=headers)
    assert response.status_code == 403, f"Expected 403 for subdomain referer, got {response.status_code}"


def test_nginx_proxy_security_legacy_protocol_agnostic():
    """
    Test that the legacy check allows both http and https referers.
    """
    headers = {"Referer": f"https://localhost:{PORT}/path"}
    response = http_get(BASE_URL, headers=headers)
    assert response.status_code != 403, f"Expected access not blocked by Nginx, got {response.status_code}"


def test_nginx_proxy_security_block_server_docs():
    """
    Test that access to `/server/docs` is BLOCKED when navigating with browser (no referrer)
    """
    url = f"http://localhost:{PORT}/server/docs"
    try:
        response = http_get(url)
        # Backend may return 404 if it doesn't have the path; Nginx should never allow a 200 here.
        assert response.status_code == 403, f"Expected 403 for /server/docs, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Nginx. Is it running?")


def test_nginx_proxy_security_allow_port():
    """
    Test that the backend port (20212) is directly reachable without Nginx security filtering.
    200 indicates a healthy backend; 500 indicates the backend is reachable but returned an error.
    """
    headers = {"Referer": f"https://localhost:{BACKEND_PORT}/path"}
    url = f"http://localhost:{BACKEND_PORT}/docs"
    try:
        response = http_get(url, headers=headers)
        assert response.status_code in [200, 500], f"Expected backend reachable on allowed port, got {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Could not connect to Nginx. Is it running?")
