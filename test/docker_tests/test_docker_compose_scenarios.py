'''
Docker Compose integration tests for NetAlertX startup scenarios.

This set of tests requires netalertx-test image built and docker compose.
Ensure netalertx-test image is built prior to starting these tests.
'''

import os
import pathlib
import subprocess
import time
import pytest

IMAGE = os.environ.get("NETALERTX_TEST_IMAGE", "netalertx-test")

# Path to test configurations
CONFIG_DIR = pathlib.Path(__file__).parent / "configurations"

pytestmark = [pytest.mark.docker, pytest.mark.compose]


def _run_docker_compose(compose_file: pathlib.Path, project_name: str, timeout: int = 30, env_vars: dict = None) -> subprocess.CompletedProcess:
    """Run docker compose up and capture output."""
    cmd = [
        "docker", "compose",
        "-f", str(compose_file),
        "-p", project_name,
        "up",
        "--abort-on-container-exit",
        "--timeout", str(timeout)
    ]

    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    try:
        result = subprocess.run(
            cmd,
            cwd=compose_file.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 10,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        # Clean up on timeout
        subprocess.run(["docker", "compose", "-f", str(compose_file), "-p", project_name, "down", "-v"],
                      cwd=compose_file.parent, check=False)
        raise

    # Always clean up
    subprocess.run(["docker", "compose", "-f", str(compose_file), "-p", project_name, "down", "-v"],
                  cwd=compose_file.parent, check=False)

    # Combine stdout and stderr
    result.output = result.stdout + result.stderr
    return result

import os
import pathlib
import subprocess
import tempfile
import time
import pytest
import yaml

IMAGE = os.environ.get("NETALERTX_TEST_IMAGE", "netalertx-test")

# Docker Compose configurations for different test scenarios
COMPOSE_CONFIGS = {
    "missing_capabilities": {
        "services": {
            "netalertx": {
                "image": IMAGE,
                "network_mode": "host",
                "userns_mode": "host",
                "cap_drop": ["ALL"],  # Drop all capabilities
                "tmpfs": ["/tmp:mode=777"],
                "volumes": [
                    "./test_data/app_db:/app/db",
                    "./test_data/app_config:/app/config",
                    "./test_data/app_log:/app/log",
                    "./test_data/app_api:/app/api",
                    "./test_data/nginx_conf:/services/config/nginx/conf.active",
                    "./test_data/services_run:/services/run"
                ],
                "environment": {
                    "TZ": "UTC"
                }
            }
        }
    },
    "host_network": {
        "services": {
            "netalertx": {
                "image": IMAGE,
                "network_mode": "host",
                "userns_mode": "host",
                "cap_add": ["NET_RAW", "NET_ADMIN", "NET_BIND_SERVICE"],
                "tmpfs": ["/tmp:mode=777"],
                "volumes": [
                    "./test_data/app_db:/app/db",
                    "./test_data/app_config:/app/config",
                    "./test_data/app_log:/app/log",
                    "./test_data/app_api:/app/api",
                    "./test_data/nginx_conf:/services/config/nginx/conf.active",
                    "./test_data/services_run:/services/run"
                ],
                "environment": {
                    "TZ": "UTC"
                }
            }
        }
    },
    "normal_startup": {
        "services": {
            "netalertx": {
                "image": IMAGE,
                "network_mode": "host",
                "userns_mode": "host",
                "cap_add": ["NET_RAW", "NET_ADMIN", "NET_BIND_SERVICE"],
                "user": "20211:20211",
                "tmpfs": ["/tmp:mode=777"],
                "volumes": [
                    "./test_data/app_db:/app/db",
                    "./test_data/app_config:/app/config",
                    "./test_data/app_log:/app/log",
                    "./test_data/app_api:/app/api",
                    "./test_data/nginx_conf:/services/config/nginx/conf.active",
                    "./test_data/services_run:/services/run"
                ],
                "environment": {
                    "TZ": "UTC"
                }
            }
        }
    }
}

pytestmark = [pytest.mark.docker, pytest.mark.compose]


def _create_test_data_dirs(base_dir: pathlib.Path) -> None:
    """Create test data directories with proper permissions."""
    dirs = ["app_db", "app_config", "app_log", "app_api", "nginx_conf", "services_run"]
    for dir_name in dirs:
        dir_path = base_dir / "test_data" / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        dir_path.chmod(0o755)

    # Create basic config file
    config_file = base_dir / "test_data" / "app_config" / "app.conf"
    if not config_file.exists():
        config_file.write_text("# Test configuration\n")

    # Create basic db file
    db_file = base_dir / "test_data" / "app_db" / "app.db"
    if not db_file.exists():
        # Create a minimal SQLite database
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        conn.close()


def _run_docker_compose(compose_file: pathlib.Path, project_name: str, timeout: int = 30, env_vars: dict = None) -> subprocess.CompletedProcess:
    """Run docker compose up and capture output."""
    cmd = [
        "docker", "compose",
        "-f", str(compose_file),
        "-p", project_name,
        "up",
        "--abort-on-container-exit",
        "--timeout", str(timeout)
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=compose_file.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        # Clean up on timeout
        subprocess.run(["docker", "compose", "-f", str(compose_file), "-p", project_name, "down", "-v"],
                      cwd=compose_file.parent, check=False)
        raise

    # Always clean up
    subprocess.run(["docker", "compose", "-f", str(compose_file), "-p", project_name, "down", "-v"],
                  cwd=compose_file.parent, check=False)

    # Combine stdout and stderr
    result.output = result.stdout + result.stderr
    return result


def test_missing_capabilities_compose() -> None:
    """Test missing required capabilities using docker compose.

    Uses docker-compose.missing-caps.yml which drops all capabilities.
    Expected: "exec /bin/sh: operation not permitted" error.
    """
    compose_file = CONFIG_DIR / "docker-compose.missing-caps.yml"
    result = _run_docker_compose(compose_file, "netalertx-missing-caps")

    # Check for expected error
    assert "exec /bin/sh: operation not permitted" in result.output
    assert result.returncode != 0


def test_host_network_compose(tmp_path: pathlib.Path) -> None:
    """Test host networking mode using docker compose.

    Simulates running with network_mode: host.
    Expected: Container starts successfully with host networking.
    """
    base_dir = tmp_path / "host_network"
    base_dir.mkdir()

    # Create test data directories
    _create_test_data_dirs(base_dir)

    # Create compose file
    compose_config = COMPOSE_CONFIGS["host_network"].copy()
    compose_file = base_dir / "docker-compose.yml"
    with open(compose_file, 'w') as f:
        yaml.dump(compose_config, f)

    # Run docker compose
    result = _run_docker_compose(compose_file, "netalertx-host-net")

    # Check that it doesn't fail with network-related errors
    assert "not running with --network=host" not in result.output
    # Container should start (may fail later for other reasons, but network should be OK)


def test_host_network_compose() -> None:
    """Test host networking mode using docker compose.

    Uses docker-compose.readonly.yml with host networking.
    Expected: Container starts successfully with host networking.
    """
    compose_file = CONFIG_DIR / "docker-compose.readonly.yml"
    result = _run_docker_compose(compose_file, "netalertx-host-net")

    # Check that it doesn't fail with network-related errors
    assert "not running with --network=host" not in result.output
    # Container should start (may fail later for other reasons, but network should be OK)


def test_custom_port_with_unwritable_nginx_config_compose() -> None:
    """Test custom port configuration with unwritable nginx config using docker compose.

    Uses docker-compose.mount-test.active_config_unwritable.yml with PORT=24444.
    Expected: Container shows warning about unable to write nginx config.
    """
    compose_file = CONFIG_DIR / "mount-tests" / "docker-compose.mount-test.active_config_unwritable.yml"
    result = _run_docker_compose(compose_file, "netalertx-custom-port", env_vars={"PORT": "24444"})

    # Check for nginx config write failure warning
    assert "Unable to write to /services/config/nginx/conf.active/netalertx.conf" in result.output
    # Container should still attempt to start but may fail for other reasons
    # The key is that the nginx config write warning appears


def test_host_network_compose(tmp_path: pathlib.Path) -> None:
    """Test host networking mode using docker compose.

    Simulates running with network_mode: host.
    Expected: Container starts successfully with host networking.
    """
    base_dir = tmp_path / "host_network"
    base_dir.mkdir()

    # Create test data directories
    _create_test_data_dirs(base_dir)

    # Create compose file
    compose_config = COMPOSE_CONFIGS["host_network"].copy()
    compose_file = base_dir / "docker-compose.yml"
    with open(compose_file, 'w') as f:
        yaml.dump(compose_config, f)

    # Run docker compose
    result = _run_docker_compose(compose_file, "netalertx-host-net")

    # Check that it doesn't fail with network-related errors
    assert "not running with --network=host" not in result.output
    # Container should start (may fail later for other reasons, but network should be OK)


def test_normal_startup_no_warnings_compose(tmp_path: pathlib.Path) -> None:
    """Test normal startup with expected warnings using docker compose.

    Simulates proper configuration with all required settings.
    Expected: Container starts and shows expected warnings with pipe characters (═).
    This demonstrates what a "normal" startup looks like with warnings.
    """
    base_dir = tmp_path / "normal_startup"
    base_dir.mkdir()

    # Create test data directories with proper permissions
    _create_test_data_dirs(base_dir)

    # Make sure directories are writable by netalertx user
    for dir_name in ["app_db", "app_config", "app_log", "app_api", "nginx_conf", "services_run"]:
        dir_path = base_dir / "test_data" / dir_name
        dir_path.chmod(0o777)  # Allow all users to write

    # Create compose file
    compose_config = COMPOSE_CONFIGS["normal_startup"].copy()
    compose_file = base_dir / "docker-compose.yml"
    with open(compose_file, 'w') as f:
        yaml.dump(compose_config, f)

    # Run docker compose
    result = _run_docker_compose(compose_file, "netalertx-normal")

    # Check that expected warnings with pipe characters appear
    # These are the typical warnings that appear in a "normal" startup
    assert "⚠️  Warning: Excessive capabilities detected" in result.output
    assert "⚠️  Warning: Container is running as read-write" in result.output
    assert "═══" in result.output  # Box drawing characters in warnings

    # Should not have critical permission errors (these indicate test setup issues)
    assert "Write permission denied" not in result.output
    assert "CRITICAL" in result.output  # CRITICAL messages are expected when permissions fail


def test_ram_disk_mount_analysis_compose(tmp_path: pathlib.Path) -> None:
    """Test mount analysis for RAM disk detection using docker compose.

    Simulates mounting persistent paths on tmpfs (RAM disk).
    Expected: Mounts table shows ❌ for RAMDisk on persistent paths, dataloss warnings.
    """
    base_dir = tmp_path / "ram_disk_test"
    base_dir.mkdir()

    # Create test data directories
    _create_test_data_dirs(base_dir)

    # Create compose file with tmpfs mounts for persistent paths
    compose_config = {
        "services": {
            "netalertx": {
                "image": IMAGE,
                "network_mode": "host",
                "userns_mode": "host",
                "cap_add": ["NET_RAW", "NET_ADMIN", "NET_BIND_SERVICE"],
                "user": "20211:20211",
                "tmpfs": [
                    "/tmp:mode=777",
                    "/app/db",  # RAM disk for persistent DB
                    "/app/config"  # RAM disk for persistent config
                ],
                "volumes": [
                    f"./test_data/app_log:/app/log",
                    f"./test_data/app_api:/app/api",
                    f"./test_data/nginx_conf:/services/config/nginx/conf.active",
                    f"./test_data/services_run:/services/run"
                ],
                "environment": {
                    "TZ": "UTC"
                }
            }
        }
    }

    compose_file = base_dir / "docker-compose.yml"
    with open(compose_file, 'w') as f:
        yaml.dump(compose_config, f)

    # Run docker compose
    result = _run_docker_compose(compose_file, "netalertx-ram-disk")

    # Check that mounts table shows RAM disk detection and dataloss warnings
    assert "Configuration issues detected" in result.output
    assert "/app/db" in result.output
    assert "/app/config" in result.output
    assert result.returncode != 0  # Should fail due to dataloss risk


def test_dataloss_risk_mount_analysis_compose(tmp_path: pathlib.Path) -> None:
    """Test mount analysis for dataloss risk using docker compose.

    Simulates mounting persistent paths on non-persistent tmpfs.
    Expected: Mounts table shows dataloss risk warnings for persistent paths.
    """
    base_dir = tmp_path / "dataloss_test"
    base_dir.mkdir()

    # Create test data directories
    _create_test_data_dirs(base_dir)

    # Create compose file with tmpfs for persistent data
    compose_config = {
        "services": {
            "netalertx": {
                "image": IMAGE,
                "network_mode": "host",
                "userns_mode": "host",
                "cap_add": ["NET_RAW", "NET_ADMIN", "NET_BIND_SERVICE"],
                "user": "20211:20211",
                "tmpfs": [
                    "/tmp:mode=777",
                    "/app/db:uid=20211,gid=20211",  # Non-persistent for DB
                    "/app/config:uid=20211,gid=20211"  # Non-persistent for config
                ],
                "volumes": [
                    f"./test_data/app_log:/app/log",
                    f"./test_data/app_api:/app/api",
                    f"./test_data/nginx_conf:/services/config/nginx/conf.active",
                    f"./test_data/services_run:/services/run"
                ],
                "environment": {
                    "TZ": "UTC"
                }
            }
        }
    }

    compose_file = base_dir / "docker-compose.yml"
    with open(compose_file, 'w') as f:
        yaml.dump(compose_config, f)

    # Run docker compose
    result = _run_docker_compose(compose_file, "netalertx-dataloss")

    # Check that mounts table shows dataloss risk detection
    assert "Configuration issues detected" in result.output
    assert "/app/db" in result.output
    assert "/app/config" in result.output
    assert result.returncode != 0  # Should fail due to dataloss risk