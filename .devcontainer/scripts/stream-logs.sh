#!/bin/sh
# Stream NetAlertX logs to stdout so the Dev Containers output channel shows them.
# This script waits briefly for the files to appear and then tails them with -F.

LOG_FILES="/app/log/app.log  /app/log/db_is_locked.log /app/log/execution_queue.log /app/log/app_front.log /app/log/app.php_errors.log /app/log/IP_changes.log /app/stderr.log /app/stdout.log"

wait_for_files() {
  # Wait up to ~10s for at least one of the files to exist
  attempts=0
  while [ $attempts -lt 20 ]; do
    for f in $LOG_FILES; do
      if [ -f "$f" ]; then
        return 0
      fi
    done
    attempts=$((attempts+1))
    sleep 0.5
  done
  return 1
}

if wait_for_files; then
  echo "Starting log stream for:"
  for f in $LOG_FILES; do
    [ -f "$f" ] && echo "  $f"
  done

  # Use tail -F where available. If tail -F isn't supported, tail -f is used as fallback.
  # Some minimal images may have busybox tail without -F; this handles both.
  if tail --version >/dev/null 2>&1; then
    # GNU tail supports -F
    tail -n +1 -F $LOG_FILES
  else
    # Fallback to -f for busybox; will exit if files rotate or do not exist initially
    tail -n +1 -f $LOG_FILES
  fi
else
  echo "No log files appeared after wait; exiting stream script."
  exit 0
fi
