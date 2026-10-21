"""
Tests for scanPresence (server/scan/device_handling.py:update_presence_from_CurrentScan(),
server/scan/session_events.py:insert_events() "New Connections" query, and the
raw Sessions insert inside create_new_devices()).

scanPresence = 0 means "this row makes no presence claim" (identity/inventory
data), not "this device is offline" - semantics are abstain, not override: a
contradicting row from another plugin for the same MAC in the same cycle
still wins. Multiple call sites independently re-derive "is this MAC
currently present" from CurrentScan and all needed the same treatment - see
the scan-pipeline skill's gotcha on this.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    make_db,
    make_current_scan_dict,
    insert_current_scan_row_from_dict,
    insert_device,
    make_device_dict,
    insert_device_from_dict,
    minutes_ago,
    DummyDB,
    down_event_macs,
)

from server.scan import device_handling  # noqa: E402
from server.scan.session_events import insert_events, pair_sessions_events, create_sessions_snapshot  # noqa: E402

MAC = "aa:bb:cc:dd:ee:01"


def _present(db: DummyDB, mac: str) -> int:
    row = db._conn.execute(
        "SELECT devPresentLastScan FROM Devices WHERE devMac = ?", (mac,)
    ).fetchone()
    return row["devPresentLastScan"]


class TestPresenceGateOnExistingDevice:
    """update_presence_from_CurrentScan() - the badge/devPresentLastScan side."""

    def test_default_presence_one_preserves_today(self):
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, present_last_scan=0)
        insert_current_scan_row_from_dict(conn, make_current_scan_dict(MAC))
        db = DummyDB(conn)

        device_handling.update_presence_from_CurrentScan(db)

        assert _present(db, MAC) == 1

    def test_presence_zero_does_not_assert_online(self):
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, present_last_scan=0)
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=0)
        )
        db = DummyDB(conn)

        device_handling.update_presence_from_CurrentScan(db)

        assert _present(db, MAC) == 0, (
            "scanPresence=0 must not claim the device is online, even though "
            "a row for it exists in CurrentScan"
        )

    def test_abstain_not_override_contradicting_row_wins(self):
        """One plugin abstains (0), another asserts presence (1) for the same MAC."""
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, present_last_scan=0)
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanSourcePlugin="KEAAPI", scanPresence=0)
        )
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanSourcePlugin="ARPSCAN", scanPresence=1)
        )
        db = DummyDB(conn)

        device_handling.update_presence_from_CurrentScan(db)

        assert _present(db, MAC) == 1, "a contradicting presence=1 row must still win"


class TestDevLastConnectionRespectsPresence:
    """update_devLastConnection_from_CurrentScan() - found missing this check
    during review of a shipped commit: an inventory/reservation row was
    making offline devices look recently connected."""

    def test_presence_zero_does_not_bump_last_connection(self):
        conn = make_db()
        insert_device(
            conn, MAC, alert_down=1, present_last_scan=0,
            last_connection="2020-01-01 00:00:00",
        )
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=0)
        )
        db = DummyDB(conn)

        device_handling.update_devLastConnection_from_CurrentScan(db)

        row = conn.execute(
            "SELECT devLastConnection FROM Devices WHERE devMac = ?", (MAC,)
        ).fetchone()
        assert row["devLastConnection"] == "2020-01-01 00:00:00", (
            "a scanPresence=0 row must not make an offline device look recently connected"
        )

    def test_presence_one_still_bumps_last_connection(self):
        """Regression guard: default (1) preserves today's behavior."""
        conn = make_db()
        insert_device(
            conn, MAC, alert_down=1, present_last_scan=0,
            last_connection="2020-01-01 00:00:00",
        )
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=1)
        )
        db = DummyDB(conn)

        device_handling.update_devLastConnection_from_CurrentScan(db)

        row = conn.execute(
            "SELECT devLastConnection FROM Devices WHERE devMac = ?", (MAC,)
        ).fetchone()
        assert row["devLastConnection"] != "2020-01-01 00:00:00"

    def test_nic_derived_presence_still_bumps_last_connection(self):
        """nic-parent-orphan-disconnect-events PRD: a parent with no direct
        CurrentScan row, but a present NIC child, must still advance
        devLastConnection - it is not actually offline."""
        conn = make_db()
        parent_mac = "aa:22:00:00:00:01"
        nic_mac = "bb:22:00:00:00:01"
        insert_device_from_dict(conn, make_device_dict(
            parent_mac, devLastConnection="2020-01-01 00:00:00",
            devParentMAC="", devParentRelType="", devReqNicsOnline=0,
        ))
        insert_device_from_dict(conn, make_device_dict(
            nic_mac, devParentMAC=parent_mac, devParentRelType="nic", devReqNicsOnline=0,
        ))
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(nic_mac, scanPresence=1)
        )
        db = DummyDB(conn)

        device_handling.update_devLastConnection_from_CurrentScan(db)

        row = conn.execute(
            "SELECT devLastConnection FROM Devices WHERE devMac = ?", (parent_mac,)
        ).fetchone()
        assert row["devLastConnection"] != "2020-01-01 00:00:00"

    def test_unrelated_device_without_nics_not_falsely_bumped(self):
        """Regression: nic_derived_presence_condition() used to be callable
        with a bare, unqualified mac_column - Devices (this function's own
        inner scan) has a devMac column, so the unqualified reference always
        bound to the function's own inner row instead of the caller's,
        making every device with no NIC children of its own read as
        NIC-derived-present as soon as *any other* device anywhere in
        Devices legitimately had one. Two devices in one DB on purpose - a
        single-device DB can't distinguish "per-row correct" from
        "table-wide tautology"."""
        conn = make_db()
        parent_mac = "aa:22:00:00:00:03"
        nic_mac = "bb:22:00:00:00:03"
        unrelated_mac = "cc:22:00:00:00:03"
        insert_device_from_dict(conn, make_device_dict(
            parent_mac, devLastConnection="2020-01-01 00:00:00",
            devParentMAC="", devParentRelType="", devReqNicsOnline=0,
        ))
        insert_device_from_dict(conn, make_device_dict(
            nic_mac, devParentMAC=parent_mac, devParentRelType="nic", devReqNicsOnline=0,
        ))
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(nic_mac, scanPresence=1)
        )
        insert_device_from_dict(conn, make_device_dict(
            unrelated_mac, devLastConnection="2020-01-01 00:00:00",
            devParentMAC="", devParentRelType="", devReqNicsOnline=0,
        ))
        db = DummyDB(conn)

        device_handling.update_devLastConnection_from_CurrentScan(db)

        parent_row = conn.execute(
            "SELECT devLastConnection FROM Devices WHERE devMac = ?", (parent_mac,)
        ).fetchone()
        unrelated_row = conn.execute(
            "SELECT devLastConnection FROM Devices WHERE devMac = ?", (unrelated_mac,)
        ).fetchone()
        assert parent_row["devLastConnection"] != "2020-01-01 00:00:00", (
            "the actual NIC-covered parent must still bump"
        )
        assert unrelated_row["devLastConnection"] == "2020-01-01 00:00:00", (
            "a device with no NIC children of its own must not be bumped just "
            "because some other device in Devices has NIC-derived presence"
        )


