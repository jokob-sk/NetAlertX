#!/bin/bash
export INSTALL_DIR=/app

LOG_FILE="${INSTALL_DIR}/log/execution_queue.log"

# Check if there are any entries with cron_restart_backend
if grep -q "cron_restart_backend" "$LOG_FILE"; then
  # Kill all python processes (restart handled by s6 overlay)
  pkill -f "python " && echo 'done'

  # Remove all lines containing cron_restart_backend from the log file
  sed -i '/cron_restart_backend/d' "$LOG_FILE"
fi
