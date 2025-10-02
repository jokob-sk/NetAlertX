## config.json Lifecycle in NetAlertX

This document describes on a high level how `config.json` is read, processed, and used by the NetAlertX core and plugins. It also outlines the plugin output contract and the main plugin types.

> [!NOTE]
> For a deep-dive on the specific configuration options and sections of the `config.json` plugin manifest, consult the [Plugins Development Guide](PLUGINS_DEV.md).

---

### 1. Loading

* On startup, the app core loads `config.json` for each plugin.
* The `config.json` represents a plugin manifest, that contains metadata and runtime settings.

---

### 2. Validation

* The core checks that each required settings key (such as `RUN`) for a plugin exists.
* Invalid or missing values may be replaced with defaults, or the plugin may be disabled.

---

### 3. Preparation

* The plugin’s settings (paths, commands, parameters) are prepared.
* Database mappings (`mapped_to_table`, `database_column_definitions`) for data ingestion into the core app are parsed.

---

### 4. Execution

* Plugins can be run at different core app execution points, such as on schedule, once on start, after a notification, etc. 
* At runtime, the scheduler triggers plugins according to their `interval`.
* The plugin executes its command or script.

---

### 5. Parsing

* Plugin output is expected in **pipe (`|`)-delimited format**.
* The core parses lines into fields, matching the **plugin interface contract**.

---

### 6. Mapping

* Each parsed field is moved into the `Plugins_` database tables and can be mapped into a configured database table.
* Controlled by `database_column_definitions` and `mapped_to_table`.
* Example: `Object_PrimaryID → Devices.MAC`.

---

### 6a. Plugin Output Contract

Each plugin must output results in the **plugin interface contract format**, pipe (`|`)-delimited values, in the column order described under [Plugin Interface Contract](PLUGINS_DEV.md)

#### IDs

  * `Object_PrimaryID` and `Object_SecondaryID` identify the record (e.g. `MAC|IP`).

#### **Watched values (`Watched_Value1–4`)**

  * Used by the core to detect changes between runs.
  * Changes here can trigger **notifications**.

#### **Extra value (`Extra`)**

  * Optional, extra field.
  * Stored in the database but **not used for alerts**.

#### **Helper values (`Helper_Value1–3`)**

  * Added for cases where more than IDs + watched + extra are needed.
  * Can be made visible in the UI.
  * Stored in the database but **not used for alerts**.

#### **Mapping matters**

  * While the plugin output is free-form, the `database_column_definitions` and `mapped_to_table` settings in `config.json` determine the **target columns and data types** in NetAlertX.

---

### 7. Persistence

* Data is upserted into the database.
* Conflicts are resolved using `Object_PrimaryID` + `Object_SecondaryID`.

---

### 8. Plugin Types and Expected Outputs

Beyond the `data_source` setting, plugins fall into functional categories. Each has its own input requirements and output expectations:

#### **Device discovery plugins**

  * **Inputs:** `N/A`, subnet, or API for discovery service, or similar.
  * **Outputs:** At minimum `MAC` and `IP` that results in a new or updated device records in the `Devices` table.
  * **Mapping:** Must be mapped to the `CurrentScan` table via `database_column_definitions` and `data_filters`.
  * **Examples:** ARP-scan, NMAP device discovery (e.g., `ARPSCAN`, `NMAPDEV`).

#### **Device-data enrichment plugins**

  * **Inputs:** Device identifier (usually `MAC`, `IP`).
  * **Outputs:** Additional data for that device (e.g. open ports).
  * **Mapping:** Controlled via `database_column_definitions` and `data_filters`.
  * **Examples:** Ports, MQTT messages (e.g., `NMAP`, `MQTT`)

#### **Name resolver plugins**

  * **Inputs:** Device identifiers (MAC, IP, or hostname).
  * **Outputs:** Updated `devName` and `devFQDN` fields.
  * **Mapping:** Not expected.
  * **Note:** Currently requires **core app modification** to add new plugins, not fully driven by the plugins’ `config.json`.
  * **Examples:** Avahiscan (e.g., `NBTSCAN`, `NSLOOKUP`).

#### **Generic plugins**

  * **Inputs:** Whatever the script or query provides.
  * **Outputs:** Data shown only in **Integrations → Plugins**, not tied to devices.
  * **Mapping:** Not expected.
  * **Examples:** External monitoring data (e.g., `INTRSPD`)

#### **Configuration-only plugins**

  * **Inputs/Outputs:** None at runtime.
  * **Mapping:** Not expected. 
  * **Examples:** Used to provide additional settings or execute scripts (e.g., `MAINT`, `CSVBCKP`).

---

### 9. Post-Processing

* Notifications are generated if watched values change.
* UI is updated with new or updated records.
* All values that are configured to be shown in teh UI appear in the Plugins section.

---

### 10. Summary

The lifecycle of `config.json` entries is:

**Load → Validate → Prepare → Execute → Parse → Map → Persist → Post-process**

Plugins must follow the **output contract**, and their category (discovery, specific, resolver, generic, config-only) defines what inputs they require and what outputs are expected.
