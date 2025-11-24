#!/bin/bash
export INSTALL_DIR=/app

if [ -f "${LOG_EXECUTION_QUEUE}" ] && grep -q "cron_restart_backend" "${LOG_EXECUTION_QUEUE}"; then
  echo "$(date): Restarting backend triggered by cron_restart_backend"
  killall python3 || echo "killall python3 failed or no process found"
  sleep 2
  /services/start-backend.sh &

  # Remove all lines containing cron_restart_backend from the log file
  # Atomic replacement with temp file. grep returns 1 if no lines selected (file becomes empty), which is valid here.
  grep -v "cron_restart_backend" "${LOG_EXECUTION_QUEUE}" > "${LOG_EXECUTION_QUEUE}.tmp"
  RC=$?
  if [ $RC -eq 0 ] || [ $RC -eq 1 ]; then
    mv "${LOG_EXECUTION_QUEUE}.tmp" "${LOG_EXECUTION_QUEUE}"
  fi
fi
