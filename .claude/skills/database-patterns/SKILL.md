---
name: database-patterns
description: Read before designing a feature that writes to the Devices table, adding audit/history logging, or choosing between a SQLite trigger and a Python hook. Covers the full Devices write-path inventory, the FIELD_SOURCE_MAP *Source attribution system, and event-sourced vs snapshot audit logging tradeoffs.
---

# Database Patterns

## Devices Table — Write-Path Inventory

Before implementing any feature that reads or writes the `Devices` table, audit ALL write paths. The table is modified from many locations — missing one path is a correctness bug.

**Known production write paths:**

| File | Function | Fields written |
|---|---|---|
| `server/models/device_instance.py` | `setDeviceData()` | All user-editable fields |
| `server/models/device_instance.py` | `updateField()` | Any single field (workflows) |
| `server/models/device_instance.py` | `updateDeviceColumn()` | Any single column |
| `server/models/device_instance.py` | `deleteDevices()` etc. | DELETE operations |
| `server/scan/device_handling.py` | `update_devices_data_from_scan()` | Scan-derived fields |
| `server/scan/device_handling.py` | `update_vendors_from_mac()` | `devVendor`, `devVendorSource` |
| `server/scan/device_handling.py` | Name resolution block | `devName`, `devFQDN`, `*Source` |
| `server/scan/device_handling.py` | `update_ipv4_ipv6()` | `devPrimaryIPv4`, `devPrimaryIPv6` |
| `server/scan/device_handling.py` | `update_icons_and_types()` | `devIcon`, `devType` |
| `server/scan/device_handling.py` | `update_presence_from_CurrentScan()` | `devPresentLastScan` |
| `server/scan/device_handling.py` | `update_devLastConnection_from_CurrentScan()` | `devLastConnection` |
| `server/scan/device_handling.py` | `update_devPresentLastScan_based_on_*()` | `devPresentLastScan` |
| `server/db/authoritative_handler.py` | `enforce_source_on_user_update()` | `*Source` columns |
| `server/db/authoritative_handler.py` | `lock_field()` / `unlock_field()` | `*Source` columns |
| `server/models/notification_instance.py` | `clearPendingEmailFlag()` | `devLastNotification` |
| `server/plugins/db_cleanup/script.py` | `cleanup_database()` | DELETE operations |

**Key insight:** Most scan functions use `sql.executemany()` — there is no per-row Python state available. Python hooks before/after executemany require a pre-fetch+diff pattern that is expensive and error-prone.

---

## Device Identity: `devMac` (today's PK) vs `devGUID` (the intended durable identity)

`devMac STRING(50) PRIMARY KEY NOT NULL COLLATE NOCASE` (`server/db/schema/app.sql`) is still the literal SQL primary key. `devGUID TEXT` (indexed via `idx_dev_guid`) is a plain column today, but per the maintainer it's the intended long-term durable identity, since MAC has known limits as an identifier that `devGUID` doesn't share (privacy MAC randomization on iOS/Android/Windows, virtualized/containerized interfaces sharing one physical MAC, multi-homed devices presenting several). `devGUID` already backs device-history grouping (`server/models/device_history_instance.py`) and workflow trigger lookups (`server/workflows/triggers.py`).

This is a gradual, in-progress migration, not a flag day. New code should resolve device identity from an already-fetched device row (which carries both `devMac` and `devGUID`) rather than assuming either field is *the* identifier, so it doesn't need rework as the migration progresses.

**One thing that will never migrate, regardless of how far the PK change goes:** `Plugins_Objects.objectPrimaryId`, `CurrentScan.scanMac`, and `Events.eveMac` are permanently MAC-keyed. A plugin discovers a device by scanning the network, so it can only ever report a MAC address, never an app-internal `devGUID` NetAlertX hasn't assigned yet at scan time. This isn't a migration gap to eventually close; it's a structural ceiling on what network-originated data can ever identify a device by.

---

## `*Source` Fields — Attribution System

The `FIELD_SOURCE_MAP` in `server/db/authoritative_handler.py` defines 10 fields that carry write attribution via paired `*Source` columns:

```python
FIELD_SOURCE_MAP = {
    "devMac":           "devMacSource",
    "devName":          "devNameSource",
    "devFQDN":          "devFQDNSource",
    "devLastIP":        "devLastIPSource",
    "devVendor":        "devVendorSource",
    "devSSID":          "devSSIDSource",
    "devParentMAC":     "devParentMACSource",
    "devParentPort":    "devParentPortSource",
    "devParentRelType": "devParentRelTypeSource",
    "devVlan":          "devVlanSource",
}
```