class TestNewConnectionsRespectsPresence:
    """insert_events()'s New Connections query must not fire Connected for a
    scanPresence=0-only row - this is what would otherwise leave a session
    open forever with no way to close it (see the scan-pipeline skill)."""

    def test_presence_zero_brand_new_device_no_connected_event(self):
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=0)
        )
        db = DummyDB(conn)

        insert_events(db)

        rows = conn.execute(
            "SELECT * FROM Events WHERE eveMac = ? AND eveEventType IN ('Connected','Down Reconnected')",
            (MAC,),
        ).fetchall()
        assert rows == [], "scanPresence=0 must not generate a Connected event"


class TestNewConnectionsNoOrphanForCreatesDeviceZero:
    """A never-before-seen MAC reported only by scanCreatesDevice=0 rows must
    not get a Connected event either - create_new_devices() will never turn
    it into a Devices row, so the event would be a permanent orphan (shows up
    in Events_Devices via its LEFT JOIN with every devName/devVendor field
    NULL). Distinct from TestNewConnectionsRespectsPresence: this MAC does
    assert presence, it's the creation gate that must suppress it."""

    def test_unknown_mac_creates_device_zero_no_connected_event(self):
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=1, scanCreatesDevice=0)
        )
        db = DummyDB(conn)

        insert_events(db)

        rows = conn.execute(
            "SELECT * FROM Events WHERE eveMac = ? AND eveEventType IN ('Connected','Down Reconnected')",
            (MAC,),
        ).fetchall()
        assert rows == [], (
            "a MAC with no Devices row that will never get one "
            "(scanCreatesDevice=0 on every contributing row) must not get a Connected event"
        )

    def test_unknown_mac_creates_device_one_still_connects(self):
        """Regression guard for the fix above: insert_events() runs before
        create_new_devices(), so a legitimately new device (scanCreatesDevice=1)
        also has no Devices row yet at this point - it must still get a
        Connected event same-cycle as its New Device event, unaffected by the
        orphan-suppression fix."""
        conn = make_db()
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=1, scanCreatesDevice=1)
        )
        db = DummyDB(conn)

        insert_events(db)

        rows = conn.execute(
            "SELECT * FROM Events WHERE eveMac = ? AND eveEventType = 'Connected'",
            (MAC,),
        ).fetchall()
        assert len(rows) == 1, (
            "a brand-new device that create_new_devices() will create later "
            "this same cycle must still get its Connected event"
        )

    def test_existing_device_reconnect_via_creates_device_zero_row_still_connects(self):
        """An already-existing device (created in a prior cycle) reconnecting
        this cycle only via an enrich-only-for-creation plugin must still get
        a Connected event - scanCreatesDevice only gates origination of new
        devices, not updates/reconnects of ones that already exist."""
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, present_last_scan=0)
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=1, scanCreatesDevice=0)
        )
        db = DummyDB(conn)

        insert_events(db)

        rows = conn.execute(
            "SELECT * FROM Events WHERE eveMac = ? AND eveEventType = 'Connected'",
            (MAC,),
        ).fetchall()
        assert len(rows) == 1, (
            "scanCreatesDevice=0 must not block a Connected event for a device "
            "that already exists"
        )


