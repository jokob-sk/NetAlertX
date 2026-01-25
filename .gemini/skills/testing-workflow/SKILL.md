---
name: testing-workflow
description: Guide for running tests within the NetAlertX environment. Detailed instructions for standard unit tests (fast), full suites (slow), and handling authentication.
---

# Testing Workflow

**Crucial:** Tests MUST be run inside the container to access the correct runtime environment (DB, Config, Dependencies).

## 1. Standard Unit Tests (Recommended)

By default, run the standard unit test suite. This **excludes** slow tests marked with `docker` (requires socket access) or `feature_complete` (extended coverage).

```bash
docker exec <CONTAINER_ID> bash -c "cd /workspaces/NetAlertX && pytest -m 'not docker and not feature_complete'"
```

## 2. Full Test Suite (Slow)

To run **all** tests, including integration tests that require Docker socket access and extended feature coverage:

```bash
docker exec <CONTAINER_ID> bash -c "cd /workspaces/NetAlertX && pytest"
```

## 3. Running Specific Tests

To run a specific file or folder:

```bash
docker exec <CONTAINER_ID> bash -c "cd /workspaces/NetAlertX && pytest <path_to_test>"
```

*Example:*
```bash
docker exec <CONTAINER_ID> bash -c "cd /workspaces/NetAlertX && pytest test/api_endpoints/test_mcp_extended_endpoints.py"
```

## Authentication in Tests

The test environment uses `API_TOKEN`. The most reliable way to retrieve the current token from a running container is:

```bash
docker exec <CONTAINER_ID> python3 -c "from helper import get_setting_value; print(get_setting_value('API_TOKEN'))"
```

### Troubleshooting

If tests fail with 403 Forbidden or empty tokens:
1. Verify server is running and use the setup script (`/workspaces/NetAlertX/.devcontainer/scripts/setup.sh`) if required.
2. Verify `app.conf` inside the container: `docker exec <ID> cat /data/config/app.conf`
3. Verify Python can read it: `docker exec <ID> python3 -c "from helper import get_setting_value; print(get_setting_value('API_TOKEN'))"`