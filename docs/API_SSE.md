# SSE (Server-Sent Events)

Real-time app state updates via Server-Sent Events. Reduces server load ~95% vs polling.

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sse/state` | GET | Stream state updates (requires Bearer token) |
| `/sse/stats` | GET | Debug: connected clients, queued events |

## Usage

### Connect to SSE Stream
```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://localhost:5000/sse/state
```

### Check Connection Stats
```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  http://localhost:5000/sse/stats
```

## Event Types

- `state_update` - App state changed (e.g., "Scanning", "Processing")
- `unread_notifications_count_update` - Number of unread notifications changed (count: int)

## Backend Integration

Broadcasts automatically triggered in `app_state.py` via `broadcast_state_update()`:

```python
from api_server.sse_broadcast import broadcast_state_update

# Called on every state change - no additional code needed
broadcast_state_update(current_state="Scanning", settings_imported=time.time())
```

## Frontend Integration

Auto-enabled via `sse_manager.js`:

```javascript
// In browser console:
netAlertXStateManager.getStats().then(stats => {
  console.log("Connected clients:", stats.connected_clients);
});
```

## Fallback Behavior

- If SSE fails after 3 attempts, automatically switches to polling
- Polling starts at 1s, backs off to 30s max
- No user-visible difference in functionality

## Files

| File | Purpose |
|------|---------|
| `server/api_server/sse_endpoint.py` | SSE endpoints & event queue |
| `server/api_server/sse_broadcast.py` | Broadcast helper functions |
| `front/js/sse_manager.js` | Client-side SSE connection manager |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check backend running, API token correct |
| No events received | Verify `broadcast_state_update()` is called on state changes |
| High memory | Events not processed fast enough, check client logs |
| Using polling instead of SSE | Normal fallback - check browser console for errors |

---


