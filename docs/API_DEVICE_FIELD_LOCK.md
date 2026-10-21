# Device Field Lock/Unlock API

## Overview

The Device Field Lock/Unlock feature allows users to lock specific device fields to prevent plugin overwrites. This is part of the authoritative device field update system that ensures data integrity while maintaining flexibility for user customization.

## Concepts

### Tracked Fields

Only certain device fields support locking. These are the fields that can be modified by both plugins and users:

- `devName` - Device name/hostname
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


### Authorization Handler

The authoritative field update logic prevents plugin overwrites:

1. Plugin provides new value for field via plugin config `SET_ALWAYS`/`SET_EMPTY`
2. Authoritative handler (in DeviceInstance) checks `{field}Source` value
3. If source is `LOCKED` or `USER`, plugin update is rejected
4. If source is `NEWDEV` or plugin name, plugin update is accepted

## See Also

- [Device locking](./DEVICE_FIELD_LOCK.md)
- [Device source fields - Authoritative updates](./DEVICE_SOURCE_FIELDS.md)
- [API Device Endpoints Documentation](./API_DEVICE.md)
- [Plugin Configuration Reference](./PLUGINS_DEV_CONFIG.md)
