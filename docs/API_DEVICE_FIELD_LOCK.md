# Device Field Lock/Unlock API

## Overview

The Device Field Lock/Unlock feature allows users to lock specific device fields to prevent plugin overwrites. This is part of the authoritative device field update system that ensures data integrity while maintaining flexibility for user customization.

## Concepts

### Tracked Fields
Only certain device fields support locking. These are the fields that can be modified by both plugins and users:
- `devMac` - Device MAC address
- `devName` - Device name/hostname  
- `devLastIP` - Last known IP address
- `devVendor` - Device vendor/manufacturer
- `devFQDN` - Fully qualified domain name
- `devSSID` - Network SSID
- `devParentMAC` - Parent device MAC address
- `devParentPort` - Parent device port
- `devParentRelType` - Parent device relationship type
- `devVlan` - VLAN identifier

### Field Source Tracking
Every tracked field has an associated `*Source` field that indicates where the current value originated:
- `NEWDEV` - Created via the UI as a new device
- `USER` - Manually edited by a user
- `LOCKED` - Field is locked; prevents any plugin overwrites
- Plugin name (e.g., `UNIFIAPI`, `PIHOLE`) - Last updated by this plugin

### Locking Mechanism
When a field is **locked**, its source is set to `LOCKED`. This prevents plugin overwrites based on the authorization logic:
1. Plugin wants to update field
2. Authoritative handler checks field's `*Source` value
3. If `*Source` == `LOCKED`, plugin update is rejected
4. User can still manually unlock the field

When a field is **unlocked**, its source is set to `NEWDEV`, allowing plugins to resume updates.

## Endpoints

### Lock or Unlock a Field
```
POST /device/{mac}/field/lock
Authorization: Bearer {API_TOKEN}
Content-Type: application/json

{
  "fieldName": "devName",
  "lock": true
}
```

#### Parameters
- `mac` (path, required): Device MAC address (e.g., `AA:BB:CC:DD:EE:FF`)
- `fieldName` (body, required): Name of the field to lock/unlock. Must be one of the tracked fields listed above.
- `lock` (body, required): Boolean. `true` to lock, `false` to unlock.

#### Responses

**Success (200)**
```json
{
  "success": true,
  "message": "Field devName locked",
  "fieldName": "devName",
  "locked": true
}
```

**Bad Request (400)**
```json
{
  "success": false,
  "error": "fieldName is required"
}
```

```json
{
  "success": false,
  "error": "Field 'devInvalidField' cannot be locked"
}
```

**Unauthorized (403)**
```json
{
  "success": false,
  "error": "Unauthorized"
}
```

**Not Found (404)**
```json
{
  "success": false,
  "error": "Device not found"
}
```

## Examples

### Lock a Device Name
Prevent the device name from being overwritten by plugins:

```bash
curl -X POST https://your-netalertx.local/api/device/AA:BB:CC:DD:EE:FF/field/lock \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "fieldName": "devName",
    "lock": true
  }'
```

### Unlock a Field
Allow plugins to resume updating a field:

```bash
curl -X POST https://your-netalertx.local/api/device/AA:BB:CC:DD:EE:FF/field/lock \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "fieldName": "devName",
    "lock": false
  }'
```

## UI Integration

The Device Edit form displays lock/unlock buttons for all tracked fields:

1. **Lock Button** (🔒): Click to prevent plugin overwrites
2. **Unlock Button** (🔓): Click to allow plugin overwrites again
3. **Source Indicator**: Shows current field source (USER, LOCKED, NEWDEV, or plugin name)

### Source Indicator Colors
- Red (USER): Field was manually edited by a user
- Orange (LOCKED): Field is locked and protected from overwrites
- Gray (NEWDEV/Plugin): Field value came from automatic discovery

## UI Workflow

### Locking a Field via UI
1. Navigate to Device Details
2. Find the field you want to protect
3. Click the lock button (🔒) next to the field
4. Button changes to unlock (🔓) and source indicator turns red (LOCKED)
5. Field is now protected from plugin overwrites

### Unlocking a Field via UI
1. Find the locked field (button shows 🔓)
2. Click the unlock button
3. Button changes back to lock (🔒) and source resets to NEWDEV
4. Plugins can now update this field again

## Authorization

All lock/unlock operations require:
- Valid API token in `Authorization: Bearer {token}` header
- User must be authenticated to the NetAlertX instance

## Implementation Details

### Backend Logic
The lock/unlock feature is implemented in:
- **API Endpoint**: `/server/api_server/api_server_start.py` - `api_device_field_lock()`
- **Data Model**: `/server/models/device_instance.py` - Authorization checks in `setDeviceData()`
- **Database**: Devices table with `*Source` columns tracking field origins

### Frontend Logic
The lock/unlock UI is implemented in:
- **Device Edit Form**: `/front/deviceDetailsEdit.php`
  - Form rendering with lock/unlock buttons
  - JavaScript function `toggleFieldLock()` for API calls
  - Source indicator display
- **Styling**: `/front/css/app.css` - Lock button and source indicator styles

### Authorization Handler
The authoritative field update logic prevents plugin overwrites:
1. Plugin provides new value for field via plugin config `SET_ALWAYS`/`SET_EMPTY`
2. Authoritative handler (in DeviceInstance) checks `{field}Source` value
3. If source is `LOCKED` or `USER`, plugin update is rejected
4. If source is `NEWDEV` or plugin name, plugin update is accepted

## Best Practices

### When to Lock Fields
- Device names that you've customized
- Static IP addresses or important identifiers
- Device vendor information you've corrected
- Fields prone to incorrect plugin updates

### When to Keep Unlocked
- Fields that plugins actively maintain (MAC, IP address)
- Fields you want auto-updated by discovery plugins
- Fields that may change frequently in your network

### Bulk Operations
The field lock/unlock feature is currently per-device. For bulk locking:
1. Use Multi-Edit to update device fields
2. Then use individual lock operations via API script
3. Or contact support for bulk lock endpoint

## Troubleshooting

### Lock Button Not Visible
- Device must be saved/created first (not "new" device)
- Field must be one of the 10 tracked fields
- Check browser console for JavaScript errors

### Lock Operation Failed
- Verify API token is valid
- Check device MAC address is correct
- Ensure device exists in database

### Field Still Updating After Lock
- Verify lock was successful (check API response)
- Reload device details page
- Check plugin logs to see if plugin is providing the field
- Look for authorization errors in NetAlertX logs

## See Also
- [API Device Endpoints Documentation](API_DEVICE.md)
- [Authoritative Field Updates System](../docs/PLUGINS_DEV.md#authoritative-fields)
- [Plugin Configuration Reference](../docs/PLUGINS_DEV_CONFIG.md)
