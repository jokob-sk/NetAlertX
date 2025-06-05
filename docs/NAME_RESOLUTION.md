# Device Name Resolution

Name resolution in NetAlertX relies on multiple plugins to resolve device names from IP addresses. If you are seeing `(name not found)` as device names, follow these steps to diagnose and fix the issue.

> [!TIP]  
> Before proceeding, make sure [Reverse DNS](./REVERSE_DNS.md) is enabled on your network.  
> You can control how names are handled and cleaned using the `NEWDEV_NAME_CLEANUP_REGEX` setting.  
> To auto-update Fully Qualified Domain Names (FQDN), enable the `REFRESH_FQDN` setting.


## Required Plugins

For best results, ensure the following name resolution plugins are enabled:

- **AVAHISCAN** – Uses mDNS/Avahi to resolve local network names.
- **NBTSCAN** – Queries NetBIOS to find device names.
- **NSLOOKUP** – Performs standard DNS lookups.
- **DIGSCAN** – Performs Name Resolution with the Dig utility (DNS).

You can check which plugins are active in your _Settings_ section and enable any that are missing.

There are other plugins that can supply device names as well, but they rely on bespoke hardware and services. See [Plugins overview](./PLUGINS.md) for details and look for plugins with name discovery (🆎) features.

## Checking Logs

If names are not resolving, check the logs for errors or timeouts.

See how to explore logs in the [Logging guide](./LOGGING.md).

Logs will show which plugins attempted resolution and any failures encountered.

## Adjusting Timeout Settings

If resolution is slow or failing due to timeouts, increase the timeout settings in your configuration, for example.

```ini
NSLOOKUP_RUN_TIMEOUT = 30
```

Raising the timeout may help if your network has high latency or slow DNS responses.

## Checking Plugin Objects

Each plugin stores results in its respective object. You can inspect these objects to see if they contain valid name resolution data.

See [Logging guide](./LOGGING.md) and [Debug plugins](./DEBUG_PLUGINS.md) guides for details.

If the object contains no results, the issue may be with DNS settings or network access.

## Improving name resolution

For more details how to improve name resolution refer to the 
[Reverse DNS Documentation](./REVERSE_DNS.md).

