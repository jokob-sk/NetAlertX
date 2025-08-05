# Icon and Type guessing: Device heuristics

This module is responsible for inferring the most likely **device type** and **icon** based on minimal identifying data like MAC address, vendor, IP, or device name.

It does this using a set of heuristics defined in an external JSON rules file, which it evaluates **in priority order**.

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

```text
1. MAC + Vendor → match_mac_and_vendor()
2. Vendor only → match_vendor()
3. Name pattern → match_name()
4. IP pattern → match_ip()
5. Final fallback → defaults
```

### Even if defaults are passed in, matching continues

For example, when `default_icon` is passed in from an external source (like `NEWDEV_devIcon`), that value **does not halt the guessing process**. The matchers still try to find a better match:

```python
# Even if default_icon is passed, match_ip() and others will still run
if (not type_ or type_ == default_type) or (not icon or icon == default_icon):
    type_, icon = match_ip(ip, default_type, default_icon)
```

This is by design — you can pass in known fallbacks (e.g. `"unknown_icon"`), but the system will still guess and overwrite them **if it finds a better match**.

---

## Defaults & Normalization

Input sanitization ensures missing data doesn’t break detection:

| Input         | Normalized to         |
| ------------- | --------------------- |
| `vendor=None` | `"unknown"`           |
| `mac=None`    | `"00:00:00:00:00:00"` |
| `ip=None`     | `"169.254.0.0"`       |
| `name=None`   | `"(unknown)"`         |

These placeholder values **still go through the matching pipeline**. This makes the logic robust and ensures IP- or name-based matching can still work even if MAC/Vendor are unknown.

---

## Match Behavior (per function)

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

**TL;DR:** If a match sets the type but has no icon, the default icon is used. If the match has both, defaults are overridden.

---

## Priority Mechanics

* JSON rules are evaluated **top-to-bottom**
* Matching is **first-hit wins** — no scoring, no weights
* Rules that are more specific (e.g. exact MAC prefixes) should be listed earlier
