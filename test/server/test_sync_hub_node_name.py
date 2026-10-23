"""
Tests for utils.plugin_utils.get_sync_hub_node_name().

Regression coverage: server/plugin.py used filename.split(".")[2] to tag
plugin objects received from a sync node, but by the time the hub processes
them decode_and_rename_files() has renamed the file to
last_result.<PREFIX>.decoded.<NodeName>.<N>.log - so index 2 is the literal
"decoded", and every synced plugin object (e.g. a WIFICANARY detection from a
WiFi satellite) was stored with syncHubNodeName = "decoded" instead of the
node's name.

Run from inside the NetAlertX container (utils.plugin_utils imports conf,
logger and helper):

    pytest "test/server/test_sync_hub_node_name.py" -v
"""

import os
import sys

import pytest

INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

from utils.plugin_utils import get_sync_hub_node_name  # noqa: E402


@pytest.mark.parametrize(
    "filename, expected",
    [
        # What the hub actually processes: already decrypted and renamed
        ("last_result.WIFICANARY.decoded.satelite.6.log", "satelite"),
        # Same file before decode_and_rename_files() touches it
        ("last_result.WIFICANARY.encoded.satelite.6.log", "satelite"),
        ("last_result.ARPSCAN.decoded.Node_1.1.log", "Node_1"),
        # Node names containing dots must survive intact
        ("last_result.ARPSCAN.decoded.sat.office.12.log", "sat.office"),
    ],
)
def test_node_name_from_received_file(filename, expected):
    """A received node file yields the node's name, never the encoded/decoded marker."""
    assert get_sync_hub_node_name(filename) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "last_result.ARPSCAN.log",  # local plugin result
        "last_result.log",          # sync's own progress file
        "last_result.satelite.log",  # PULL-mode device dump (handled by sync.py, not here)
    ],
)
def test_local_result_file_has_no_node_name(filename):
    """Local result files are not tagged with any sync node."""
    assert get_sync_hub_node_name(filename) == ""
