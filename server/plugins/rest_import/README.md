## Overview

Import devices from any REST API that returns JSON

Designed to replace small vendor-specific plugins for systems like OPNsense, RouterOS, asset management tools, and custom inventory APIs. Multiple endpoints can be configured independently in a single plugin instance.

### Quick setup guide

Navigate to **Settings** > **REST Import** and click **Add** to create an import definition.

| Field | Description |
|---|---|
| **Name** | Friendly label shown in logs (e.g. `OPNsense DHCP`) |
| **URL** | Full REST endpoint URL |
| **Method** | `GET` or `POST` |
| **Verify SSL** | Disable for self-signed certificates |
| **Auth Type** | `none`, `basic`, or `bearer` |
| **Username / API Key** | Used with `basic` auth |
| **Password / API Secret** | Used with `basic` auth |
| **Bearer Token** | Used with `bearer` auth |
| **Custom Headers** | Optional. One `Key: Value` per line |
| **POST Body** | Optional JSON body for `POST` requests |
| **Device List Path** | Dot-separated path to the array of records (e.g. `rows`, `data.devices`). Leave blank if the response is already an array |

### Field mapping

Map API response fields to NetAlertX scan fields. Leave a mapping blank to skip that field.

| Popup field | Scan column |
|---|---|
| MAC Address | `scanMac` |
| IP Address | `scanLastIP` |
| Device Name | `scanName` |
| Vendor | `scanVendor` |
| SSID | `scanSSID` |
| Device Type | `scanType` |
| Parent MAC | `scanParentMAC` |
| Parent Port | `scanParentPort` |
| Site | `scanSite` |
| VLAN | `scanVlan` |

### Fake MAC generation

Enable **Generate Fake MAC** when the API does not expose MAC addresses (e.g. remote ICMP scans, IP-only inventory systems). A deterministic fake MAC is derived from the IP address using the `fa:ce:` prefix. Requires a valid IP mapping.

> [!WARNING]
> Fake MACs can cause inconsistencies if IP addresses change between scans. Static IPs are strongly recommended when using this feature.

### Example: OPNsense Dnsmasq API

See the [OPNsense configuration guide](https://docs.netalertx.com/REST_IMPORT) for details. 

**Response:**
```json
{
  "rows": [
    {
      "hwaddr": "94:18:65:de:22:01",
      "address": "192.168.1.2",
      "hostname": "Orbi-Base-Station",
      "mac_info": "NETGEAR"
    }
  ]
}
```

**Configuration:**
```text
Name:              OPNsense DHCP
URL:               https://firewall/api/dnsmasq/leases/search
Method:            GET
Auth Type:         basic
Username:          admin
Device List Path:  rows
MAC Address:       hwaddr
IP Address:        address
Device Name:       hostname
Vendor:            mac_info
```

### Notes

- Version: 1.0.0
- Author: `jokob-sk`
- Records with missing or invalid MAC addresses are skipped unless **Generate Fake MAC** is enabled
- Each import definition executes independently; failed imports do not block others
