# Workflow examples

Workflows in NetAlertX automate actions based on real-time events and conditions. Below are practical examples that demonstrate how to build automation using triggers, conditions, and actions.

## Un-archive devices if detected online

This workflow automatically unarchives a device if it was previously archived but has now been detected as online.

### 📋 Use Case

Sometimes devices are manually archived (e.g., no longer expected on the network), but they reappear unexpectedly. This workflow reverses the archive status when such devices are detected during a scan.

### ⚙️ Workflow Configuration

```json
{
  "name": "Un-archive devices if detected online",
  "trigger": {
    "object_type": "Devices",
    "event_type": "update"
  },
  "conditions": [
    {
      "logic": "AND",
      "conditions": [
        {
          "field": "devIsArchived",
          "operator": "equals",
          "value": "1"
        },
        {
          "field": "devPresentLastScan",
          "operator": "equals",
          "value": "1"
        }
      ]
    }
  ],
  "actions": [
    {
      "type": "update_field",
      "field": "devIsArchived",
      "value": "0"
    }
  ],
  "enabled": "Yes"
}
```

### 🔍 Explanation

    - Trigger: Listens for updates to device records.
    - Conditions:
        - `devIsArchived` is `1` (archived).
        - `devPresentLastScan` is `1` (device was detected in the latest scan).
    - Action: Updates the device to set `devIsArchived` to `0` (unarchived).

### ✅ Result

Whenever a previously archived device shows up during a network scan, it will be automatically unarchived — allowing it to reappear in your device lists and dashboards.