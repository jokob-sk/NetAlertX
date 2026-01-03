# PUID/PGID Security — Why the entrypoint requires numeric IDs

## Purpose

This short document explains the security rationale behind the root-priming entrypoint's validation of runtime user IDs (`PUID`) and group IDs (`PGID`). The validation is intentionally strict and is a safety measure to prevent environment-variable based command injection when running as root during the initial priming stage.

## Key points

- The entrypoint accepts only values that are strictly numeric (digits only). Non-numeric values are treated as malformed and are a fatal error.
- The fatal check exists to prevent *injection* or accidental shell interpretation of environment values while the container runs as root (e.g., `PUID="20211 && rm -rf /"`).
- There is **no artificial upper bound** enforced by the validation — any numeric UID/GID is valid (for example, `100000` is acceptable).

## Behavior on malformed input

- If `PUID` or `PGID` cannot be parsed as numeric (digits-only), the entrypoint prints an explicit security message to stderr and exits with a non-zero status.
- This is a deliberate, conservative safety measure — we prefer failing fast on potentially dangerous input rather than continuing with root-privileged operations.

## Operator guidance

- Always supply numeric values for `PUID` and `PGID` in your environment (via `docker-compose.yml`, `docker run -e`, or equivalent). Example: `PUID=20211`.
- If you need to run with a high-numbered UID/GID (e.g., `100000`), that is fine — the entrypoint allows it as long as the value is numeric.
- Don’t pass shell meta-characters, spaces, or compound commands in `PUID` or `PGID` — those will be rejected as malformed and cause the container to exit.

## Required Capabilities for Privilege Drop

If you are hardening your container by dropping capabilities (e.g., `cap_drop: [ALL]`), you **must** explicitly grant the `SETUID` and `SETGID` capabilities.

- **Why?** The entrypoint runs as root to set permissions, then uses `su-exec` to switch to the user specified by `PUID`/`PGID`. This switch requires the kernel to allow the process to change its own UID/GID.
- **Symptom:** If these capabilities are missing, the container will log a warning ("su-exec failed") and continue running as **root** (UID 0), defeating the purpose of setting `PUID`/`PGID`.
- **Fix:** Add `SETUID` and `SETGID` to your `cap_add` list.

```yaml
cap_drop:
  - ALL
cap_add:
  - SETUID
  - SETGID
  # ... other required caps like CHOWN, NET_ADMIN, etc.
```

---

*Document created to clarify the security behavior of the root-priming entrypoint (PUID/PGID validation).*