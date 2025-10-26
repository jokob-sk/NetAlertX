# Backing things up

> [!NOTE]
> To backup 99% of your configuration backup at least the `/app/config` folder. Please read the whole page (or at least "Scenario 2: Corrupted database") for details.
> Note that database definitions might change over time. The safest way is to restore your older backups into the **same version** of the app they were taken from and then gradually upgarde between releases to the latest version.

There are 4 artifacts that can be used to backup the application:

| File                  | Description                   | Limitations                   |
|-----------------------|-------------------------------|-------------------------------|
| `/db/app.db`       | Database file(s)  | The database file might be in an uncommitted state or corrupted |
| `/config/app.conf` | Configuration file |  Can be overridden with the [`APP_CONF_OVERRIDE` env variable](https://github.com/jokob-sk/NetAlertX/tree/main/dockerfiles#docker-environment-variables).  |
| `/config/devices.csv`  | CSV file containing device information |     Doesn't contain historical data        |
| `/config/workflows.json`  | A JSON file containing your workflows |     N/A        |


## Backup strategies

The safest approach to backups is to backup everything, by taking regular file system backups of the `/db` and `/config` folders (I use [Kopia](https://github.com/kopia/kopia)). 

Arguably, the most time is spent setting up the device list, so if only one file is kept I'd recommend to have a latest backup of the `devices_<timestamp>.csv` or `devices.csv` file, followed by the `app.conf` and `workflows.json` files. You can also download `app.conf` and `devices.csv` file in the Maintenance section:

![Backup and Restore Section in Maintenance](./img/BACKUPS/Maintenance_Backup_Restore.png)

### Scenario 1: Full backup

End-result: Full restore

#### 💾 Source artifacts:

- `/app/db/app.db` (uncorrupted)
- `/app/config/app.conf`
- `/app/config/workflows.json`

#### 📥 Recovery:

To restore the application map the above files as described in the [Setup documentation](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md#docker-paths). 


### Scenario 2: Corrupted database

End-result: Partial restore (historical data and some plugin data will be missing)

#### 💾 Source artifacts:

- `/app/config/app.conf`
- `/app/config/devices_<timestamp>.csv` or `/app/config/devices.csv`
- `/app/config/workflows.json`

#### 📥 Recovery:

Even with a corrupted database you can recover what I would argue is 99% of the configuration. 

- upload the `app.conf` and `workflows.json` files into the mounted `/app/config/` folder as described in the [Setup documentation](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md#docker-paths).
- rename the `devices_<timestamp>.csv` to `devices.csv` and place it in the `/app/config` folder
- Restore the `devices.csv` backup via the [Maintenance section](./DEVICES_BULK_EDITING.md)

## Data and backup storage

To decide on a backup strategy, check where the data is stored:

### Core Configuration

The core application configuration is in the `app.conf` file (See [Settings System](./SETTINGS_SYSTEM.md) for details), such as:

- Notification settings
- Scanner settings
- Scheduled maintenance settings
- UI configuration

### Core Device Data

The core device data is backed up to the `devices_<timestamp>.csv` or `devices.csv` file via the [CSV Backup `CSVBCKP` Plugin](https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/csv_backup). This file contains data, such as:

- Device names
- Device icons
- Device network configuration
- Device categorization 
- Device custom properties data

### Historical data

Historical data is stored in the `app.db` database (See [Database overview](./DATABASE.md) for details). This data includes:

- Plugin objects
- Plugin historical entries
- History of Events, Notifications, Workflow Events
- Presence history


