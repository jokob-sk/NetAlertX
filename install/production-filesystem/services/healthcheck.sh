#!/bin/bash

# NetAlertX Comprehensive Health Check Script
# This script verifies all critical services and endpoints are functioning

set -e

EXIT_CODE=0

echo "[HEALTHCHECK] Starting comprehensive health check..."

# Function to log errors and set exit code
log_error() {
    echo "[HEALTHCHECK] ERROR: $1" >&2
    EXIT_CODE=1
}

# Function to log success
log_success() {
    echo "[HEALTHCHECK] ✓ $1"
}

# 1. Check if crond is running
if pgrep -f "crond" > /dev/null; then
    log_success "crond is running"
else
    log_error "crond is not running"
fi

# 2. Check if php-fpm is running
if pgrep -f "php-fpm" > /dev/null; then
    log_success "php-fpm is running"
else
    log_error "php-fpm is not running"
fi

# 3. Check if nginx is running
if pgrep -f "nginx" > /dev/null; then
    log_success "nginx is running"
else
    log_error "nginx is not running"
fi

# 4. Check if python /app/server is running
if pgrep -f "python.*server" > /dev/null; then
    log_success "python /app/server is running"
else
    log_error "python /app/server is not running"
fi

# 5. Check port 20211 is open and contains "netalertx"
if curl -sf --max-time 10 "http://localhost:${PORT:-20211}" | grep -i "netalertx" > /dev/null; then
    log_success "Port ${PORT:-20211} is responding and contains 'netalertx'"
else
    log_error "Port ${PORT:-20211} is not responding or doesn't contain 'netalertx'"
fi

# NOTE: GRAPHQL_PORT might not be set and is initailized as a setting with a default value in the container. It can also be initialized via APP_CONF_OVERRIDE 
# # 6. Check port 20212/graphql returns "graphql" in first lines
# GRAPHQL_PORT=${GRAPHQL_PORT:-20212}
# if curl -sf --max-time 10 "http://localhost:${GRAPHQL_PORT}/graphql" | head -10 | grep -i "graphql" > /dev/null; then
#     log_success "Port ${GRAPHQL_PORT}/graphql is responding with GraphQL content"
# else
#     log_error "Port ${GRAPHQL_PORT}/graphql is not responding or doesn't contain 'graphql'"
# fi

# Summary
if [ $EXIT_CODE -eq 0 ]; then
    echo "[HEALTHCHECK] ✅ All health checks passed"
else
    echo "[HEALTHCHECK] ❌ One or more health checks failed"
fi

exit $EXIT_CODE