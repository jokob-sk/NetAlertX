# Usage

1. **Run the Script**

`python ./db_cleanup.py`

2. **Menu Options**
- **1. Check/Clean by MAC address**
  - Enter a MAC address in the format `xx:xx:xx:xx:xx:xx`.
  - The script will query the database and display any matching entries.
  - Confirm to delete the entries if desired.
- **2. Check/Clean by IP address**
  - Enter an IP address in the format `xxx.xxx.xxx.xxx`.
  - The script will query the database and display any matching entries.
  - Confirm to delete the entries if desired.
- **3. Exit**
  - Quit the script.

## Database Queries

The script checks the following tables:
- `Events`
- `Devices`
- `CurrentScan`
- `Notifications`
- `AppEvents`
- `Plugins_Objects`

For each MAC or IP address provided, the script:

1. Queries the tables for matching entries.
2. Prompts to delete the entries if any are found.


### Other info

- Date : 23-Dec-2024 - version 1.0
- Author: [laxduke](https://github.com/laxduke)