# Device Heuristics: Icon and Type Guessing

This module is responsible for inferring the most likely **device type** and **icon** based on minimal identifying data like MAC address, vendor, IP, or device name.

It does this using a set of heuristics defined in an external JSON rules file, which it evaluates **in priority order**.

>[!NOTE]
> You can find the full source code of the heuristics module in the `device_heuristics.py` file.  

---

## JSON Rule Format

Rules are defined in a file called `device_heuristics_rules.json` (located under `/back`), structured like:

```json
[
  {
    "dev_type": "Phone",
    "icon_html": "<i class=\"fa-brands fa-apple\"></i>",
    "matching_pattern": [
      { "mac_prefix": "001A79", "vendor": "Apple" }
    ],
    "name_pattern": ["iphone", "pixel"]
  }
]
```

>[!NOTE]
> Feel free to raise a PR in case you'd like to add any rules into the `device_heuristics_rules.json` file. Please place new rules into the correct position and consider the priority of already available rules.

### Supported fields:

| Field              | Type                 | Description                                                     |
| ------------------ | -------------------- | --------------------------------------------------------------- |
| `dev_type`         | `string`             | Type to assign if rule matches (e.g. `"Gateway"`, `"Phone"`)    |
| `icon_html`        | `string`             | Icon (HTML string) to assign if rule matches. Encoded to base64 at load time. |
| `matching_pattern` | `array`              | List of `{ mac_prefix, vendor }` objects for first strict and then loose matching    |
| `name_pattern`     | `array` *(optional)* | List of lowercase substrings (used with regex)                  |
| `ip_pattern`       | `array` *(optional)* | Regex patterns to match IPs                                     |

**Order in this array defines priority** — rules are checked top-down and short-circuit on first match.

---

## Matching Flow (in Priority Order)

The function `guess_device_attributes(...)` runs a series of matching functions in strict order:

1. MAC + Vendor → `match_mac_and_vendor()`
2. Vendor only → `match_vendor()`
3. Name pattern → `match_name()`
4. IP pattern → `match_ip()`
5. Final fallback → defaults defined in the `NEWDEV_devIcon` and `NEWDEV_devType` settings.

> [!NOTE]
> The app will try guessing the device type or icon if `devType` or `devIcon` are `""` or `"null"`.

### Use of default values

The guessing process runs for every device **as long as the current type or icon still matches the default values**. Even if earlier heuristics return a match, the system continues evaluating additional clues — like name or IP — to try and replace placeholders.

```python
# Still considered a match attempt if current values are defaults
if (not type_ or type_ == default_type) or (not icon or icon == default_icon):
    type_, icon = match_ip(ip, default_type, default_icon)
```

In other words: if the type or icon is still `"unknown"` (or matches the default), the system assumes the match isn’t final — and keeps looking. It stops only when both values are non-default (defaults are defined in the `NEWDEV_devIcon` and `NEWDEV_devType` settings).

---

## Match Behavior (per function)

These functions are executed in the following order:

### `match_mac_and_vendor(mac_clean, vendor, ...)`

* Looks for MAC prefix **and** vendor substring match
* Most precise
* Stops as soon as a match is found

### `match_vendor(vendor, ...)`

* Falls back to substring match on vendor only
* Ignores rules where `mac_prefix` is present (ensures this is really a fallback)

### `match_name(name, ...)`

* Lowercase name is compared against all `name_pattern` values using regex
* Good for user-assigned labels (e.g. "AP Office", "iPhone")

### `match_ip(ip, ...)`

* If IP is present and matches regex patterns under any rule, it returns that type/icon
* Usually used for gateways or local IP ranges

---

## Icons

* Each rule can define an `icon_html`, which is converted to a `icon_base64` on load
* If missing, it falls back to the passed-in `default_icon` (`NEWDEV_devIcon` setting)
* If a match is found but icon is still blank, default is used

**TL;DR:** Type and icon must both be matched. If only one is matched, the other falls back to the default.

---

## Priority Mechanics

* JSON rules are evaluated **top-to-bottom**
* Matching is **first-hit wins** — no scoring, no weights
* Rules that are more specific (e.g. exact MAC prefixes) should be listed earlier
