#!/bin/sh
# check-ports.sh detects and warns if required ports are already in use
# or if they are configured to be the same.
# Intended for lightweight Alpine containers (uses busybox netstat).

# Define ports from ENV variables, applying defaults
PORT_APP=${PORT:-20211}

# Prefer explicit GRAPHQL_PORT, fall back to parsed override if present.
if [ -n "${APP_CONF_OVERRIDE:-}" ]; then
    # crude parse: look for GRAPHQL_PORT in JSON-like string
    PORT_GQL=$(printf '%s' "${APP_CONF_OVERRIDE}" | grep -o 'GRAPHQL_PORT"*[:=]\"*[0-9]\+' | tr -cd '0-9' || true)
fi
PORT_GQL=${PORT_GQL:-${GRAPHQL_PORT:-20212}}

# Check if ports are configured to be the same
if [ "${PORT_APP}" -eq "${PORT_GQL}" ]; then
    cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  Configuration Warning: Both ports are set to ${PORT_APP}.

    The Application port (\$PORT) and the GraphQL API port (\$GRAPHQL_PORT)
    are configured to use the same port. This will cause a conflict.

    https://docs.netalertx.com/docker-troubleshooting/port-conflicts
══════════════════════════════════════════════════════════════════════════════
EOF
fi

# Check for netstat (usually provided by busybox)
if ! command -v netstat >/dev/null 2>&1; then
    cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  Configuration Error: 'netstat' command not found.

    Cannot check port availability. Please ensure 'net-tools'
    or the busybox 'netstat' applet is available in this container.
══════════════════════════════════════════════════════════════════════════════
EOF
    exit 0 # Exit gracefully, this is a non-fatal check
fi

# Fetch all listening TCP/UDP ports once.
# We awk $4 to get the 'Local Address' column (e.g., 0.0.0.0:20211 or :::20211)
LISTENING_PORTS=$(netstat -lntu | awk '{print $4}')

# Check Application Port
# We grep for ':{PORT}$' to match the port at the end of the string.
if echo "$LISTENING_PORTS" | grep -q ":${PORT_APP}$"; then
    cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  Port Warning: Application port ${PORT_APP} is already in use.

    The main application (defined by \$PORT) may fail to start.

    https://docs.netalertx.com/docker-troubleshooting/port-conflicts
══════════════════════════════════════════════════════════════════════════════
EOF
fi

# Check GraphQL Port (always emit if listening, even if same port)
if echo "$LISTENING_PORTS" | grep -q ":${PORT_GQL}$"; then
    cat <<EOF
══════════════════════════════════════════════════════════════════════════════
⚠️  Port Warning: GraphQL API port ${PORT_GQL} is already in use.

    The GraphQL API (defined by \$APP_CONF_OVERRIDE or \$GRAPHQL_PORT)
    may fail to start.

    https://docs.netalertx.com/docker-troubleshooting/port-conflicts
══════════════════════════════════════════════════════════════════════════════
EOF
fi