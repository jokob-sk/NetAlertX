#!/usr/bin/env python3
"""
Shared test utilities and configuration
"""

import os
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Configuration
BASE_URL = os.getenv("UI_BASE_URL", "http://localhost:20211")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:20212")

def get_api_token():
    """Get API token from config file"""
    config_path = "/data/config/app.conf"
    try:
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('API_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    # Remove both single and double quotes
                    token = token.strip('"').strip("'")
                    return token
    except FileNotFoundError:
        print(f"⚠ Config file not found: {config_path}")
    return None

def get_driver(download_dir=None):
    """Create a Selenium WebDriver for Chrome/Chromium

    Args:
        download_dir: Optional directory for downloads. If None, uses /tmp/selenium_downloads
    """
    import os
    import subprocess

    # Check if chromedriver exists
    chromedriver_paths = ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver']
    chromium_paths = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']

    chromedriver = None
    for path in chromedriver_paths:
        if os.path.exists(path):
            chromedriver = path
            break

    chromium = None
    for path in chromium_paths:
        if os.path.exists(path):
            chromium = path
            break

    if not chromedriver:
        print(f"⚠ chromedriver not found in {chromedriver_paths}")
        return None

    if not chromium:
        print(f"⚠ chromium not found in {chromium_paths}")
        return None

    # Setup download directory
    if download_dir is None:
        download_dir = "/tmp/selenium_downloads"
    os.makedirs(download_dir, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.binary_location = chromium

    # Configure downloads
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        service = Service(chromedriver)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.download_dir = download_dir  # Store for later use
        return driver
    except Exception as e:
        print(f"⚠ Could not start Chromium: {e}")
        import traceback
        traceback.print_exc()
        return None

def api_get(endpoint, api_token, timeout=5):
    """Make GET request to API - endpoint should be path only (e.g., '/devices')"""
    headers = {"Authorization": f"Bearer {api_token}"}
    # Handle both full URLs and path-only endpoints
    url = endpoint if endpoint.startswith('http') else f"{API_BASE_URL}{endpoint}"
    return requests.get(url, headers=headers, timeout=timeout)

def api_post(endpoint, api_token, data=None, timeout=5):
    """Make POST request to API - endpoint should be path only (e.g., '/devices')"""
    headers = {"Authorization": f"Bearer {api_token}"}
    # Handle both full URLs and path-only endpoints
    url = endpoint if endpoint.startswith('http') else f"{API_BASE_URL}{endpoint}"
    return requests.post(url, headers=headers, json=data, timeout=timeout)
