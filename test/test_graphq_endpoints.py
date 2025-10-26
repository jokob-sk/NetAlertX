import sys
import pathlib
import sqlite3
import random
import string
import uuid
import pytest
from datetime import datetime, timedelta

INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/front/plugins", f"{INSTALL_PATH}/server"])

from helper import timeNowTZ, get_setting_value
from api_server.api_server_start import app

@pytest.fixture(scope="session")
def api_token():
    return get_setting_value("API_TOKEN")

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_mac():
    # Generate a unique MAC for each test run
    return "AA:BB:CC:" + ":".join(f"{random.randint(0,255):02X}" for _ in range(3))

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_graphql_debug_get(client):
    """GET /graphql should return the debug string"""
    resp = client.get("/graphql")
    assert resp.status_code == 200
    assert resp.data.decode() == "NetAlertX GraphQL server running."

def test_graphql_post_unauthorized(client):
    """POST /graphql without token should return 401"""
    query = {"query": "{ devices { devName devMac } }"}
    resp = client.post("/graphql", json=query)
    assert resp.status_code == 401
    assert "Unauthorized access attempt" in resp.json.get("error", "")

def test_graphql_post_devices(client, api_token):
    """POST /graphql with a valid token should return device data"""
    query = {
        "query": """
        {
            devices {
                devices { 
                    devGUID
                    devGroup
                    devIsRandomMac
                    devParentChildrenCount
                }
                count
            }
        }
        """
    }
    resp = client.post("/graphql", json=query, headers=auth_headers(api_token))
    assert resp.status_code == 200

    body = resp.get_json()

    # GraphQL spec: response always under "data"
    assert "data" in body
    data = body["data"]

    assert "devices" in data
    assert isinstance(data["devices"]["devices"], list)
    assert isinstance(data["devices"]["count"], int)

def test_graphql_post_settings(client, api_token):
    """POST /graphql should return settings data"""
    query = {
        "query": """
        {
            settings {
                settings { setKey setValue setGroup }
                count
            }
        }
        """
    }
    resp = client.post("/graphql", json=query, headers=auth_headers(api_token))
    assert resp.status_code == 200
    data = resp.json.get("data", {})
    assert "settings" in data
    assert isinstance(data["settings"]["settings"], list)
