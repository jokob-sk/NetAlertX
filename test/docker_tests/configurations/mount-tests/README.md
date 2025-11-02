# Mount Diagnostic Test Configurations

This directory contains docker-compose files for testing all possible mount configurations.

## Generated Files

- `docker-compose.mount-test.db_no-mount.yml`: No mount - use container filesystem for db_no-mount
- `docker-compose.mount-test.db_ramdisk.yml`: RAM disk (tmpfs) for db_ramdisk
- `docker-compose.mount-test.db_mounted.yml`: Proper mount (volume for persistent, none for non-persistent) for db_mounted
- `docker-compose.mount-test.db_unwritable.yml`: Read-only mount for db_unwritable
- `docker-compose.mount-test.config_no-mount.yml`: No mount - use container filesystem for config_no-mount
- `docker-compose.mount-test.config_ramdisk.yml`: RAM disk (tmpfs) for config_ramdisk
- `docker-compose.mount-test.config_mounted.yml`: Proper mount (volume for persistent, none for non-persistent) for config_mounted
- `docker-compose.mount-test.config_unwritable.yml`: Read-only mount for config_unwritable
- `docker-compose.mount-test.api_no-mount.yml`: No mount - use container filesystem for api_no-mount
- `docker-compose.mount-test.api_ramdisk.yml`: RAM disk (tmpfs) for api_ramdisk
- `docker-compose.mount-test.api_mounted.yml`: Proper mount (volume for persistent, none for non-persistent) for api_mounted
- `docker-compose.mount-test.api_unwritable.yml`: Read-only mount for api_unwritable
- `docker-compose.mount-test.log_no-mount.yml`: No mount - use container filesystem for log_no-mount
- `docker-compose.mount-test.log_ramdisk.yml`: RAM disk (tmpfs) for log_ramdisk
- `docker-compose.mount-test.log_mounted.yml`: Proper mount (volume for persistent, none for non-persistent) for log_mounted
- `docker-compose.mount-test.log_unwritable.yml`: Read-only mount for log_unwritable
- `docker-compose.mount-test.run_no-mount.yml`: No mount - use container filesystem for run_no-mount
- `docker-compose.mount-test.run_ramdisk.yml`: RAM disk (tmpfs) for run_ramdisk
- `docker-compose.mount-test.run_mounted.yml`: Proper mount (volume for persistent, none for non-persistent) for run_mounted
- `docker-compose.mount-test.run_unwritable.yml`: Read-only mount for run_unwritable
- `docker-compose.mount-test.active_config_no-mount.yml`: No mount - use container filesystem for active_config_no-mount
- `docker-compose.mount-test.active_config_ramdisk.yml`: RAM disk (tmpfs) for active_config_ramdisk
- `docker-compose.mount-test.active_config_mounted.yml`: Proper mount (volume for persistent, none for non-persistent) for active_config_mounted
- `docker-compose.mount-test.active_config_unwritable.yml`: Read-only mount for active_config_unwritable

## Usage

Run tests using pytest:

```bash
cd /workspaces/NetAlertX/test/docker_tests
pytest test_mount_diagnostics_pytest.py
```

Or run specific scenarios:

```bash
pytest test_mount_diagnostics_pytest.py -k "db_ramdisk"
```
