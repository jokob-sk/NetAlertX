## Overview

Backs the **Custom Properties** feature on devices - interactive icons (links, notes, delete, run-plugin, etc.) shown in the device list. This plugin doesn't scan or collect anything itself; it only defines the field types and default option lists used wherever a `devCustomProps` table is edited: directly on a device (Device Details > Custom Properties) and via the `NEWDEV_devCustomProps` setting that seeds the default for newly discovered devices. Full usage guide: [Custom Properties](https://docs.netalertx.com/CUSTOM_PROPERTIES).

### Settings

- `CUSTPROP_icon`: the pool of icons offered by the icon picker when adding/editing a custom property. This is a shared list, not per-property - edit it to add or remove choices available everywhere.
- `CUSTPROP_type`: the list of available property types. The built-in ones each drive specific behavior when the property's icon is clicked - see [Available Action Types](https://docs.netalertx.com/CUSTOM_PROPERTIES#available-action-types) for exactly what `link`, `link_new_tab`, `show_notes`, `delete_dev`, and `run_plugin` each do; `none`/`data` are non-interactive.
- `CUSTPROP_args`, `CUSTPROP_name`, `CUSTPROP_notes`, `CUSTPROP_show`, `CUSTPROP_actions`: column definitions for a single custom-property row (the action's arguments, display name, tooltip notes, visibility toggle, and row action buttons). These aren't values you set once - they're the schema every Custom Properties table (per-device or `NEWDEV_devCustomProps`) is built from.

### Usage

- Head to **Settings** > **Custom properties** to adjust the icon and type pools available to every device.
- Individual property rows are added/edited per device (Device Details > Custom Properties) or as the new-device default via `NEWDEV_devCustomProps` - not here.
