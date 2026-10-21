"""
Tests for MAC normalization on the CurrentScan-promotion path
(server/plugin.py:process_plugin_events()).

scanMac is normally already lowercase by the time this code runs -
plugin_object_class.__init__ normalizes objectPrimaryId via
primary_id_is_mac(), and every current CurrentScan-mapped plugin declares
"type": "device_mac"/"device_name_mac" on that column - so covering it here
too is defense-in-depth for a plugin that omits that type annotation.

scanParentMAC has no such upstream normalization at all (primary_id_is_mac()
only ever checks objectPrimaryId) - this is the column these tests actually
exist to cover, since none of the ~22 real plugins mapping to it call
normalize_mac() in their own script.py.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    make_plugin_db,
    make_plugin_dict,
    make_plugin_event_row,
    CREATE_CURRENT_SCAN,
)

from plugin import process_plugin_events  # noqa: E402

PREFIX = "TESTPLG"


def _plugin_with_parentmac_mapping(prefix: str) -> dict:
    """A plugin dict mapping objectPrimaryId -> scanMac and helpVal1 -> scanParentMAC,
    matching the real shape used by e.g. unifi_import/omada_sdn_imp/rest_import."""
    plugin = make_plugin_dict(prefix)
    plugin["mapped_to_table"] = "CurrentScan"
    plugin["database_column_definitions"] = [
        {"column": "objectPrimaryId", "mapped_to_column": "scanMac", "type": "device_mac"},
        {"column": "helpVal1", "mapped_to_column": "scanParentMAC"},
    ]
    return plugin


def _current_scan_row(conn):
    cur = conn.cursor()
    cur.execute("SELECT scanMac, scanParentMAC FROM CurrentScan")
    return cur.fetchone()


def _plugin_db():
    db, conn = make_plugin_db()
    conn.execute(CREATE_CURRENT_SCAN)
    conn.commit()
    return db, conn


class TestScanMacNormalization:
    def test_uppercase_scanmac_is_lowercased(self):
        db, conn = _plugin_db()
        try:
            plugin = _plugin_with_parentmac_mapping(PREFIX)
            row = make_plugin_event_row(PREFIX, "AA:BB:CC:DD:EE:01")
            process_plugin_events(db, plugin, [row])

            scan_mac, _ = _current_scan_row(conn)
            assert scan_mac == "aa:bb:cc:dd:ee:01"
        finally:
            conn.close()


class TestScanParentMacNormalization:
    """The real coverage gap: scanParentMAC has no upstream normalization,
    unlike scanMac (see module docstring)."""

    def test_uppercase_scanparentmac_is_lowercased(self):
        db, conn = _plugin_db()
        try:
            plugin = _plugin_with_parentmac_mapping(PREFIX)
            row = make_plugin_event_row(
                PREFIX, "aa:bb:cc:dd:ee:01", help_val1="AA:BB:CC:DD:EE:99"
            )
            process_plugin_events(db, plugin, [row])

            _, parent_mac = _current_scan_row(conn)
            assert parent_mac == "aa:bb:cc:dd:ee:99"
        finally:
            conn.close()

    def test_empty_scanparentmac_left_empty_not_corrupted(self):
        """normalize_mac(None)/normalize_mac('') must not be applied to a
        falsy value - guards the truthy check in process_plugin_events()'s
        normalization step against turning an unset parent MAC into garbage
        (e.g. normalize_mac(None) would otherwise produce 'no:ne')."""
        db, conn = _plugin_db()
        try:
            plugin = _plugin_with_parentmac_mapping(PREFIX)
            row = make_plugin_event_row(
                PREFIX, "aa:bb:cc:dd:ee:01", help_val1=""
            )
            process_plugin_events(db, plugin, [row])

            _, parent_mac = _current_scan_row(conn)
            assert parent_mac == ""
        finally:
            conn.close()
