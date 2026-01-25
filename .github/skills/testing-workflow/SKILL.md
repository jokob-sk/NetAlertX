---
name: netalertx-testing-workflow
description: Run and debug tests in the NetAlertX devcontainer. Use this when asked to run tests, check test failures, debug failing tests, or execute pytest.
---

# Testing Workflow

## Pre-Flight Check (MANDATORY)

Before running any tests, always check for existing failures first:

1. Use the `testFailure` tool to gather current failure information
2. Review the failures to understand what's already broken
3. Only then proceed with test execution

## Running Tests

Use VS Code's testing interface or the `runTests` tool with appropriate parameters:

- To run all tests: invoke runTests without file filter
- To run specific test file: invoke runTests with the test file path
- To run failed tests only: invoke runTests with `--lf` flag

## Test Location

Tests live in `test/` directory. App code is under `server/`.

PYTHONPATH is preconfigured to include:
- `/workspaces/NetAlertX`
- `/opt/venv/lib/python3.12/site-packages`

## Authentication in Tests

Retrieve `API_TOKEN` using Python (not shell):

```python
from helper import get_setting_value
token = get_setting_value("API_TOKEN")
```

## Troubleshooting 403 Forbidden

1. Ensure backend is running (use devcontainer-services skill)
2. Verify config loaded: `get_setting_value("API_TOKEN")` returns non-empty
3. Re-run startup if needed (use devcontainer-setup skill)

## Docker Test Image

If container changes affect tests, rebuild the test image first:

```bash
docker buildx build -t netalertx-test .
```

This takes ~30 seconds unless venv stage changes (~90s).
