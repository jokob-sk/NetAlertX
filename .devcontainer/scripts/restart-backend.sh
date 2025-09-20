#!/bin/sh
# Start (or restart) the NetAlertX Python backend under debugpy in background.
# This script is invoked by the VS Code task "Restart GraphQL".
# It exists to avoid complex inline command chains that were being mangled by the task runner.

set -e

LOG_DIR=/app/log
APP_DIR=/app/server
PY=python3
PORT_DEBUG=5678

# Kill any prior debug/run instances
sudo killall python3 2>/dev/null || true
sleep 2


cd "$APP_DIR"

# Launch using absolute module path for clarity; rely on cwd for local imports
setsid nohup ${PY} -m debugpy --listen 0.0.0.0:${PORT_DEBUG} /app/server/__main__.py >/dev/null 2>&1 &
PID=$!
sleep 2

