## Overview

Handles routine housekeeping so long-running logs and in-app notifications don't grow unbounded: trims `app.log` down to a configured line count, purges old in-app notification entries past a configured count, and sets the retention window (in days) for NetAlertX's own resource-usage history (System Info -> Performance tab).

### Usage

- Runs automatically once configured - no manual action needed beyond setting a schedule and the retention values on the Settings page.
