## Overview

Settings that control the look, layout, and live behavior of the web UI — the Devices page, device icons, locale/date formatting, and how/when the UI polls or waits on the backend. None of these affect what data is scanned or stored, only how it's displayed and interacted with.

### What each group changes

- **Devices page layout** (`device_columns`, `columns_filters`, `shown_cards`, `hide_empty`, `PRESENCE`, `MY_DEVICES`, `DEV_SECTIONS`): which columns/filters/tiles appear on the Devices list and in what order, which device statuses populate the presence chart and the default *My devices* view, and which page sections can be hidden entirely.
- **Device filtering** (`hide_rel_types`): excludes devices whose parent relationship matches one of the given types (e.g. `nic`, `virtual`) from most device lists — useful for hiding virtual/container interfaces that would otherwise clutter the list.
- **Appearance** (`theme`, `ICONS`, `LOCALE`): the UI color theme (with a `System` option that follows the OS/browser), the pool of pre-defined icons offered in the device icon picker, and the locale used to format dates across the UI.
- **Live/refresh behavior** (`REFRESH`, `SCAN_PAUSE`, `DEFAULT_PAGE_SIZE`, `WAIT_FOR_SETTINGS`): how often the UI auto-reloads itself (`0` disables auto-refresh), how long a manual scan pause lasts, the default table page size, and whether saving settings blocks the UI until the backend finishes reloading — it only actually blocks when a plugin's configuration changed; other changes return immediately regardless of this setting.
- **Network page** (`TOPOLOGY_ORDER`): sort order for nodes in the Network topology view.
- **MAC handling** (`NOT_RANDOM_MAC`): MAC prefixes that should never be flagged as a randomized/private MAC, even if they'd otherwise match the randomization heuristic.

Setting names and tooltips in the Settings UI are the source of truth for exact behavior and accepted values — this README only orients you to what each group is for.

### Usage

- Head to **Settings** > **UI Settings** to adjust the default values.
