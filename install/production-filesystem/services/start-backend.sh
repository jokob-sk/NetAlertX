#!/bin/bash

cd "${NETALERTX_APP}" || exit 1
max_attempts=50  # 10 seconds total (50 * 0.2s)
attempt=0
while pgrep -x python3 >/dev/null && [ $attempt -lt $max_attempts ]; do
	killall -TERM python3 &>/dev/null
	sleep 0.2
	((attempt++))
done
# Force kill if graceful shutdown failed
killall -KILL python3 &>/dev/null

echo "Starting python3 $(cat /services/config/python/backend-extra-launch-parameters 2>/dev/null) -m server > ${NETALERTX_LOG}/stdout.log 2> >(tee ${NETALERTX_LOG}/stderr.log >&2)"
read -ra EXTRA_PARAMS < <(cat /services/config/python/backend-extra-launch-parameters 2>/dev/null)
exec python3 "${EXTRA_PARAMS[@]}" -m server > "${NETALERTX_LOG}/stdout.log" 2> >(tee "${NETALERTX_LOG}/stderr.log" >&2)
