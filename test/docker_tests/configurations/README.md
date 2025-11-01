# NetAlertX Docker Test Configurations

This directory contains docker-compose configurations for different test scenarios.

## Available Configurations

### readonly
- **File**: `docker-compose.readonly.yml`
- **Description**: Tests with a read-only container filesystem
- **Use case**: Verify that the application works correctly when the container filesystem is read-only

### writable
- **File**: `docker-compose.writable.yml`
- **Description**: Tests with writable tmpfs mounts for performance
- **Use case**: Standard testing with optimized writable directories

## Mount Diagnostic Tests

The `mount-tests/` subdirectory contains 24 docker-compose configurations that test all possible mount scenarios for each path that NetAlertX monitors:

- **6 paths**: `/app/db`, `/app/config`, `/app/api`, `/app/log`, `/services/run`, `/services/config/nginx/conf.active`
- **4 scenarios per path**: `no-mount`, `ramdisk`, `mounted`, `unwritable`
- **Total**: 24 comprehensive test configurations

### Running Tests

Use pytest to run the mount diagnostic tests:

```bash
cd /workspaces/NetAlertX/test/docker_tests
pytest test_mount_diagnostics_pytest.py -v
```

Or run specific test scenarios:

```bash
pytest test_mount_diagnostics_pytest.py -k "db_ramdisk"
```

### Test Coverage

Each test validates that the mount diagnostic tool (`/entrypoint.d/10-mounts.py`) correctly identifies:
- **Good configurations**: No issues reported, exit code 0
- **Bad configurations**: Issues detected in table format, exit code 1

The tests ensure that persistent paths (db, config) require durable storage (volumes) while non-persistent paths (api, log, run) benefit from fast storage (tmpfs).