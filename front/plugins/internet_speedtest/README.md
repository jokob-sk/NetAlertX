## Overview

A plugin allowing for executing regular internet speed tests. 

### Usage

This plugin supports two engines:
1.  **Baseline Engine**: Uses the Python `speedtest-cli` library (default).
2.  **Native Engine (Optimized)**: Uses the native Ookla Speedtest binary.

#### Opt-in for Native Engine
To use the native engine:
- Provide the native `speedtest` binary in your environment: [Speedtest CLI Homepage](https://www.speedtest.net/apps/cli)
- Map the binary to `/usr/bin/speedtest` in the container.
- **Ensure the native speedtest binary is installed on the host at the source path.**

```yaml
volumes:
  - /usr/bin/speedtest:/usr/bin/speedtest:ro
```
-  The plugin will automatically detect and use it for subsequent tests.


### Data Mapping

- **Watched_Value1** — Download Speed (Mbps).
- **Watched_Value2** — Upload Speed (Mbps).
- **Watched_Value3** — Full JSON payload (useful for n8n or detailed webhooks).

### Notes

- The native binary is recommended for connections > 100 Mbps.
- If the native binary is not detected, the plugin seamlessly falls back to the baseline library.