class TestOnlineToPresenceZeroTransitionClosesSession:
    """The regression this PRD review round specifically caught: a device
    going from online to a scanPresence=0-only report must still get a
    Device Down/Disconnected Event, or pair_sessions_events() never pairs a
    closing event and the session view shows it as open forever."""

    def test_device_down_fires_and_session_closes(self):
        conn = make_db()
        insert_device(
            conn, MAC, alert_down=1, present_last_scan=1,
            last_connection=minutes_ago(120),
        )
        # Open session, as if create_new_devices() opened it on first connect.
        conn.execute(
            """INSERT INTO Sessions
               (sesMac, sesIp, sesEventTypeConnection, sesDateTimeConnection,
                sesEventTypeDisconnection, sesDateTimeDisconnection, sesStillConnected, sesAdditionalInfo)
               VALUES (?, '192.168.1.10', 'Connected', ?, NULL, NULL, 1, '')""",
            (MAC, minutes_ago(120)),
        )
        conn.execute(
            "INSERT INTO Events (eveMac, eveIp, eveDateTime, eveEventType, eveAdditionalInfo, evePendingAlertEmail) "
            "VALUES (?, '192.168.1.10', ?, 'New Device', '', 1)",
            (MAC, minutes_ago(120)),
        )
        conn.commit()

        # This cycle: only a scanPresence=0 report for this MAC (e.g. an
        # inventory plugin) - device transitions from online to "no presence".
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=0)
        )
        db = DummyDB(conn)

        insert_events(db)

        assert MAC in down_event_macs(conn.cursor()), (
            "the Device Down query must fire even though a CurrentScan row "
            "still exists for this MAC (just with scanPresence=0) - without "
            "this the session below never gets a closing event to pair against"
        )

        pair_sessions_events(db)
        create_sessions_snapshot(db)

        row = conn.execute(
            "SELECT sesStillConnected FROM Sessions WHERE sesMac = ?", (MAC,)
        ).fetchone()
        assert row["sesStillConnected"] == 0, (
            "session must close (sesStillConnected=0) once the Device Down "
            "event exists and gets paired - this is the bug found in PRD review"
        )


class TestPresenceZeroSessionsInsertGate:
    """create_new_devices()'s raw INSERT INTO Sessions for already-existing
    reconnecting devices must respect scanPresence too."""

    def test_presence_zero_existing_device_no_open_session_inserted(self):
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, present_last_scan=0)
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=0)
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        rows = conn.execute(
            "SELECT * FROM Sessions WHERE sesMac = ? AND sesStillConnected = 1", (MAC,)
        ).fetchall()
        assert rows == [], "scanPresence=0 must not open a session for a reconnecting device"


class TestSessionsInsertNoDuplicatesAcrossPlugins:
    """create_new_devices()'s raw Sessions insert must collapse multiple
    presence-asserting plugin rows for the same reconnecting MAC into one
    session row - Sessions has no uniqueness constraint at all, so an
    unaggregated SELECT previously opened one row per distinct scanLastIP."""

    def test_differing_ip_across_plugins_collapses_to_one_session_row(self):
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, present_last_scan=0)
        insert_current_scan_row_from_dict(
            conn,
            make_current_scan_dict(
                MAC, scanSourcePlugin="ARPSCAN", scanLastIP="192.168.1.30"
            ),
        )
        insert_current_scan_row_from_dict(
            conn,
            make_current_scan_dict(
                MAC, scanSourcePlugin="DOCKER", scanLastIP="192.168.1.31"
            ),
        )
        db = DummyDB(conn)

        device_handling.create_new_devices(db)

        rows = conn.execute(
            "SELECT * FROM Sessions WHERE sesMac = ? AND sesStillConnected = 1", (MAC,)
        ).fetchall()
        assert len(rows) == 1, (
            "differing scanLastIP across plugin rows for the same reconnecting "
            "MAC must not open duplicate Sessions rows"
        )


class TestIpChangedRespectsPresence:
    """IP Changed query was found missing 'AND scanPresence = 1' entirely - a
    scanPresence=0 (abstain/inventory) row reporting a different IP must not
    fire an IP Changed event, consistent with scanPresence's abstain-not-
    override semantics used everywhere else in this file."""

    def test_presence_zero_differing_ip_no_ip_changed_event(self):
        conn = make_db()
        insert_device(conn, MAC, alert_down=1, present_last_scan=1, last_ip="192.168.1.10")
        insert_current_scan_row_from_dict(
            conn, make_current_scan_dict(MAC, scanPresence=0, scanLastIP="192.168.1.99")
        )
        db = DummyDB(conn)

        insert_events(db)

        rows = conn.execute(
            "SELECT * FROM Events WHERE eveMac = ? AND eveEventType = 'IP Changed'",
            (MAC,),
        ).fetchall()
        assert rows == [], "scanPresence=0 must not trigger an IP Changed event"
