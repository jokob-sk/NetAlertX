## Overview

Plugin to run regular database cleanup tasks. It is strongly recommended to have an hourly or at least daily schedule running.

The database cleanup plugin (DBCLNP) helps maintain the system by removing outdated or unnecessary data, ensuring smooth operation. Below are the key settings that control the cleanup process:

- **`PLUGINS_KEEP_HIST`**:  
  Specifies how many historical records to retain for each plugin. Recommended value: `500` entries.

- **`HRS_TO_KEEP_NEWDEV`**:  
  Defines how long, in hours, newly discovered device records should be kept. Once the specified time has passed, the records will be deleted if tehy still are marked as NEW. Recommended value: `0` (no auto delete).

- **`DAYS_TO_KEEP_EVENTS`**:  
  Specifies the number of days to retain event logs. Event entries older than the given number of days will be automatically deleted during cleanup. Recommended value: `30` days.


By fine-tuning these settings, you ensure that the database remains optimized, preventing performance degradation in the NetAlertX system.


### Usage

- Check the Settings page for details.
