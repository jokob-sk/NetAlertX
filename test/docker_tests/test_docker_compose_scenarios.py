'''
Docker Compose integration tests for NetAlertX startup scenarios.

This set of tests requires netalertx-test image built and docker compose.
Ensure netalertx-test image is built prior to starting these tests.
'''

import copy
import os
import pathlib
import re
import subprocess
import pytest
import yaml

# Path to test configurations
CONFIG_DIR = pathlib.Path(__file__).parent / "configurations"
ANSI_ESCAPE = re.compile(r"\x1B\[[0-9;]*[A-Za-z]")

pytestmark = [pytest.mark.docker, pytest.mark.compose]

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
                "read_only": True,
                "cap_drop": ["ALL"],
                "cap_add": ["NET_RAW", "NET_ADMIN", "NET_BIND_SERVICE"],
                "user": "20211:20211",
                "tmpfs": [
                    "/app/log:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime",
                    "/app/api:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,sync,noatime,nodiratime",
                    "/services/config/nginx/conf.active:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime",
                    "/services/run:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime",
                    "/tmp:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime",
                ],
                "volumes": [
                    {
                        "type": "volume",
                        "source": "__CONFIG_VOLUME__",
                        "target": "/app/config",
                        "read_only": False,
                    },
                    {
                        "type": "volume",
                        "source": "__DB_VOLUME__",
                        "target": "/app/db",
                        "read_only": False,
                    },
                    {
                        "type": "bind",
                        "source": "/etc/localtime",
                        "target": "/etc/localtime",
                        "read_only": True,
                    },
                ],
                "environment": {
                    "TZ": "UTC"
                }
            }
        }
    }
}
def _create_test_data_dirs(base_dir: pathlib.Path) -> None:
    """Create test data directories and files with write permissions for the container user."""
    dirs = ["app_db", "app_config", "app_log", "app_api", "nginx_conf", "services_run"]
    for dir_name in dirs:
        dir_path = base_dir / "test_data" / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        dir_path.chmod(0o777)

    # Create basic config file
    config_file = base_dir / "test_data" / "app_config" / "app.conf"
    if not config_file.exists():
        config_file.write_text("# Test configuration\n")
    config_file.chmod(0o666)

    # Create basic db file
    db_file = base_dir / "test_data" / "app_db" / "app.db"
    if not db_file.exists():
        # Create a minimal SQLite database
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        conn.close()
    db_file.chmod(0o666)


def _run_docker_compose(
    compose_file: pathlib.Path,
    project_name: str,
    timeout: int = 5,
    env_vars: dict | None = None,
    detached: bool = False,
) -> subprocess.CompletedProcess:
    """Run docker compose up and capture output."""
    cmd = [
        "docker", "compose",
        "-f", str(compose_file),
        "-p", project_name,
    ]

    up_cmd = cmd + ["up"]
    if detached:
        up_cmd.append("-d")
    else:
        up_cmd.extend([
            "--abort-on-container-exit",
            "--timeout", str(timeout)
        ])

    # Merge custom env vars with current environment
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    try:
        if detached:
            up_result = subprocess.run(
                up_cmd,
                cwd=compose_file.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
                env=env,
            )

            logs_cmd = cmd + ["logs"]
            logs_result = subprocess.run(
                logs_cmd,
                cwd=compose_file.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
                env=env,
            )

            result = subprocess.CompletedProcess(
                up_cmd,
                up_result.returncode,
                stdout=(up_result.stdout or "") + (logs_result.stdout or ""),
                stderr=(up_result.stderr or "") + (logs_result.stderr or ""),
            )
        else:
            result = subprocess.run(
                up_cmd,
                cwd=compose_file.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout + 10,
                check=False,
                env=env,
            )
    except subprocess.TimeoutExpired:
        # Clean up on timeout
        subprocess.run(["docker", "compose", "-f", str(compose_file), "-p", project_name, "down", "-v"],
                      cwd=compose_file.parent, check=False, env=env)
        raise

    # Always clean up
    subprocess.run(["docker", "compose", "-f", str(compose_file), "-p", project_name, "down", "-v"],
                  cwd=compose_file.parent, check=False, env=env)

    # Combine stdout and stderr
    result.output = result.stdout + result.stderr

    # Surface command context and IO for any caller to aid debugging
    print("\n[compose command]", " ".join(up_cmd))
    print("[compose cwd]", str(compose_file.parent))
    print("[compose stdin]", "<none>")
    if result.stdout:
        print("[compose stdout]\n" + result.stdout)
    if result.stderr:
        print("[compose stderr]\n" + result.stderr)
    if detached:
        logs_cmd_display = cmd + ["logs"]
        print("[compose logs command]", " ".join(logs_cmd_display))

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

    project_name = "netalertx-normal"

    # Create compose file mirroring production docker-compose.yml
    compose_config = copy.deepcopy(COMPOSE_CONFIGS["normal_startup"])
    service = compose_config["services"]["netalertx"]

    config_volume_name = f"{project_name}_config"
    db_volume_name = f"{project_name}_db"

    service["volumes"][0]["source"] = config_volume_name
    service["volumes"][1]["source"] = db_volume_name

    service.setdefault("environment", {})
    service["environment"].update({
        "PORT": "22111",
        "GRAPHQL_PORT": "22112",
    })

    compose_config["volumes"] = {
        config_volume_name: {},
        db_volume_name: {},
    }

    compose_file = base_dir / "docker-compose.yml"
    with open(compose_file, 'w') as f:
        yaml.dump(compose_config, f)

    # Run docker compose
    result = _run_docker_compose(compose_file, project_name, detached=True)

    clean_output = ANSI_ESCAPE.sub("", result.output)

    # Check that startup completed without critical issues and mounts table shows success
    assert "Startup pre-checks" in clean_output
    assert "❌" not in clean_output
    assert "/app/db                            |     ✅" in clean_output

    # Ensure no critical errors or permission problems surfaced
    assert "Write permission denied" not in clean_output
    assert "CRITICAL" not in clean_output
    assert "⚠️" not in clean_output


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