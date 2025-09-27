#!/bin/sh
# check_nmap_caps.sh - Uses a real nmap command to detect missing container
# privileges and warns the user. It is silent on success.

# Run a fast nmap command that requires raw sockets, capturing only stderr.
ERROR_OUTPUT=$(nmap --privileged -sS -p 20211 127.0.0.1 2>&1 >/dev/null)
EXIT_CODE=$?

# If the exit code is exactly 126 AND the error message contains a known permission error...
if [ "$EXIT_CODE" -eq 126 ] && \
   echo "$ERROR_OUTPUT" | grep -q -e "Operation not permitted" -e "requires root privileges"
then
    # ...then print the detailed warning.
    echo "⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️" >&2
    echo "  ATTENTION: This container is running without elevated" >&2
    echo "             network privileges (NET_RAW/NET_ADMIN)." >&2
    echo "" >&2
    echo "  Advanced network tools that require raw socket access," >&2
    echo "  like 'nmap -sS', will fail." >&2
    echo "" >&2
    echo "  To fix this, restart the container with the following flags:" >&2
    echo "  --cap-add=NET_RAW --cap-add=NET_ADMIN" >&2
    echo "⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️" >&2
    exit 1
fi