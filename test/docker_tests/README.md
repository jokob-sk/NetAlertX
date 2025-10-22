# Alpine Docker tests

This is intended to be run as Root user as permissions are altered. It will create and analyze the results of various configurations on containers. The test craeates a container, logs the results, terminates the container, then starts the next test
0. No errors on startup
   1. missing config/db generation
   2. After config/db generation
1. root user mount on 
   1. /app/db
   2. /app/config
   3. /app/log
   4. /app/api
   5. /services/config/nginx/conf.active
   6. /services/run/
2. 000 permissions on
   1. /app/db
   2. /app/db/app.db
   3. /app/config
   4. /app/config/app.conf
   5. /app/log
   6. /app/api
   7. /services/config/nginx/conf.active
   8. /services/run/
3. Container read-only missing mounts
   1. /app/db
   2. /app/config
   3. /app/log
   4. /app/api
   5. /services/config/nginx/conf.active
   6. /services/run/
4. Custom port/listen address without /services/config/nginx/conf.active mount
5. Missing cap NET_ADMIN, NET_RAW, NET_BIND_SERVICE
6. Run as Root user
7. Run as user 1000
8. Run without network_mode host
9.  Missing /app/config/app.conf
10. Missing /app/db/app.db
11. Ramdisk mounted on 
    1.  /app/config
    2.  /app/db