---
name: logging-standards
description: Logging conventions for NetAlertX backend Python code. Use this when adding, modifying, or reviewing log statements.
---

# Logging Standards

## Import

```python
from logger import mylog
```

Never import `logging` directly in application code. Use `mylog` exclusively.

## Function Signature

```python
mylog(level, message_or_list)
```

`message_or_list` can be a plain string or a list of values — the logger joins them with spaces.

## Log Levels

Levels from least to most verbose (higher number = more output):

| Level | Numeric | When to use |
|-------|---------|-------------|
| `"none"` | 0 | Always printed regardless of user setting. Reserve for startup, fatal errors, and one-time permission checks. |
| `"minimal"` | 1 | Important state transitions visible by default (scan start/end, plugin finish, restart). |
| `"verbose"` | 2 | Informational progress — what the system is doing without clutter (e.g. "No changes to report"). |
| `"debug"` | 3 | Developer-level detail — loop decisions, branch taken, counts. |
| `"trace"` | 4 | Granular per-item tracing — individual device rows, SQL queries, raw values. |

## Message Format

Prefix every message with a `[Module]` tag matching the file/function context:

```python
mylog("debug", [f"[device_handling] Processing MAC: {mac}"])
mylog("verbose", ["[Scan] Scan complete — devices updated:", count])
```

Use `f-strings` inside a list element, not string concatenation:

```python
# Correct
mylog("debug", [f"[NIC] parent={parent_mac} nic_online={nic_online}"])

# Avoid
mylog("debug", "[NIC] parent=" + parent_mac + " nic_online=" + str(nic_online))
```

## Timestamp

`mylog` / `file_print` prepend the current local-timezone time automatically via `timeNowTZ`. Do **not** add a timestamp manually inside the message.

## What NOT to Log

- Do not log raw user input without sanitization.
- Do not log full SQL query strings at `"none"` or `"minimal"` — use `"trace"` at most.
- Do not use `print()` in server code — use `mylog`. `file_print` is an internal helper; do not call it directly.

## Log File Location

Written to `{logPath}/app.log` (`logPath` from `const.py` → `/tmp/logs` at runtime). Do not hardcode this path.
