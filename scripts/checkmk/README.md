# NetAlertX-New-Devices-Checkmk-Script

This script retrieves the list of all devices from NetAlertX by reading the `table_devices.json` file from the API directory within the "NetAlertX" Docker container (default: `/tmp/api`, configurable via `NETALERTX_API` environment variable). It then checks if there are any new devices (`devIsNew == 1`). 

- If new devices are found, a warning state is reported.  
- Otherwise, an OK state is returned.

## Checkmk Local Check Format

The script follows the Checkmk local check format:  

```
<status> <service_name> <perfdata> <message>
```

For more details, see the [Checkmk Local Checks Documentation](https://docs.checkmk.com/latest/en/localchecks.html).

### Other info

- Version: 1.0
- Author: N/A
- Release Date: 08-Jan-2025 

> [!NOTE]
> This is a community supplied script and not maintained. 