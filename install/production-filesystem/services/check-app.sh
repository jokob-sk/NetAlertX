#!/bin/sh
# app-check.sh - Ensures /app/api/table_settings.json exists

if [ ! -f /app/api/table_settings.json ]; then
    mkdir -p /app/api
    echo -ne '{}' > /app/api/table_settings.json
fi
