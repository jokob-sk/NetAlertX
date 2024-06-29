#!/bin/bash
export INSTALL_DIR=/app

LOG_FILE="${INSTALL_DIR}/front/log/execution_queue.log"

# Check if there are any entries with cron_restart_backend
if grep -q "cron_restart_backend" "$LOG_FILE"; then
  # Kill all python processes and restart the server
  pkill -f "python " && (python ${INSTALL_DIR}/server > /dev/null 2>&1 &) && echo 'done'

  # Remove all lines containing cron_restart_backend from the log file
  sed -i '/cron_restart_backend/d' "$LOG_FILE"
fi
