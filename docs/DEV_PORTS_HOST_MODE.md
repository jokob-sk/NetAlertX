# Dev Ports in Host Network Mode

When using `"--network=host"` in the devcontainer, VS Code's normal port forwarding model doesn't apply. All container ports are already on the host network namespace, so:

- Listing ports in `forwardPorts` can cause VS Code to pre-bind or reserve them (conflicts with startup scripts waiting for a free port).
- The PORTS panel will not auto-detect services reliably, because forwarding isn't occurring.
- Debugger ports (e.g. Xdebug `9003`, Python debugpy `5678`) can still be listed safely.

## Recommended Pattern

1. Only include debugger ports in `forwardPorts`:
   ```jsonc
   "forwardPorts": [5678, 9003]
   ```
2. Do NOT list application service ports (e.g. 20211, 20212) there when in host mode.
3. Use the helper task to enumerate current bindings:
   - Run task: `> Tasks: Run Task` → `[Dev Container] List NetAlertX Ports`

## Port Enumeration Script
Script: `scripts/list-ports.sh`
Outputs binding address, PID (if resolvable) and process name for key ports.

You can edit the PORTS variable inside that script to add/remove watched ports.

## Xdebug Notes
Set in `99-xdebug.ini`:
```ini
xdebug.client_host=127.0.0.1
xdebug.client_port=9003
xdebug.discover_client_host=1
```
Ensure your IDE is listening on 9003.

## Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|
| `Waiting for port 20211 to free...` repeats | VS Code pre-bound the port via `forwardPorts` | Remove the port from `forwardPorts`, rebuild, retry |
| PHP request hangs at start | Xdebug trying to connect to unresolved host (`host.docker.internal`) | Use `127.0.0.1` or rely on discovery |
| PORTS panel empty | Expected in host mode | Use the port enumeration task |

## Future Improvements
- Optional: add a small web status endpoint summarizing runtime ports.
- Optional: detect host mode in `setup.sh` and skip the wait loop if the PID using port is the intended process.

