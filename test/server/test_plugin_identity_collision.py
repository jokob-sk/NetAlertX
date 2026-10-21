"""
Tests for the identity-hash collision guard in process_plugin_events().

If two events in the same plugin run resolve to the same idsHash (same
sanitized primaryId + secondaryId), nothing in the merge loop expects that -
merging both into the same Plugins_Objects row would silently conflate two
distinct discovered identities. process_plugin_events() now rejects the
whole run's batch (persists nothing) when this happens, without picking a
winner, and leaves a run with no collision unaffected.

Run from inside the NetAlertX container - server/plugin.py isn't importable
standalone outside it (real conf/database/api imports).

    pytest "test/server/test_plugin_identity_collision.py" -v
"""

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    make_plugin_db,
    make_plugin_dict,
    make_plugin_event_row,
    seed_plugin_object,
    plugin_objects_rows,
)

import plugin as plugin_module  # noqa: E402
from plugin import process_plugin_events  # noqa: E402

PREFIX = "TESTPLG"


@pytest.fixture
def plugin_db():
    """Yield a (PluginFakeDB, connection) backed by an in-memory SQLite database."""
    db, conn = make_plugin_db()
    yield db, conn
    conn.close()


def _no_report_on(key, default=""):
    """Monkeypatch target: return empty REPORT_ON so no events are generated."""
    if key.endswith("_REPORT_ON"):
        return []
    return default


class TestCollisionRejectsWholeBatch:
    def test_colliding_events_persist_nothing(self, plugin_db, monkeypatch):
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _no_report_on)

        plugin = make_plugin_dict(PREFIX)
        events = [
            make_plugin_event_row(PREFIX, "device_A", secondary_id="sec"),
            make_plugin_event_row(PREFIX, "device_A", secondary_id="sec", watched1="different"),
        ]

        process_plugin_events(db, plugin, events)

        assert plugin_objects_rows(conn, PREFIX) == []

    def test_collision_does_not_touch_preexisting_objects(self, plugin_db, monkeypatch):
        """A rejected batch must not modify unrelated, already-persisted
        objects from prior runs either."""
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _no_report_on)

        cur = conn.cursor()
        seed_plugin_object(cur, PREFIX, "existing_device", watched1="val1",
                           status="watched-not-changed")
        conn.commit()

        plugin = make_plugin_dict(PREFIX)
        events = [
            make_plugin_event_row(PREFIX, "device_A", secondary_id="sec"),
            make_plugin_event_row(PREFIX, "device_A", secondary_id="sec"),
        ]

        process_plugin_events(db, plugin, events)

        rows = plugin_objects_rows(conn, PREFIX)
        assert len(rows) == 1
        assert rows[0][2] == "existing_device"

    def test_collision_logged_via_mylog_none(self, plugin_db, monkeypatch):
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _no_report_on)
        calls = []
        monkeypatch.setattr(plugin_module, "mylog", lambda level, msg: calls.append((level, msg)))

        plugin = make_plugin_dict(PREFIX)
        events = [
            make_plugin_event_row(PREFIX, "device_A", secondary_id="sec"),
            make_plugin_event_row(PREFIX, "device_A", secondary_id="sec"),
        ]

        process_plugin_events(db, plugin, events)

        assert any(level == "none" and "collision" in msg for level, msg in calls)


class TestNoCollisionBehavesAsBefore:
    def test_distinct_events_persist_normally(self, plugin_db, monkeypatch):
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _no_report_on)

        plugin = make_plugin_dict(PREFIX)
        events = [
            make_plugin_event_row(PREFIX, "device_A"),
            make_plugin_event_row(PREFIX, "device_B"),
        ]

        process_plugin_events(db, plugin, events)

        rows = plugin_objects_rows(conn, PREFIX)
        ids = {r[2] for r in rows}
        assert ids == {"device_A", "device_B"}

    def test_concatenation_boundary_shift_is_not_a_false_collision(self, plugin_db, monkeypatch):
        """idsHash hashes the (primaryId, secondaryId) pair, not their string
        concatenation - ("ab", "c") and ("a", "bc") both concatenate to "abc",
        which would wrongly hash identically and trip the collision guard,
        rejecting a legitimate batch that has no real duplicate in it."""
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _no_report_on)

        plugin = make_plugin_dict(PREFIX)
        events = [
            make_plugin_event_row(PREFIX, "ab", secondary_id="c"),
            make_plugin_event_row(PREFIX, "a", secondary_id="bc"),
        ]

        process_plugin_events(db, plugin, events)

        rows = plugin_objects_rows(conn, PREFIX)
        pairs = {(r[2], r[3]) for r in rows}  # (objectPrimaryId, objectSecondaryId)
        assert pairs == {("ab", "c"), ("a", "bc")}

    def test_event_matching_a_preexisting_object_is_not_a_collision(self, plugin_db, monkeypatch):
        """The collision check only compares events against each other, not
        against pre-existing Plugins_Objects rows - matching an existing
        object is the normal "exists" path, not a collision."""
        db, conn = plugin_db
        monkeypatch.setattr("plugin.get_setting_value", _no_report_on)

        cur = conn.cursor()
        seed_plugin_object(cur, PREFIX, "device_A", watched1="val1",
                           status="watched-not-changed")
        conn.commit()

        plugin = make_plugin_dict(PREFIX)
        events = [make_plugin_event_row(PREFIX, "device_A", watched1="val1")]

        process_plugin_events(db, plugin, events)

        rows = plugin_objects_rows(conn, PREFIX)
        assert len(rows) == 1
        assert rows[0][2] == "device_A"
