#!/bin/sh
# Quick port/service enumerator for host-network dev container.
# Shows which processes are bound to key NetAlertX ports.
PORTS="20211 20212 9003 9000 5678"
printf "%-8s %-22s %-8s %s\n" PORT BIND LISTEN_PID COMMAND
for p in $PORTS; do
  line=$(ss -ltnp 2>/dev/null | awk -v P=":${p}" '$4 ~ P {print $0; exit}')
  if [ -n "$line" ]; then
    addr=$(echo "$line" | awk '{print $4}')
    pid=$(echo "$line" | sed -n 's/.*pid=\([0-9]*\).*/\1/p')
    cmd="$( [ -n "$pid" ] && ps -o comm= -p "$pid" 2>/dev/null)"
    printf "%-8s %-22s %-8s %s\n" "$p" "$addr" "${pid:-?}" "${cmd:-?}"
  else
    printf "%-8s %-22s %-8s %s\n" "$p" "(not listening)" "-" "-"
  fi
done

# Show any other NetAlertX-related listeners (nginx, php-fpm, python backend)
ss -ltnp 2>/dev/null | egrep 'nginx|php-fpm|python' || true
