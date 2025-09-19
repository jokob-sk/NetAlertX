#!/bin/sh
# shellcheck shell=sh
# Simple helper to run pytest inside the devcontainer with correct paths
set -eu

# Ensure we run from the workspace root
cd /workspaces/NetAlertX

# Make sure PYTHONPATH includes server and workspace
export PYTHONPATH="/workspaces/NetAlertX:/workspaces/NetAlertX/server:/app:/app/server:${PYTHONPATH:-}"

# Default to running the full test suite under /workspaces/NetAlertX/test
pytest -q --maxfail=1 --disable-warnings test "$@"
