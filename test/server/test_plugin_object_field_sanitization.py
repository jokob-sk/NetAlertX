"""
Tests for the sanitize-by-default pass in plugin_object_class.__init__.

A plugin's watchedValue*/extra/helpVal*/foreignKey fields are attacker-
influenced (parsed from network responses, headers, etc.) but persisted and
later rendered. plugin_object_class strips HTML tag-delimiter and control
characters from every mapped field by default; a column opts out via
config.json's "allow_raw_text": true, restricted to display-only types
(textarea_readonly) by
test/plugins/test_plugin_conventions.py::test_allow_raw_text_only_on_safe_types.

Run from inside the NetAlertX container - server/plugin.py isn't importable
standalone outside it (real conf/database/api imports).

    pytest "test/server/test_plugin_object_field_sanitization.py" -v
"""

import os
import sys

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server/plugins", f"{INSTALL_PATH}/server"])

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import make_plugin_event_row  # noqa: E402

import plugin as plugin_module  # noqa: E402
from plugin import plugin_object_class  # noqa: E402

PREFIX = "TESTPLG"
PAYLOAD = "<img src=x onerror=alert(1)>"
STRIPPED = "img src=x onerror=alert(1)"


def _publisher_plugin(allow_raw_text_on_watched2=False):
    """Shaped like a real publisher plugin's config.json: watchedValue2
    holds a raw API-response body, optionally marked allow_raw_text."""
    return {
        "unique_prefix": PREFIX,
        "settings": [],
        "database_column_definitions": [
            {"column": "watchedValue1", "type": "text"},
            {
                "column": "watchedValue2",
                "type": "textarea_readonly",
                "allow_raw_text": allow_raw_text_on_watched2,
            },
            {"column": "extra", "type": "text"},
            {"column": "helpVal1", "type": "text"},
        ],
    }


def _watched_publisher_plugin():
    """Same shape as _publisher_plugin, but declares watchedValue1 as a WATCH
    column so watchedIndxs/watchedHash actually get populated."""
    plugin = _publisher_plugin()
    plugin["settings"] = [{"function": "WATCH", "value": ["watchedValue1"]}]
    return plugin


def _non_mac_identity_plugin():
    """A non-MAC-primaryId plugin (e.g. sync.py's GUID-keyed objects) that
    declares objectPrimaryId/objectSecondaryId, so both go through the
    generic sanitize loop instead of normalize_mac()."""
    return {
        "unique_prefix": PREFIX,
        "settings": [],
        "database_column_definitions": [
            {"column": "objectPrimaryId", "type": "text"},
            {"column": "objectSecondaryId", "type": "text"},
        ],
    }


class TestIdsHashUsesSanitizedValues:
    def test_ids_hash_reflects_sanitized_primary_id_not_raw(self):
        """Same risk class as watchedHash: idsHash drives the merge/dedup
        loop in process_plugin_events(), so it must be computed from the
        sanitized primaryId/secondaryId, not a bypassed raw value."""
        plugin = _non_mac_identity_plugin()
        clean = plugin_object_class(plugin, make_plugin_event_row(PREFIX, "hello"))
        dirty = plugin_object_class(plugin, make_plugin_event_row(PREFIX, "<hello>"))
        assert clean.primaryId == dirty.primaryId == "hello"
        assert clean.idsHash == dirty.idsHash


class TestWatchedHashUsesSanitizedValues:
    def test_watched_hash_reflects_sanitized_value_not_raw(self):
        """Two raw watched1 values that sanitize to the same text must
        produce the same watchedHash - it has to be computed from self.watched1
        (post-sanitization), not objDbRow's raw value."""
        plugin = _watched_publisher_plugin()
        clean = plugin_object_class(plugin, make_plugin_event_row(PREFIX, "id1", watched1="hello"))
        dirty = plugin_object_class(plugin, make_plugin_event_row(PREFIX, "id1", watched1="<hello>"))
        assert clean.watched1 == dirty.watched1 == "hello"
        assert clean.watchedHash == dirty.watchedHash

    def test_watched_hash_still_differs_for_genuinely_different_values(self):
        plugin = _watched_publisher_plugin()
        a = plugin_object_class(plugin, make_plugin_event_row(PREFIX, "id1", watched1="hello"))
        b = plugin_object_class(plugin, make_plugin_event_row(PREFIX, "id1", watched1="world"))
        assert a.watchedHash != b.watchedHash


