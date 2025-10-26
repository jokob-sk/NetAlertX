#!/bin/bash
set -euo pipefail

read -r -p "Are you sure you want to destroy your host docker containers and images? Type YES to continue: " reply

if [[ "${reply}" == "YES" ]]; then
  docker system prune -af
  docker builder prune -af
else
  echo "Aborted."
  exit 1
fi

echo "Done."
