#!/bin/bash
set -euo pipefail

if [[ -n "${CONFIRM_PRUNE:-}" && "${CONFIRM_PRUNE}" == "YES" ]]; then
  reply="YES"
else
  read -r -p "Are you sure you want to destroy your host docker containers and images? Type YES to continue: " reply
fi

if [[ "${reply}" == "YES" ]]; then
  docker system prune -af
  docker builder prune -af
else
  echo "Aborted."
  exit 1
fi

echo "Done."
