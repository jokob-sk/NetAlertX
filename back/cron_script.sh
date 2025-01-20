#!/bin/bash
export INSTALL_DIR=/app

LOG_FILE="${INSTALL_DIR}/log/execution_queue.log"

# Check if there are any entries with cron_restart_backend
if grep -q "cron_restart_backend" "$LOG_FILE"; then
  # Restart python application using s6
  s6-svc -r /var/run/s6-rc/servicedirs/netalertx
  echo 'done'

  # Remove all lines containing cron_restart_backend from the log file
  sed -i '/cron_restart_backend/d' "$LOG_FILE"
fi
