# Performance Optimization Guide

There are several ways to improve the application's performance. The application has been tested on a range of devices, from a Raspberry Pi 4 to NAS and NUC systems. If you are running the application on a lower-end device, carefully fine-tune the performance settings to ensure an optimal user experience.

## Common Causes of Slowness

Performance issues are usually caused by:

- **Incorrect settings** – The app may restart unexpectedly. Check `app.log` under **Maintenance → Logs** for details.
- **Too many background processes** – Disable unnecessary scanners.
- **Long scan durations** – Limit the number of scanned devices.
- **Excessive disk operations** – Optimize scanning and logging settings.
- **Failed maintenance plugins** – Ensure maintenance tasks are running properly.

The application performs regular maintenance and database cleanup. If these tasks fail, performance may degrade.

### Database and Log File Size

A large database or oversized log files can slow down performance. You can check database and table sizes on the **Maintenance** page.

![DB size check](./img/PERFORMANCE/db_size_check.png)

> [!NOTE]
> - For **~100 devices**, the database should be around **50MB**.
> - No table should exceed **10,000 rows** in a healthy system.
> - These numbers vary based on network activity and settings.

---

## Maintenance Plugins

Two plugins help maintain the application’s performance:

### **1. Database Cleanup (DBCLNP)**
- Responsible for database maintenance.
- Check settings in the [DB Cleanup Plugin Docs](/front/plugins/db_cleanup/README.md).
- Ensure it’s not failing by checking logs.
- Adjust the schedule (`DBCLNP_RUN_SCHD`) and timeout (`DBCLNP_RUN_TIMEOUT`) if needed.

### **2. Maintenance (MAINT)**
- Handles log cleanup and other maintenance tasks.
- Check settings in the [Maintenance Plugin Docs](/front/plugins/maintenance/README.md).
- Ensure it’s running correctly by checking logs.
- Adjust the schedule (`MAINT_RUN_SCHD`) and timeout (`MAINT_RUN_TIMEOUT`) if needed.

---

## Scan Frequency and Coverage

Frequent scans increase resource usage, network traffic, and database read/write cycles.

### **Optimizations**
- **Increase scan intervals** (`<PLUGIN>_RUN_SCHD`) on busy networks or low-end hardware.
- **Extend scan timeouts** (`<PLUGIN>_RUN_TIMEOUT`) to prevent failures.
- **Reduce the subnet size** – e.g., from `/16` to `/24` to lower scan loads.

Some plugins have additional options to limit the number of scanned devices. If certain plugins take too long to complete, check if you can optimize scan times by selecting a scan range. 

For example, the **ICMP plugin** allows you to specify a regular expression to scan only IPs that match a specific pattern.

---

## Storing Temporary Files in Memory

On systems with slower I/O speeds, you can optimize performance by storing temporary files in memory. This primarily applies to the API directory (default: `/tmp/api`, configurable via `NETALERTX_API`) and `/tmp/log` folders.

Using `tmpfs` reduces disk writes and improves performance. However, it should be **disabled** if persistent logs or API data storage are required.

Below is an optimized `docker-compose.yml` snippet:


```yaml
version: "3"
services:
  netalertx:
    container_name: netalertx
    # Uncomment the line below to test the latest dev image
    # image: "ghcr.io/jokob-sk/netalertx-dev:latest"
    image: "ghcr.io/jokob-sk/netalertx:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - /local_data_dir/config:/data/config
      - /local_data_dir/db:/data/db      
      # (Optional) Useful for debugging setup issues
      - /local_data_dir/logs:/tmp/log
      # (API: OPTION 1) Store temporary files in memory (recommended for performance)
      - type: tmpfs              # ◀ 🔺
        target: /tmp/api         # ◀ 🔺
      # (API: OPTION 2) Store API data on disk (useful for debugging)
      # - /local_data_dir/api:/tmp/api
      # Ensuring the timezone is the same as on the server - make sure also the TIMEZONE setting is configured
      - /etc/localtime:/etc/localtime:ro    
    environment: 
      - PORT=20211

```