class TestDefaultSanitization:
    def test_watched_field_without_allow_raw_text_is_sanitized(self):
        row = make_plugin_event_row(PREFIX, "id1", watched2=PAYLOAD)
        obj = plugin_object_class(_publisher_plugin(), row)
        assert obj.watched2 == STRIPPED

    def test_extra_and_helpval_are_sanitized_by_default(self):
        row = make_plugin_event_row(PREFIX, "id1", extra=PAYLOAD, help_val1=PAYLOAD)
        obj = plugin_object_class(_publisher_plugin(), row)
        assert obj.extra == STRIPPED
        assert obj.helpVal1 == STRIPPED

    def test_clean_text_passes_through_unchanged(self):
        row = make_plugin_event_row(PREFIX, "id1", watched2="200 OK")
        obj = plugin_object_class(_publisher_plugin(), row)
        assert obj.watched2 == "200 OK"

    def test_preexisting_dirty_value_is_sanitized_on_readback(self):
        """A row already persisted with an unsanitized value before this
        mechanism shipped must be cleaned the next time it's read, not just
        at write time - __init__ runs on every DB read, not only on insert."""
        row = make_plugin_event_row(PREFIX, "id1", watched2=PAYLOAD)
        obj = plugin_object_class(_publisher_plugin(), row)
        assert "<" not in obj.watched2 and ">" not in obj.watched2


class TestAllowRawTextOptOut:
    def test_column_with_allow_raw_text_true_is_not_sanitized(self):
        row = make_plugin_event_row(PREFIX, "id1", watched2=PAYLOAD)
        obj = plugin_object_class(_publisher_plugin(allow_raw_text_on_watched2=True), row)
        assert obj.watched2 == PAYLOAD

    def test_other_fields_still_sanitized_when_one_column_opts_out(self):
        row = make_plugin_event_row(PREFIX, "id1", watched2=PAYLOAD, extra=PAYLOAD)
        obj = plugin_object_class(_publisher_plugin(allow_raw_text_on_watched2=True), row)
        assert obj.watched2 == PAYLOAD  # opted out
        assert obj.extra == STRIPPED  # no opt-out on this column


class TestForeignKeySanitization:
    """foreignKey has no database_column_definitions entry of its own (no
    config flag to attach an opt-out to) - always sanitized, unconditionally."""

    def test_mac_shaped_foreign_key_passes_unchanged(self):
        row = make_plugin_event_row(PREFIX, "id1", foreign_key="aa:bb:cc:dd:ee:ff")
        obj = plugin_object_class(_publisher_plugin(), row)
        assert obj.foreignKey == "aa:bb:cc:dd:ee:ff"

    def test_guid_shaped_foreign_key_passes_unchanged(self):
        guid = "550e8400-e29b-41d4-a716-446655440000"
        row = make_plugin_event_row(PREFIX, "id1", foreign_key=guid)
        obj = plugin_object_class(_publisher_plugin(), row)
        assert obj.foreignKey == guid

    def test_internet_sentinel_passes_unchanged(self):
        row = make_plugin_event_row(PREFIX, "id1", foreign_key="internet")
        obj = plugin_object_class(_publisher_plugin(), row)
        assert obj.foreignKey == "internet"

    def test_injection_payload_is_stripped_not_blanked(self):
        row = make_plugin_event_row(PREFIX, "id1", foreign_key=PAYLOAD)
        obj = plugin_object_class(_publisher_plugin(), row)
        assert obj.foreignKey == STRIPPED


class TestSanitizationLogging:
    def test_mylog_fires_when_value_changes(self, monkeypatch):
        calls = []
        monkeypatch.setattr(plugin_module, "mylog", lambda level, msg: calls.append((level, msg)))
        row = make_plugin_event_row(PREFIX, "id1", watched2=PAYLOAD)
        plugin_object_class(_publisher_plugin(), row)
        assert any(level == "none" and "watchedValue2" in msg for level, msg in calls)

    def test_mylog_does_not_fire_for_clean_values(self, monkeypatch):
        calls = []
        monkeypatch.setattr(plugin_module, "mylog", lambda level, msg: calls.append((level, msg)))
        row = make_plugin_event_row(PREFIX, "id1", watched2="200 OK", foreign_key="aa:bb:cc:dd:ee:ff")
        plugin_object_class(_publisher_plugin(), row)
        assert calls == []
