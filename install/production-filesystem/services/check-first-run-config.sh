#!/bin/sh
# first-run-check.sh - Checks and initializes configuration files on first run

# Check for app.conf and deploy if required
if [ ! -f /app/config/app.conf ]; then
    mkdir -p /app/config
    cp /app/back/app.conf /app/config/app.conf
    echo "🆕 First run detected: Default configuration initialized." >&2
fi

