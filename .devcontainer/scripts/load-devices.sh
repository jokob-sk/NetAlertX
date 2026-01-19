#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
if [ -n "${CSV_PATH:-}" ]; then
  : # user provided CSV_PATH
else
  # Portable mktemp fallback: try GNU coreutils first, then busybox-style
  if mktemp --version >/dev/null 2>&1; then
    CSV_PATH="$(mktemp --tmpdir netalertx-devices-XXXXXX.csv 2>/dev/null || mktemp /tmp/netalertx-devices-XXXXXX.csv)"
  else
    CSV_PATH="$(mktemp -t netalertx-devices.XXXXXX 2>/dev/null || mktemp /tmp/netalertx-devices-XXXXXX.csv)"
  fi
fi
DEVICE_COUNT="${DEVICE_COUNT:-255}"
SEED="${SEED:-20211}"
NETWORK_CIDR="${NETWORK_CIDR:-192.168.50.0/22}"
DB_DIR="${NETALERTX_DB:-/data/db}"
DB_FILE="${DB_DIR%/}/app.db"

# Ensure we are inside the devcontainer
"${SCRIPT_DIR}/isDevContainer.sh" >/dev/null

if [ ! -f "${DB_FILE}" ]; then
  echo "[load-devices] Database not found at ${DB_FILE}. Is the devcontainer initialized?" >&2
  exit 1
fi

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "[load-devices] sqlite3 is required but not installed." >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "[load-devices] python3 is required but not installed." >&2
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "[load-devices] curl is required but not installed." >&2
  exit 1
fi

# Generate synthetic device inventory CSV
python3 "${REPO_ROOT}/scripts/generate-device-inventory.py" \
  --output "${CSV_PATH}" \
  --devices "${DEVICE_COUNT}" \
  --seed "${SEED}" \
  --network "${NETWORK_CIDR}" >/dev/null

echo "[load-devices] CSV generated at ${CSV_PATH} (devices=${DEVICE_COUNT}, seed=${SEED})"

API_TOKEN="$(sqlite3 "${DB_FILE}" "SELECT setValue FROM Settings WHERE setKey='API_TOKEN';")"
GRAPHQL_PORT="$(sqlite3 "${DB_FILE}" "SELECT setValue FROM Settings WHERE setKey='GRAPHQL_PORT';")"

if [ -z "${API_TOKEN}" ] || [ -z "${GRAPHQL_PORT}" ]; then
  echo "[load-devices] Failed to read API_TOKEN or GRAPHQL_PORT from ${DB_FILE}" >&2
  exit 1
fi

IMPORT_URL="http://localhost:${GRAPHQL_PORT}/devices/import"

HTTP_CODE=$(curl -sS -o /tmp/load-devices-response.json -w "%{http_code}" \
  -X POST "${IMPORT_URL}" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -F "file=@${CSV_PATH}")

if [ "${HTTP_CODE}" != "200" ]; then
  echo "[load-devices] Import failed with HTTP ${HTTP_CODE}. Response:" >&2
  cat /tmp/load-devices-response.json >&2
  exit 1
fi

# Fetch totals for a quick sanity check
TOTALS=$(curl -sS -H "Authorization: Bearer ${API_TOKEN}" "http://localhost:${GRAPHQL_PORT}/devices/totals" || true)

echo "[load-devices] Import succeeded (HTTP ${HTTP_CODE})."
echo "[load-devices] Devices totals: ${TOTALS}"
echo "[load-devices] Done. CSV kept at ${CSV_PATH}"
