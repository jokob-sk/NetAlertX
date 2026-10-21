## Overview

Keeps a Dynamic DNS (DDNS) hostname pointed at your current public IP. On each run, the plugin resolves the IP currently published for `DDNS_DOMAIN` (via `dig`) and compares it to the IP NetAlertX already has recorded for the special `Internet` device. If they differ, it calls `DDNS_UPDATE_URL` with your `DDNS_USER`/`DDNS_PASSWORD`/`DDNS_DOMAIN` - the DDNS provider is expected to detect the new IP from the request's own source address, which is how most `username=&password=&hostname=`-style DDNS update APIs work. The default `DDNS_UPDATE_URL` targets Dynu, but any provider using that same query-string convention works by changing the URL.

### Requirements

- A device with MAC `Internet` and an up-to-date `devLastIP` - normally maintained by the `internet_ip` (`INTRNT`) plugin. Without it, the "previous IP" the comparison relies on stays empty and every run looks like a change.
- `dig` and `curl` available in the container (already present in the default image).

### Settings

- `DDNS_DOMAIN` / `DDNS_USER` / `DDNS_PASSWORD`: your DDNS provider's hostname and login credentials.
- `DDNS_UPDATE_URL`: the provider's update endpoint. Defaults to Dynu's `https://api.dynu.com/nic/update?`; swap it for another provider that accepts the same query-string update format.
- `DDNS_RUN`: when to run. Since this only needs to catch a WAN IP change (not run on every scan), an hourly or daily `schedule` is the recommended value over `always_after_scan`.
- `DDNS_WATCH` / `DDNS_REPORT_ON`: control whether and when a notification is sent for this plugin's activity.

### Usage

- Check the Settings page for details.
