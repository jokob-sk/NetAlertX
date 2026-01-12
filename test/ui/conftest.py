#!/usr/bin/env python3
"""
Pytest configuration and fixtures for UI tests
"""

import pytest

import sys
import os

# Add test directory to path
sys.path.insert(0, os.path.dirname(__file__))

from test_helpers import get_driver, get_api_token, BASE_URL, API_BASE_URL   # noqa: E402 [flake8 lint suppression]


@pytest.fixture(scope="function")
def driver():
    """Provide a Selenium WebDriver instance for each test"""
    driver_instance = get_driver()
    if not driver_instance:
        pytest.skip("Browser not available")

    yield driver_instance

    driver_instance.quit()


@pytest.fixture(scope="session")
def api_token():
    """Provide API token for the session"""
    token = get_api_token()
    if not token:
        pytest.skip("API token not available")
    return token


@pytest.fixture(scope="session")
def base_url():
    """Provide base URL for UI"""
    return BASE_URL


@pytest.fixture(scope="session")
def api_base_url():
    """Provide base URL for API"""
    return API_BASE_URL
