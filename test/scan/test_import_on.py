"""
Tests for the IMPORT_ON reserved setting name (server/plugin.py:process_plugin_events()).

IMPORT_ON is an optional reserved setting: a plugin that never declares it
behaves exactly as today (always promote mapped_to_table rows into
CurrentScan). A plugin that declares it and has it set to a falsy value skips
only the CurrentScan promotion for this run - the plugin's own
Plugins_Objects/Plugins_Events/Plugins_History writes are unaffected.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    make_plugin_db,
    make_plugin_dict,
    make_plugin_event_row,
    plugin_objects_rows,
    CREATE_CURRENT_SCAN,
)

from plugin import process_plugin_events  # noqa: E402

PREFIX = "TESTPLG"


@pytest.fixture
def plugin_db():
    """PluginFakeDB backed by an in-memory SQLite DB that also has CurrentScan."""
    db, conn = make_plugin_db()
    conn.execute(CREATE_CURRENT_SCAN)
    conn.commit()
    yield db, conn
    conn.close()


def _mapped_plugin_dict(prefix: str) -> dict:
    """A plugin dict with mapped_to_table: CurrentScan, mapping objectPrimaryId -> scanMac."""
    plugin = make_plugin_dict(prefix)
    plugin["mapped_to_table"] = "CurrentScan"
    plugin["database_column_definitions"] = [
        {"column": "objectPrimaryId", "mapped_to_column": "scanMac"},
        {"column": "objectSecondaryId", "mapped_to_column": "scanLastIP"},
    ]
    return plugin


def _current_scan_macs(conn) -> set:
    cur = conn.cursor()
    cur.execute("SELECT scanMac FROM CurrentScan")
    return {r[0] for r in cur.fetchall()}


def _settings(import_on_value):
    """Monkeypatch target: <PREFIX>_IMPORT_ON -> import_on_value, _REPORT_ON -> [], else ''."""
    def _get(key, default=""):
        if key.endswith("_IMPORT_ON"):
            return import_on_value
        if key.endswith("_REPORT_ON"):
            return []
        return default
    return _get


class TestImportOnUndeclared:
    """A plugin that never declares IMPORT_ON must behave exactly like today."""

    def test_currentscan_promotion_happens_by_default(self, plugin_db, monkeypatch):
        db, conn = plugin_db
        # get_setting_value(default=None) for an undeclared setting must return
        # the passed default (None here) - simulate that "never declared" reality.
        monkeypatch.setattr("plugin.get_setting_value", _settings(None))

        plugin = _mapped_plugin_dict(PREFIX)
        events = [make_plugin_event_row(PREFIX, "aa:bb:cc:dd:ee:01", secondary_id="1.2.3.4")]

        process_plugin_events(db, plugin, events)

        assert _current_scan_macs(conn) == {"aa:bb:cc:dd:ee:01"}
        assert len(plugin_objects_rows(conn, PREFIX)) == 1


class TestImportOnDeclaredTrue:
    def test_currentscan_promotion_happens(self, plugin_db, monkeypatch):
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _settings(True))

        plugin = _mapped_plugin_dict(PREFIX)
        events = [make_plugin_event_row(PREFIX, "aa:bb:cc:dd:ee:02", secondary_id="1.2.3.4")]

        process_plugin_events(db, plugin, events)

        assert _current_scan_macs(conn) == {"aa:bb:cc:dd:ee:02"}


class TestImportOnDeclaredFalse:
    """The core behavior this mechanism exists for."""

    def test_currentscan_promotion_skipped_but_plugin_tables_still_populate(
        self, plugin_db, monkeypatch
    ):
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _settings(False))

        plugin = _mapped_plugin_dict(PREFIX)
        events = [make_plugin_event_row(PREFIX, "aa:bb:cc:dd:ee:03", secondary_id="1.2.3.4")]

        process_plugin_events(db, plugin, events)

        assert _current_scan_macs(conn) == set(), (
            "IMPORT_ON=False must skip the CurrentScan promotion"
        )
        assert len(plugin_objects_rows(conn, PREFIX)) == 1, (
            "the plugin's own Plugins_Objects write must be unaffected by IMPORT_ON"
        )

    def test_zero_is_also_falsy(self, plugin_db, monkeypatch):
        """Settings are often stored/typed as 0/1, not Python bool - 0 must gate too."""
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _settings(0))

        plugin = _mapped_plugin_dict(PREFIX)
        events = [make_plugin_event_row(PREFIX, "aa:bb:cc:dd:ee:04")]

        process_plugin_events(db, plugin, events)

        assert _current_scan_macs(conn) == set()


class TestImportOnScopedToCurrentScanOnly:
    """IMPORT_ON's documented purpose is gating CurrentScan promotion only -
    found in review that the original gate checked import_disabled alone,
    without scoping it to mapped_to_table == 'CurrentScan'. No plugin maps
    to another table today, but the gate must not silently widen to one that
    does in the future."""

    def test_non_currentscan_destination_still_written_when_import_on_false(
        self, plugin_db, monkeypatch
    ):
        db, conn = plugin_db
        conn.execute("CREATE TABLE IF NOT EXISTS OtherTable (otMac TEXT, otIp TEXT)")
        conn.commit()
        monkeypatch.setattr("plugin.get_setting_value", _settings(False))

        plugin = make_plugin_dict(PREFIX)
        plugin["mapped_to_table"] = "OtherTable"
        plugin["database_column_definitions"] = [
            {"column": "objectPrimaryId", "mapped_to_column": "otMac"},
            {"column": "objectSecondaryId", "mapped_to_column": "otIp"},
        ]
        events = [make_plugin_event_row(PREFIX, "aa:bb:cc:dd:ee:05", secondary_id="1.2.3.4")]

        process_plugin_events(db, plugin, events)

        rows = conn.execute("SELECT otMac FROM OtherTable").fetchall()
        assert {r[0] for r in rows} == {"aa:bb:cc:dd:ee:05"}, (
            "IMPORT_ON only gates CurrentScan promotion - a plugin mapping to "
            "any other destination table must still be written regardless of it"
        )
