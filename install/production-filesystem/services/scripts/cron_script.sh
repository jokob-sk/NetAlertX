#!/bin/bash
export INSTALL_DIR=/app



# Check if there are any entries with cron_restart_backend
if grep -q "cron_restart_backend" "${LOG_EXECUTION_QUEUE}"; then
  killall python3
  sleep 2
  /services/start-backend.sh >/dev/null 2>&1 &

  # Remove all lines containing cron_restart_backend from the log file
  # Atomic replacement with temp file
  grep -v "cron_restart_backend" "${LOG_EXECUTION_QUEUE}" > "${LOG_EXECUTION_QUEUE}.tmp"
  mv "${LOG_EXECUTION_QUEUE}.tmp" "${LOG_EXECUTION_QUEUE}"
fi
