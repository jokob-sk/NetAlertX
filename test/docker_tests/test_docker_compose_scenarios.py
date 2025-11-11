'''
Docker Compose integration tests for NetAlertX startup scenarios.

This set of tests requires netalertx-test image built and docker compose.
Ensure netalertx-test image is built prior to starting these tests.
'''

import copy
import os
import pathlib
import re
import shutil
import socket
import subprocess
import time
from collections.abc import Callable, Iterable

from _pytest.outcomes import Skipped
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

DEFAULT_HTTP_PORT = int(os.environ.get("NETALERTX_DEFAULT_HTTP_PORT", "20211"))
COMPOSE_PORT_WAIT_TIMEOUT = int(os.environ.get("NETALERTX_COMPOSE_PORT_WAIT_TIMEOUT", "180"))
COMPOSE_SETTLE_WAIT_SECONDS = int(os.environ.get("NETALERTX_COMPOSE_SETTLE_WAIT", "15"))
PREFERRED_CUSTOM_PORTS = (22111, 22112)
HOST_ADDR_ENV = os.environ.get("NETALERTX_HOST_ADDRS", "")


def _discover_host_addresses() -> tuple[str, ...]:
    """Return candidate loopback addresses for reaching host-mode containers."""

    candidates: list[str] = ["127.0.0.1"]

    if HOST_ADDR_ENV:
        env_addrs = [addr.strip() for addr in HOST_ADDR_ENV.split(",") if addr.strip()]
        candidates.extend(env_addrs)

    ip_cmd = shutil.which("ip")
    if ip_cmd:
        try:
            route_proc = subprocess.run(
                [ip_cmd, "-4", "route", "show", "default"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            route_proc = None
        if route_proc and route_proc.returncode == 0 and route_proc.stdout:
            match = re.search(r"default\s+via\s+(?P<gateway>\S+)", route_proc.stdout)
            if match:
                gateway = match.group("gateway")
                candidates.append(gateway)

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for addr in candidates:
        if addr not in seen:
            deduped.append(addr)
            seen.add(addr)

    return tuple(deduped)


HOST_ADDRESS_CANDIDATES = _discover_host_addresses()
LAST_PORT_SUCCESSES: dict[int, str] = {}

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


def _port_is_free(port: int) -> bool:
    """Return True if a TCP port is available on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _wait_for_ports(ports: Iterable[int], timeout: int = COMPOSE_PORT_WAIT_TIMEOUT) -> None:
    """Block until every port in the iterable accepts TCP connections or timeout expires."""

    remaining = set(ports)
    deadline = time.time() + timeout
    last_errors: dict[int, dict[str, BaseException]] = {port: {} for port in remaining}

    while remaining and time.time() < deadline:
        ready: list[int] = []
        for port in list(remaining):
            for addr in HOST_ADDRESS_CANDIDATES:
                try:
                    with socket.create_connection((addr, port), timeout=2):
                        ready.append(port)
                        LAST_PORT_SUCCESSES[port] = addr
                        break
                except OSError as exc:
                    last_errors.setdefault(port, {})[addr] = exc
            else:
                continue
        for port in ready:
            remaining.discard(port)
        if remaining:
            time.sleep(1)

    if remaining:
        details: list[str] = []
        for port in sorted(remaining):
            addr_errors = last_errors.get(port, {})
            if addr_errors:
                error_summary = ", ".join(f"{addr}: {err}" for addr, err in addr_errors.items())
            else:
                error_summary = "no connection attempts recorded"
            details.append(f"{port} -> {error_summary}")
        raise TimeoutError(
            "Ports did not become ready before timeout: " + "; ".join(details)
        )


def _select_custom_ports() -> tuple[int, int]:
    """Choose a pair of non-default ports, preferring the standard high test pair when free."""
    preferred_http, preferred_graphql = PREFERRED_CUSTOM_PORTS
    if _port_is_free(preferred_http) and _port_is_free(preferred_graphql):
        return preferred_http, preferred_graphql

    # Fall back to scanning ephemeral range for the first free consecutive pair.
    for port in range(30000, 60000, 2):
        if _port_is_free(port) and _port_is_free(port + 1):
            return port, port + 1

    raise RuntimeError("Unable to locate two free high ports for compose testing")


def _make_port_check_hook(ports: tuple[int, ...]) -> Callable[[], None]:
    """Return a callback that waits for the provided ports to accept TCP connections."""

    def _hook() -> None:
        for port in ports:
            LAST_PORT_SUCCESSES.pop(port, None)
        time.sleep(COMPOSE_SETTLE_WAIT_SECONDS)
        _wait_for_ports(ports, timeout=COMPOSE_PORT_WAIT_TIMEOUT)

    return _hook


def _write_normal_startup_compose(
    base_dir: pathlib.Path,
    project_name: str,
    env_overrides: dict[str, str] | None,
) -> pathlib.Path:
    """Generate a compose file for the normal startup scenario with optional environment overrides."""

    compose_config = copy.deepcopy(COMPOSE_CONFIGS["normal_startup"])
    service = compose_config["services"]["netalertx"]

    data_volume_name = f"{project_name}_data"
    service["volumes"][0]["source"] = data_volume_name

    if env_overrides:
        service_env = service.setdefault("environment", {})
        service_env.update(env_overrides)

    compose_config["volumes"] = {data_volume_name: {}}

    compose_file = base_dir / "docker-compose.yml"
    with open(compose_file, "w") as f:
        yaml.dump(compose_config, f)

    return compose_file


def _assert_ports_ready(
    result: subprocess.CompletedProcess,
    project_name: str,
    ports: tuple[int, ...],
) -> str:
    """Validate the post-up hook succeeded and return sanitized compose logs for further assertions."""

    post_error = getattr(result, "post_up_error", None)
    clean_output = ANSI_ESCAPE.sub("", result.output)
    port_hosts = {port: LAST_PORT_SUCCESSES.get(port) for port in ports}
    result.port_hosts = port_hosts  # type: ignore[attr-defined]

    if post_error:
        pytest.fail(
            "Port readiness check failed for project"
            f" {project_name} on ports {ports}: {post_error}\n"
            f"Compose logs:\n{clean_output}"
        )

    port_summary = ", ".join(
        f"{port}@{addr if addr else 'unresolved'}" for port, addr in port_hosts.items()
    )
    print(f"[compose port hosts] {project_name}: {port_summary}")

    return clean_output


def _run_docker_compose(
    compose_file: pathlib.Path,
    project_name: str,
    timeout: int = 5,
    env_vars: dict | None = None,
    detached: bool = False,
    post_up: Callable[[], None] | None = None,
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

    post_up_exc: BaseException | None = None
    skip_exc: Skipped | None = None

    try:
        if detached:
            up_result = _run_with_conflict_retry(up_cmd, timeout)

            if post_up:
                try:
                    post_up()
                except Skipped as exc:
                    skip_exc = exc
                except BaseException as exc:  # noqa: BLE001 - bubble the root cause through the result payload
                    post_up_exc = exc

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
    result.post_up_error = post_up_exc  # type: ignore[attr-defined]
    if skip_exc is not None:
        raise skip_exc

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
    default_http_port = DEFAULT_HTTP_PORT
    default_ports = (default_http_port,)
    if not _port_is_free(default_http_port):
        pytest.skip(
            "Default NetAlertX ports are already bound on this host; "
            "skipping compose normal-startup validation."
        )

    default_dir = base_dir / "default"
    default_dir.mkdir()
    default_project = "netalertx-normal-default"

    default_compose_file = _write_normal_startup_compose(default_dir, default_project, None)
    default_result = _run_docker_compose(
        default_compose_file,
        default_project,
        timeout=60,
        detached=True,
        post_up=_make_port_check_hook(default_ports),
    )
    default_output = _assert_ports_ready(default_result, default_project, default_ports)

    assert "Startup pre-checks" in default_output
    assert "❌" not in default_output

    data_line = ""
    data_parts: list[str] = []
    for line in default_output.splitlines():
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
    assert data_parts[1] == CONTAINER_PATHS['data'], f"Unexpected path column in /data row: {data_parts}"
    assert data_parts[2] == "✅" and data_parts[3] == "✅", (
        f"Unexpected mount row values for /data: {data_parts[2:4]}"
    )

    assert "Write permission denied" not in default_output
    assert "CRITICAL" not in default_output
    assert "⚠️" not in default_output

    custom_http, custom_graphql = _select_custom_ports()
    assert custom_http != default_http_port
    custom_ports = (custom_http,)

    custom_dir = base_dir / "custom"
    custom_dir.mkdir()
    custom_project = "netalertx-normal-custom"

    custom_compose_file = _write_normal_startup_compose(
        custom_dir,
        custom_project,
        {
            "PORT": str(custom_http),
            "GRAPHQL_PORT": str(custom_graphql),
        },
    )

    custom_result = _run_docker_compose(
        custom_compose_file,
        custom_project,
        timeout=60,
        detached=True,
        post_up=_make_port_check_hook(custom_ports),
    )
    custom_output = _assert_ports_ready(custom_result, custom_project, custom_ports)

    assert "Startup pre-checks" in custom_output
    assert "❌" not in custom_output
    assert "Write permission denied" not in custom_output
    assert "CRITICAL" not in custom_output
    assert "⚠️" not in custom_output


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
