#!/bin/sh
# first-run-check.sh - Checks and initializes configuration files on first run

# Check for app.conf
if [ ! -f /app/config/app.conf ]; then
    mkdir -p /app/config
    cp /app/back/app.conf /app/config/app.conf
    echo "🆕 First run detected: Default configuration initialized." >&2
fi

# Check for app.db
if [ ! -f /app/db/app.db ]; then
    mkdir -p /app/db
    cp /app/back/app.db /app/db/app.db
    echo "🆕 First run detected: Fresh database created." >&2
fi
