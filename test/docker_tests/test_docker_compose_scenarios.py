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

CONTAINER_PATHS = {
    "data": "/data",
    "db": "/data/db",
    "config": "/data/config",
    "log": "/tmp/log",
    "api": os.environ.get("NETALERTX_API", "/tmp/api"),
    "run": "/tmp/run",
    "nginx_active": "/tmp/nginx/active-config",
}

TMPFS_ROOT = "/tmp:uid=20211,gid=20211,mode=1700,rw,noexec,nosuid,nodev,async,noatime,nodiratime"

pytestmark = [pytest.mark.docker, pytest.mark.compose]

IMAGE = os.environ.get("NETALERTX_TEST_IMAGE", "netalertx-test")

_CONFLICT_NAME_PATTERN = re.compile(r'The container name "/([^"]+)" is already in use')

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
                    f"./test_data/data:{CONTAINER_PATHS['data']}",
                    f"./test_data/log:{CONTAINER_PATHS['log']}",
                    f"./test_data/api:{CONTAINER_PATHS['api']}",
                    f"./test_data/nginx_conf:{CONTAINER_PATHS['nginx_active']}",
                    f"./test_data/run:{CONTAINER_PATHS['run']}"
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
                    f"./test_data/data:{CONTAINER_PATHS['data']}",
                    f"./test_data/log:{CONTAINER_PATHS['log']}",
                    f"./test_data/api:{CONTAINER_PATHS['api']}",
                    f"./test_data/nginx_conf:{CONTAINER_PATHS['nginx_active']}",
                    f"./test_data/run:{CONTAINER_PATHS['run']}"
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
                "tmpfs": [TMPFS_ROOT],
                "volumes": [
                    {
                        "type": "volume",
                        "source": "__DATA_VOLUME__",
                        "target": CONTAINER_PATHS["data"],
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
    dirs = [
        "data/db",
        "data/config",
        "log",
        "api",
        "nginx_conf",
        "run",
    ]
    for dir_name in dirs:
        dir_path = base_dir / "test_data" / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        dir_path.chmod(0o777)

    # Create basic config file
    config_file = base_dir / "test_data" / "data" / "config" / "app.conf"
    if not config_file.exists():
        config_file.write_text("# Test configuration\n")
    config_file.chmod(0o666)

    # Create basic db file
    db_file = base_dir / "test_data" / "data" / "db" / "app.db"
    if not db_file.exists():
        # Create a minimal SQLite database
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        conn.close()
    db_file.chmod(0o666)


def _extract_conflict_container_name(output: str) -> str | None:
    match = _CONFLICT_NAME_PATTERN.search(output)
    if match:
        return match.group(1)
    return None


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

    # Ensure no stale containers from previous runs; always clean before starting.
    subprocess.run(
        cmd + ["down", "-v"],
        cwd=compose_file.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        env=env,
    )

    def _run_with_conflict_retry(run_cmd: list[str], run_timeout: int) -> subprocess.CompletedProcess:
        retry_conflict = True
        while True:
            proc = subprocess.run(
                run_cmd,
                cwd=compose_file.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=run_timeout,
                check=False,
                env=env,
            )
            combined = (proc.stdout or "") + (proc.stderr or "")
            if retry_conflict and "is already in use by container" in combined:
                conflict_name = _extract_conflict_container_name(combined)
                if conflict_name:
                    subprocess.run(
                        ["docker", "rm", "-f", conflict_name],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                        env=env,
                    )
                    retry_conflict = False
                    continue
            return proc

    try:
        if detached:
            up_result = _run_with_conflict_retry(up_cmd, timeout)

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
            result = _run_with_conflict_retry(up_cmd, timeout + 10)
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

    # Keep verbose output for human debugging. Future automation must not remove this print; use
    # the failedTest tool to trim context instead of stripping logs.
    print("\n[compose output]", result.output)

    # Check for nginx config write failure warning
    assert f"Unable to write to {CONTAINER_PATHS['nginx_active']}/netalertx.conf" in result.output
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

    data_volume_name = f"{project_name}_data"

    service["volumes"][0]["source"] = data_volume_name

    service.setdefault("environment", {})
    service["environment"].update({
        "PORT": "22111",
        "GRAPHQL_PORT": "22112",
    })

    compose_config["volumes"] = {
        data_volume_name: {},
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

    data_line = ""
    data_parts: list[str] = []
    for line in clean_output.splitlines():
        if CONTAINER_PATHS['data'] not in line or '|' not in line:
            continue
        parts = [segment.strip() for segment in line.split('|')]
        if len(parts) < 2:
            continue
        if parts[1] == CONTAINER_PATHS['data']:
            data_line = line
            data_parts = parts
            break

    assert data_line, "Expected /data row in mounts table"

    parts = data_parts
    assert parts[1] == CONTAINER_PATHS['data'], f"Unexpected path column in /data row: {parts}"
    assert parts[2] == "✅" and parts[3] == "✅", f"Unexpected mount row values for /data: {parts[2:4]}"

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
                    CONTAINER_PATHS["data"],  # RAM disk for persistent data root
                ],
                "volumes": [
                    f"./test_data/log:{CONTAINER_PATHS['log']}",
                    f"./test_data/api:{CONTAINER_PATHS['api']}",
                    f"./test_data/nginx_conf:{CONTAINER_PATHS['nginx_active']}",
                    f"./test_data/run:{CONTAINER_PATHS['run']}"
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
    assert CONTAINER_PATHS["data"] in result.output
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
                    f"{CONTAINER_PATHS['data']}:uid=20211,gid=20211",  # Non-persistent for unified data
                ],
                "volumes": [
                    f"./test_data/log:{CONTAINER_PATHS['log']}",
                    f"./test_data/api:{CONTAINER_PATHS['api']}",
                    f"./test_data/nginx_conf:{CONTAINER_PATHS['nginx_active']}",
                    f"./test_data/run:{CONTAINER_PATHS['run']}"
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
    assert CONTAINER_PATHS["data"] in result.output
    assert result.returncode != 0  # Should fail due to dataloss risk
