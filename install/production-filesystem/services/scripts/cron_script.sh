#!/bin/bash
export INSTALL_DIR=/app



# Check if there are any entries with cron_restart_backend
if grep -q "cron_restart_backend" "${LOG_EXECUTION_QUEUE}"; then
  echo "$(date): Restarting backend triggered by cron_restart_backend"
  
  # Create marker for entrypoint.sh to restart the service instead of killing the container
  touch /tmp/backend_restart_pending
  
  killall python3 || echo "killall python3 failed or no process found"

  # Remove all lines containing cron_restart_backend from the log file
  # Atomic replacement with temp file
  grep -v "cron_restart_backend" "${LOG_EXECUTION_QUEUE}" > "${LOG_EXECUTION_QUEUE}.tmp"
  mv "${LOG_EXECUTION_QUEUE}.tmp" "${LOG_EXECUTION_QUEUE}"
fi
