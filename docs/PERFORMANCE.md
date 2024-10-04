# Performance tips

The application runs regular maintenance a DB cleanup tasks. If these tasks fail, you might encounter performance issues. 

Most performance issues are caused by a big database or large log files. Enabling unnecessary plugins will also lead to performance degradation. 

You can always check the size of your database and database tables under the Maintenance page. 

![Db size check](/docs/img/PERFORMANCE/db_size_check.png)

> [!NOTE]
> For around 100 devices the database should be approximately `50MB` and none of the entries (rows) should exceed the value of `10 000` on a healthy system. 

## Maintenance plugins

There are 2 plugins responsible for maintaining the overal health of the application. One is responsible for the database cleanup and one for other tasks, such as log cleanup. 

### DB Cleanup (DBCLNP)

The database cleanup plugin. Check details and related setting in the [DB Cleanup plugin docs](/front/plugins/db_cleanup/README.md). Make sure the plugin is not failing by checking the logs. Try changing the schedule `DBCLNP_RUN_SCHD` and the timeout `DBCLNP_RUN_TIMEOUT` (increase) if the plugin is failing to execute.

### Maintenance (MAINT)

The maintenance plugin. Check details and related setting in the [Maintenance plugin docs](/front/plugins/maintenance/README.md). Make sure the plugin is not failing by checking the logs. Try changing the schedule `MAINT_RUN_SCHD` and the timeout `MAINT_RUN_TIMEOUT` (increase) if the plugin is failing to execute.
