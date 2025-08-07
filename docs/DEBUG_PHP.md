# Debugging backend PHP issues

## Logs in UI

![Logs UI](./img/DEBUG/maintenance_debug_php.png)

You can view recent backend PHP errors directly in the **Maintenance > Logs** section of the UI. This provides quick access to logs without needing terminal access.

## Accessing logs directly

Sometimes, the UI might not be accessible. In that case, you can access the logs directly inside the container.

### Step-by-step:

1. **Open a shell into the container:**

   ```bash
   docker exec -it netalertx /bin/sh
   ```

2. **Check the NGINX error log:**

   ```bash
   cat /var/log/nginx/error.log
   ```

3. **Check the PHP application error log:**

   ```bash
   cat /app/log/app.php_errors.log
   ```

These logs will help identify syntax issues, fatal errors, or startup problems when the UI fails to load properly.