`*Source` values: `'USER'`, `'LOCKED'`, `'NEWDEV'`, or a plugin prefix (e.g., `'ARPSCAN'`, `'NSLOOKUP'`).

These fields are updated **in the same transaction** as the primary field. A SQLite `AFTER UPDATE` trigger can read `NEW.devNameSource` to obtain correct attribution without any extra context-passing.

**Attribution rules for features that need `changedBy`:**

| Field category | Attribution |
|---|---|
| In `FIELD_SOURCE_MAP` | `COALESCE(NULLIF(NEW.<field>Source, ''), 'system')` |
| User-only fields (`devGroup`, `devComments`, `devFavorite`, `devOwner`, `devLocation`, etc.) | `'user:api'` — only `setDeviceData()` writes these |
| Auto-computed fields (`devIcon`, `devType`, `devPrimaryIPv4`, `devPrimaryIPv6`) | `'system'` |
| `*Source` fields themselves | `'system'` |

---

## Cross-Cutting Concerns — Prefer SQLite Triggers Over Python Hooks

When a feature needs to intercept **every write** to the `Devices` table (audit logging, computed columns, cascading logic), prefer a **SQLite `AFTER UPDATE` / `AFTER INSERT` trigger** over Python-layer hooks.

**Why:**
- Triggers catch all 14+ write paths automatically, including `executemany()` bulk updates
- Zero modifications to existing write-path functions (DRY)
- Self-healing: future write paths are automatically covered
- Attribution is available via `NEW.*Source` fields (see above)

**When Python hooks are still appropriate:**
- The logic needs access to Python objects, settings, or services not available in SQL
- The feature only fires from one or two known write paths
- The logic is too complex to express in SQL (multi-table joins with app-layer business logic)

### Trigger Performance Pattern

```sql
CREATE TRIGGER trg_example
AFTER UPDATE ON Devices
FOR EACH ROW
-- Guard: short-circuit entire body when feature is disabled (zero cost)
WHEN (SELECT CAST(setValue AS INTEGER) FROM Settings WHERE setKey = 'FEATURE_ENABLED') > 0
BEGIN
  -- Per-field conditional insert
  INSERT INTO SomeTable (devGUID, column, oldVal, newVal, changedBy, ts)
  SELECT NEW.devGUID, 'devName', OLD.devName, NEW.devName,
         COALESCE(NULLIF(NEW.devNameSource, ''), 'system'),
         datetime('now', 'utc')
  WHERE OLD.devName IS NOT NEW.devName
    AND instr(',' || (SELECT setValue FROM Settings WHERE setKey = 'TRACKED_FIELDS') || ',', ',devName,') > 0;
  -- Repeat for each tracked field...
END;
```

**Performance:** The Settings table is tiny (~100 rows) and stays in SQLite's page cache. Per-row Settings reads inside triggers are effectively in-memory lookups. The `WHEN` guard makes the disabled state zero-cost.

---

## Snapshot vs Event-Sourced Audit Logging

When implementing change history, always use **event-sourced (per-field rows)** not **snapshots (full row copies)**.

| | Event-sourced | Snapshot |
|---|---|---|
| Storage | Small — only changed fields | Large — all 40+ columns every mutation |
| Filter by field | O(log n) via index | O(n) — must diff every adjacent pair |
| Filter by source | O(log n) via index | Not possible without diffing |
| `changedBy` attribution | Embedded at write time | Not available without extra context |
| Retention calculation | Simple timestamp DELETE | Same, but much higher storage |

At 1000 devices, 5-min scan interval, 14-day retention: snapshot storage ≈ 280 MB/day. Event-sourced storage for the same workload is typically <1 MB/day (most scans produce no tracked field changes).

---

## `DevicesHistory` Table — Reference Schema

```sql
CREATE TABLE IF NOT EXISTS DevicesHistory (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    devGUID      TEXT NOT NULL,
    timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
    changedBy    TEXT NOT NULL,
    changedColumn TEXT NOT NULL,
    oldValue     TEXT,
    newValue     TEXT,
    FOREIGN KEY (devGUID) REFERENCES Devices(devGUID) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_devhist_guid_column ON DevicesHistory(devGUID, changedColumn);
CREATE INDEX IF NOT EXISTS idx_devhist_timestamp   ON DevicesHistory(timestamp);
```
