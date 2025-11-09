# Plugins Implementation Details

Plugins provide data to the NetAlertX core, which processes it to detect changes, discover new devices, raise alerts, and apply heuristics.

---

## Overview: Plugin Data Flow

1. Each plugin runs on a defined schedule.
2. Aligning all plugin schedules is recommended so they execute in the same loop.
3. During execution, all plugins write their collected data into the **`CurrentScan`** table.
4. After all plugins complete, the `CurrentScan` table is evaluated to detect **new devices**, **changes**, and **triggers**.

Although plugins run independently, they contribute to the shared `CurrentScan` table.
To inspect its contents, set `LOG_LEVEL=trace` and check for the log section:

```
================ CurrentScan table content ================
```

---

## `config.json` Lifecycle

This section outlines how each plugin’s `config.json` manifest is read, validated, and used by the core and plugins.
It also describes plugin output expectations and the main plugin categories.

> [!TIP]
> For detailed schema and examples, see the [Plugin Development Guide](PLUGINS_DEV.md).

---

### 1. Loading

* On startup, the core loads `config.json` for each plugin.
* The file acts as a **plugin manifest**, defining metadata, runtime configuration, and database mappings.

---

### 2. Validation

* The core validates required keys (for example, `RUN`).
* Missing or invalid entries may be replaced with defaults or cause the plugin to be disabled.

---

### 3. Preparation

* Plugin parameters (paths, commands, and options) are prepared for execution.
* Database mappings (`mapped_to_table`, `database_column_definitions`) are parsed to define how data integrates with the main app.

---

### 4. Execution

* Plugins may run:

  * On a fixed schedule.
  * Once at startup.
  * After a notification or other trigger.
* The scheduler executes plugins according to their `interval`.

---

### 5. Parsing

* Plugin output must be **pipe-delimited (`|`)**.
* The core parses each output line following the **Plugin Interface Contract**, splitting and mapping fields accordingly.

---

### 6. Mapping

* Parsed fields are inserted into the plugin’s `Plugins_*` table.
* Data can be mapped into other tables (e.g., `Devices`, `CurrentScan`) as defined by:

  * `database_column_definitions`
  * `mapped_to_table`

**Example:** `Object_PrimaryID → devMAC`

---

### 6a. Plugin Output Contract

All plugins must follow the **Plugin Interface Contract** defined in `PLUGINS_DEV.md`.
Output values are pipe-delimited in a fixed order.

#### Identifiers

* `Object_PrimaryID` and `Object_SecondaryID` uniquely identify records (for example, `MAC|IP`).

#### Watched Values (`Watched_Value1–4`)

* Used by the core to detect changes between runs.
* Changes in these fields can trigger notifications.

#### Extra Field (`Extra`)

* Optional additional value.
* Stored in the database but not used for alerts.

#### Helper Values (`Helper_Value1–3`)

* Optional auxiliary data (for display or plugin logic).
* Stored but not alert-triggering.

#### Mapping

* While the output format is flexible, the plugin’s manifest determines the destination and type of each field.

---

### 7. Persistence

* Parsed data is **upserted** into the database.
* Conflicts are resolved using the combined key: `Object_PrimaryID + Object_SecondaryID`.

---

## Plugin Categories

Plugins fall into several functional categories depending on their purpose and expected outputs.

### 1. Device Discovery Plugins

* **Inputs:** None, subnet, or discovery API.
* **Outputs:** `MAC` and `IP` for new or updated device records in `Devices`.
* **Mapping:** Required – usually into `CurrentScan`.
* **Examples:** `ARPSCAN`, `NMAPDEV`.

---

### 2. Device Data Enrichment Plugins

* **Inputs:** Device identifiers (`MAC`, `IP`).
* **Outputs:** Additional metadata (for example, open ports or sensors).
* **Mapping:** Controlled via manifest definitions.
* **Examples:** `NMAP`, `MQTT`.

---

### 3. Name Resolver Plugins

* **Inputs:** Device identifiers (`MAC`, `IP`, hostname`).
* **Outputs:** Updated `devName` and `devFQDN`.
* **Mapping:** Typically none.
* **Note:** Adding new resolvers currently requires a core change.
* **Examples:** `NBTSCAN`, `NSLOOKUP`.

---

### 4. Generic Plugins

* **Inputs:** Custom, based on the plugin logic or script.
* **Outputs:** Data displayed under **Integrations → Plugins** only.
* **Mapping:** Not required.
* **Examples:** `INTRSPD`, custom monitoring scripts.

---

### 5. Configuration-Only Plugins

* **Inputs/Outputs:** None at runtime.
* **Purpose:** Used for configuration or maintenance tasks.
* **Examples:** `MAINT`, `CSVBCKP`.

---

## Post-Processing

After persistence:

* The core generates notifications for any watched value changes.
* The UI updates with new or modified data.
* Plugins with UI-enabled data display under **Integrations → Plugins**.

---

## Summary

The lifecycle of a plugin configuration is:

**Load → Validate → Prepare → Execute → Parse → Map → Persist → Post-process**

Each plugin must:

* Follow the **output contract**.
* Declare its type and expected output structure.
* Define mappings and watched values clearly in `config.json`.


