---
name: api-development
description: Develop and extend NetAlertX REST API endpoints. Use this when asked to create endpoint, add API route, implement API, or modify API responses.
---

# API Development

## Entry Point

Flask app: `server/api_server/api_server_start.py`

## Existing Routes

- `/device/<mac>` - Single device operations
- `/devices` - Device list
- `/devices/export/{csv,json}` - Export devices
- `/devices/import` - Import devices
- `/devices/totals` - Device counts
- `/devices/by-status` - Devices grouped by status
- `/nettools` - Network utilities
- `/events` - Event log
- `/sessions` - Session management
- `/dbquery` - Database queries
- `/metrics` - Prometheus metrics
- `/sync` - Synchronization

## Authorization

All routes require header:

```
Authorization: Bearer <API_TOKEN>
```

Retrieve token via `get_setting_value('API_TOKEN')`.

## Response Contract

**MANDATORY:** All responses must include `"success": true|false`

```python
return {"success": False, "error": "Description of what went wrong"}
```

On success:

```python
return {"success": True, "data": result}
```

```python
return {"success": False, "error": "Description of what went wrong"}
```

On success:

```python
return {"success": True, "data": result}
```


**Exception:** The legacy `/device/<mac>` GET endpoint does not follow this contract to maintain backward compatibility with the UI.

## Adding New Endpoints

1. Add route in `server/api_server/` directory
2. Follow authorization pattern
3. Return proper response contract
4. Update UI to read/write JSON cache (don't bypass pipeline)
