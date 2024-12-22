# Performance tips

The application runs regular maintenance and DB cleanup tasks. If these tasks fail, you might encounter performance issues. 

Most performance issues are caused by a big database or large log files. Enabling unnecessary plugins will also lead to performance degradation. 

You can always check the size of your database and database tables under the Maintenance page. 

![Db size check](/docs/img/PERFORMANCE/db_size_check.png)

> [!NOTE]
> For around 100 devices the database should be approximately `50MB` and none of the entries (rows) should exceed the value of `10 000` on a healthy system. These numbers will depend on your network activity and settings. 

## Maintenance plugins

There are 2 plugins responsible for maintaining the overal health of the application. One is responsible for the database cleanup and one for other tasks, such as log cleanup. 

### DB Cleanup (DBCLNP)

The database cleanup plugin. Check details and related setting in the [DB Cleanup plugin docs](/front/plugins/db_cleanup/README.md). Make sure the plugin is not failing by checking the logs. Try changing the schedule `DBCLNP_RUN_SCHD` and the timeout `DBCLNP_RUN_TIMEOUT` (increase) if the plugin is failing to execute.

### Maintenance (MAINT)

The maintenance plugin. Check details and related setting in the [Maintenance plugin docs](/front/plugins/maintenance/README.md). Make sure the plugin is not failing by checking the logs. Try changing the schedule `MAINT_RUN_SCHD` and the timeout `MAINT_RUN_TIMEOUT` (increase) if the plugin is failing to execute.

## Scan frequency and coverage

The more often you scan the networks the more resources, traffic and DB read/write cycles are executed. Especially on busy networks and lower end hardware, consider increasing scan intervals (`<PLUGIN>_RUN_SCHD`)  and timeouts (`<PLUGIN>_RUN_TIMEOUT`).

Also consider decreasing the scanned subnet, e.g. from `/16` to `/24` if need be.   

# Store temporary files in memory

You can also store temporary files in application memory (`/app/api` and `/app/log` folders). See highlighted lines `◀` below.

```yaml
version: "3"
services:
  netalertx:
    container_name: netalertx
    # use the below line if you want to test the latest dev image
    # image: "jokobsk/netalertx-dev:latest" 
    image: "jokobsk/netalertx:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/config:/app/config
      - local/path/db:/app/db      
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/app/log
      # (API: OPTION 1) use for performance
      - type: tmpfs              # ◀
        target: /app/api         # ◀
      # (API: OPTION 2) use when debugging issues 
      # -  local/path/api:/app/api
    environment:
      - TZ=Europe/Berlin      
      - PORT=20211
```
