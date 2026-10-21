"""Tests for forced device status updates."""

import os
import sys

from server.scan import device_handling

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_test_helpers import (  # noqa: E402
    DummyDB,
    insert_device_from_dict,
    make_db,
    make_device_dict,
)


def test_force_status_updates_present_flag():
    """Forced status should override devPresentLastScan for online/offline values."""
    conn = make_db()

    for mac, present_last_scan, force_status in [
        ("AA:AA:AA:AA:AA:01", 0, "online"),
        ("AA:AA:AA:AA:AA:02", 1, "offline"),
        ("AA:AA:AA:AA:AA:03", 1, "dont_force"),
        ("AA:AA:AA:AA:AA:04", 0, None),
        ("AA:AA:AA:AA:AA:05", 0, "ONLINE"),
    ]:
        insert_device_from_dict(
            conn,
            make_device_dict(
                mac, devPresentLastScan=present_last_scan, devForceStatus=force_status
            ),
        )

    db = DummyDB(conn)
    updated = device_handling.update_devPresentLastScan_based_on_force_status(db)

    rows = {
        row["devMac"]: row["devPresentLastScan"]
        for row in conn.execute("SELECT devMac, devPresentLastScan FROM Devices")
    }

    assert updated == 3
    assert rows["AA:AA:AA:AA:AA:01"] == 1
    assert rows["AA:AA:AA:AA:AA:02"] == 0
    assert rows["AA:AA:AA:AA:AA:03"] == 1
    assert rows["AA:AA:AA:AA:AA:04"] == 0
    assert rows["AA:AA:AA:AA:AA:05"] == 1

    conn.close()
