# 💾 Backing things up

> [!NOTE]
> To backup 99% of your configuration backup at least the `/config` folder. Please read the whole page (or at least "Scenario 2: Corrupted database") for details.

There are 3 artifacts that can be used to backup the application:

| File                  | Description                   | Limitations                   |
|-----------------------|-------------------------------|-------------------------------|
| `/db/pialert.db`       | Database file(s)  | The database file might be in an uncommitted state or corrupted |
| `/config/pialert.conf` | Configuration file |   Doesn't contain settings from the Maintenance section        |
| `/config/devices.csv`  | CSV file containing device information |     Doesn't contain historical data        |

## Data and cackup storage

To decide on a backup strategy, check where the data is stored:

### Core Configuration

The core application configuration is in the `pialert.conf` file (See [Settings System](https://github.com/jokob-sk/NetAlertX/blob/main/docs/SETTINGS_SYSTEM.md) for details), such as:

- Notification settings
- Scanner settings
- Scheduled maintenance settings
- UI configuration (80%)

### Core Device Data

The core device data is backed up to the `devices_<timestamp>.csv` file via the [CSV Backup `CSVBCKP` Plugin](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/csv_backup). This file contains data, such as:

- Device names
- Device Icons
- Device Network configuration
- Device categorization 

### Historical data

Historical data is stored in the `pialert.db` database (See [Database overview](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DATABASE.md) for details). This data includes:

- Plugin objects
- Plugin historical entries
- History of Events, Notifications, Workflow Events
- Presence History

## 🧭 Backup strategies

The safest approach to backups is to backup all of the above, by taking regular file system backups (I use [Kopia](https://github.com/kopia/kopia)). 

Arguably, the most time is spent setting up the device list, so if only one file is kept I'd recommend to have a latest backup of the `devices_<timestamp>.csv` file, followed by the `pialert.conf` file. 

### Scenario 1: Full backup

End-result: Full restore

#### Source artifacts:

- `/db/pialert.db` (uncorrupted)
- `/config/pialert.conf`

#### Recovery:

To restore the application map the above files as described in the [Setup documentation](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md#docker-paths). 


### Scenario 2: Corrupted database

End-result: Partial restore (historical data & configurations from the Maintenance section will be missing)

#### Source artifacts:

- `/config/pialert.conf`
- `/config/devices_<timestamp>.csv` or `/config/devices.csv`

#### Recovery:

Even with a corrupted database you can recover what I would argue is 99% of the configuration (except of a couple of settings under Maintenance). 

- map the `/config/pialert.conf` file as described in the [Setup documentation](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md#docker-paths).
- rename the `devices_<timestamp>.csv` to `devices.csv` and place it in the `/config` folder
- Restore the `devices.csv` backup via the [Maintenance section](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICES_BULK_EDITING.md)


