from urllib.parse import urljoin, urlparse

import pytest

from api_server.api_server_start import app
from helper import get_setting_value


@pytest.fixture(scope="session")
def api_token():
    """Return the API token from the loaded config."""
    return get_setting_value("API_TOKEN")


@pytest.fixture
def client():
    """Yield a Flask test client for the API server."""
    with app.test_client() as client:
        yield client


def read_endpoint_event(client, api_token):
    """Open the MCP SSE stream and return the data of its first (endpoint) event."""
    response = client.get("/mcp/sse", headers={"Authorization": f"Bearer {api_token}"}, buffered=False)
    assert response.status_code == 200
    try:
        first_event = next(response.response)
    finally:
        response.close()
    if isinstance(first_event, bytes):
        first_event = first_event.decode()
    lines = first_event.strip().splitlines()
    assert lines[0] == "event: endpoint"
    return lines[1].removeprefix("data: ")


@pytest.mark.parametrize("sse_url, expected_path", [
    ("http://host:20212/mcp/sse", "/mcp/messages"),
    ("http://host:20211/server/mcp/sse", "/server/mcp/messages"),
])
def test_sse_endpoint_resolves_to_messages_route(client, api_token, sse_url, expected_path):
    """The advertised endpoint must resolve to the messages route both directly and behind the /server proxy prefix."""
    endpoint = read_endpoint_event(client, api_token)
    resolved = urlparse(urljoin(sse_url, endpoint))
    assert resolved.path == expected_path
    assert resolved.query.startswith("session_id=")
