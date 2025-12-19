"""
This set of tests requires netalertx-test image built. Ensure netalertx-test image is built prior
to starting these tests or they will fail.  netalertx-test image is generally rebuilt using the
Build Unit Test Docker Image task. but can be created manually with the following command executed
in the workspace:
docker buildx build -t netalertx-test .
"""

import os
import pathlib
import shutil
import subprocess
import uuid
import re
import pytest

IMAGE = os.environ.get("NETALERTX_TEST_IMAGE", "netalertx-test")
GRACE_SECONDS = float(os.environ.get("NETALERTX_TEST_GRACE", "2"))
DEFAULT_CAPS = ["NET_RAW", "NET_ADMIN", "NET_BIND_SERVICE"]

CONTAINER_TARGETS: dict[str, str] = {
    "data": "/data",
    "app_db": "/data/db",
    "data_db": "/data/db",
    "app_config": "/data/config",
    "data_config": "/data/config",
    "app_log": "/tmp/log",
    "log": "/tmp/log",
    "app_api": os.environ.get("NETALERTX_API", "/tmp/api"),
    "api": os.environ.get("NETALERTX_API", "/tmp/api"),
    "nginx_conf": "/tmp/nginx/active-config",
    "nginx_active": "/tmp/nginx/active-config",
    "services_run": "/tmp/run",
}

DATA_SUBDIR_KEYS = ("app_db", "app_config")
OPTIONAL_TMP_KEYS = ("app_log", "app_api", "nginx_conf", "services_run")

VOLUME_MAP = CONTAINER_TARGETS

pytestmark = [pytest.mark.docker, pytest.mark.feature_complete]


def _unique_label(prefix: str) -> str:
    return f"{prefix.upper()}__NETALERTX_INTENTIONAL__{uuid.uuid4().hex[:6]}"


def _create_docker_volume(prefix: str) -> str:
    name = f"netalertx-test-{prefix}-{uuid.uuid4().hex[:8]}".lower()
    subprocess.run(
        ["docker", "volume", "create", name],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return name


def _remove_docker_volume(name: str) -> None:
    subprocess.run(
        [
            "docker",
            "volume",
            "rm",
            "-f",
            name,
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _seed_config_volume() -> str:
    name = _create_docker_volume("config")
    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        "0:0",
        "--entrypoint",
        "/bin/sh",
        "-v",
        f"{name}:/data",
        IMAGE,
        "-c",
        "install -d /data && install -m 600 /app/back/app.conf /data/app.conf && chown 20211:20211 /data/app.conf",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        _remove_docker_volume(name)
        raise
    return name


def _seed_data_volume() -> str:
    name = _create_docker_volume("data")
    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        "0:0",
        "--entrypoint",
        "/bin/sh",
        "-v",
        f"{name}:/data",
        IMAGE,
        "-c",
        "install -d /data/db /data/config && chown -R 20211:20211 /data",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        _remove_docker_volume(name)
        raise
    return name


def _chown_path(host_path: pathlib.Path, uid: int, gid: int) -> None:
    """Chown a host path using the test image with host user namespace."""
    if not host_path.exists():
        raise RuntimeError(f"Cannot chown missing path {host_path}")

    cmd = [
        "docker",
        "run",
        "--rm",
        "--userns",
        "host",
        "--user",
        "0:0",
        "--entrypoint",
        "/bin/chown",
        "-v",
        f"{host_path}:/mnt",
        IMAGE,
        "-R",
        f"{uid}:{gid}",
        "/mnt",
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to chown {host_path} to {uid}:{gid}") from exc


def _setup_mount_tree(
    tmp_path: pathlib.Path,
    prefix: str,
    seed_config: bool = True,
    seed_db: bool = True,
) -> dict[str, pathlib.Path]:
    label = _unique_label(prefix)
    base = tmp_path / f"{label}_MOUNT_ROOT"
    base.mkdir()
    paths: dict[str, pathlib.Path] = {}

    # Create unified /data mount root
    data_root = base / f"{label}_DATA_INTENTIONAL_NETALERTX_TEST"
    data_root.mkdir(parents=True, exist_ok=True)
    data_root.chmod(0o777)
    paths["data"] = data_root

    # Create required data subdirectories and aliases
    db_dir = data_root / "db"
    db_dir.mkdir(exist_ok=True)
    db_dir.chmod(0o777)
    paths["app_db"] = db_dir
    paths["data_db"] = db_dir

    config_dir = data_root / "config"
    config_dir.mkdir(exist_ok=True)
    config_dir.chmod(0o777)
    paths["app_config"] = config_dir
    paths["data_config"] = config_dir

    # Optional /tmp mounts that certain tests intentionally bind
    for key in OPTIONAL_TMP_KEYS:
        folder_name = f"{label}_{key.upper()}_INTENTIONAL_NETALERTX_TEST"
        host_path = base / folder_name
        host_path.mkdir(parents=True, exist_ok=True)
        try:
            host_path.chmod(0o777)
        except PermissionError:
            pass
        paths[key] = host_path
        # Provide backwards-compatible aliases where helpful
        if key == "app_log":
            paths["log"] = host_path
        elif key == "app_api":
            paths["api"] = host_path
        elif key == "nginx_conf":
            paths["nginx_active"] = host_path

    # Determine repo root from env or by walking up from this file
    repo_root_env = os.environ.get("NETALERTX_REPO_ROOT")
    if repo_root_env:
        repo_root = pathlib.Path(repo_root_env)
    else:
        repo_root = None
        cur = pathlib.Path(__file__).resolve()
        for parent in cur.parents:
            if any([
                (parent / "pyproject.toml").exists(),
                (parent / ".git").exists(),
                (parent / "back").exists() and (parent / "db").exists()
            ]):
                repo_root = parent
                break
        if repo_root is None:
            repo_root = cur.parents[2]

    if seed_config:
        config_file = paths["app_config"] / "app.conf"
        config_src = repo_root / "back" / "app.conf"
        if not config_src.exists():
            print(
                f"[WARN] Seed file not found: {config_src}. Set NETALERTX_REPO_ROOT or run from repo root. Skipping copy."
            )
        else:
            shutil.copyfile(config_src, config_file)
            config_file.chmod(0o600)
    if seed_db:
        db_file = paths["app_db"] / "app.db"
        db_src = repo_root / "db" / "app.db"
        if not db_src.exists():
            print(
                f"[WARN] Seed file not found: {db_src}. Set NETALERTX_REPO_ROOT or run from repo root. Skipping copy."
            )
        else:
            shutil.copyfile(db_src, db_file)
            db_file.chmod(0o600)

    _chown_netalertx(base)

    return paths


def _setup_fixed_mount_tree(base: pathlib.Path) -> dict[str, pathlib.Path]:
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)

    paths: dict[str, pathlib.Path] = {}

    data_root = base / "DATA_NETALERTX_TEST"
    data_root.mkdir(parents=True, exist_ok=True)
    data_root.chmod(0o777)
    paths["data"] = data_root

    db_dir = data_root / "db"
    db_dir.mkdir(exist_ok=True)
    db_dir.chmod(0o777)
    paths["app_db"] = db_dir
    paths["data_db"] = db_dir

    config_dir = data_root / "config"
    config_dir.mkdir(exist_ok=True)
    config_dir.chmod(0o777)
    paths["app_config"] = config_dir
    paths["data_config"] = config_dir

    for key in OPTIONAL_TMP_KEYS:
        host_path = base / f"{key.upper()}_NETALERTX_TEST"
        host_path.mkdir(parents=True, exist_ok=True)
        host_path.chmod(0o777)
        paths[key] = host_path
        if key == "app_log":
            paths["log"] = host_path
        elif key == "app_api":
            paths["api"] = host_path
        elif key == "nginx_conf":
            paths["nginx_active"] = host_path
    return paths


def _build_volume_args(
    paths: dict[str, pathlib.Path],
) -> list[tuple[str, str, bool]]:
    return _build_volume_args_for_keys(paths, {"data"})


def _build_volume_args_for_keys(
    paths: dict[str, pathlib.Path],
    keys: set[str],
    read_only: set[str] | None = None,
) -> list[tuple[str, str, bool]]:
    bindings: list[tuple[str, str, bool]] = []
    read_only = read_only or set()
    for key in keys:
        if key not in CONTAINER_TARGETS:
            raise KeyError(f"Unknown mount key {key}")
        target = CONTAINER_TARGETS[key]
        if key not in paths:
            raise KeyError(f"Missing host path for key {key}")
        bindings.append((str(paths[key]), target, key in read_only))
    return bindings


def _chown_root(host_path: pathlib.Path) -> None:
    _chown_path(host_path, 0, 0)


def _chown_netalertx(host_path: pathlib.Path) -> None:
    _chown_path(host_path, 20211, 20211)


def _run_container(
    label: str,
    volumes: list[tuple[str, str, bool]] | None = None,
    *,
    env: dict[str, str] | None = None,
    user: str | None = None,
    drop_caps: list[str] | None = None,
    network_mode: str | None = "host",
    extra_args: list[str] | None = None,
    volume_specs: list[str] | None = None,
    sleep_seconds: float = GRACE_SECONDS,
    wait_for_exit: bool = False,
    pre_entrypoint: str | None = None,
) -> subprocess.CompletedProcess[str]:
    name = f"netalertx-test-{label}-{uuid.uuid4().hex[:8]}".lower()

    # Clean up any existing container with this name
    subprocess.run(
        ["docker", "rm", "-f", name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cmd: list[str] = ["docker", "run", "--rm", "--name", name]

    if network_mode:
        cmd.extend(["--network", network_mode])
    cmd.extend(["--userns", "host"])
    # Add default ramdisk to /tmp with permissions 777
    cmd.extend(["--tmpfs", "/tmp:mode=777"])
    if user:
        cmd.extend(["--user", user])
    if drop_caps:
        for cap in drop_caps:
            cmd.extend(["--cap-drop", cap])
    else:
        for cap in DEFAULT_CAPS:
            cmd.extend(["--cap-add", cap])
    if env:
        for key, value in env.items():
            cmd.extend(["-e", f"{key}={value}"])
    if extra_args:
        cmd.extend(extra_args)
    for host_path, target, readonly in volumes or []:
        mount = f"{host_path}:{target}"
        if readonly:
            mount += ":ro"
        cmd.extend(["-v", mount])
    if volume_specs:
        for spec in volume_specs:
            cmd.extend(["-v", spec])

    # Diagnostic wrapper: list ownership and perms of mounted targets inside
    # the container before running the real entrypoint. This helps debug
    # permission failures by capturing the container's view of the host mounts.
    mounts_ls = """
    echo "--- MOUNT PERMS (container view) ---";
    ls -ldn \
    """
    for _, target, _ in volumes or []:
        mounts_ls += f" {target}"
    mounts_ls += " || true; echo '--- END MOUNTS ---'; \n"

    setup_script = ""
    if pre_entrypoint:
        setup_script = pre_entrypoint
        if not setup_script.endswith("\n"):
            setup_script += "\n"

    if wait_for_exit:
        script = mounts_ls + setup_script + "sh /entrypoint.sh"
    else:
        script = "".join([
            mounts_ls,
            setup_script,
            "sh /entrypoint.sh & pid=$!; ",
            f"sleep {sleep_seconds}; ",
            "if kill -0 $pid >/dev/null 2>&1; then kill -TERM $pid >/dev/null 2>&1 || true; fi; ",
            "wait $pid; code=$?; if [ $code -eq 143 ]; then exit 0; fi; exit $code"
        ])
    cmd.extend(["--entrypoint", "/bin/sh", IMAGE, "-c", script])

    # Print the full Docker command for debugging
    print("\n--- DOCKER CMD ---\n", " ".join(cmd), "\n--- END CMD ---\n")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=sleep_seconds + 30,
        check=False,
    )
    # Combine and clean stdout and stderr
    stdouterr = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout or "") + re.sub(
        r"\x1b\[[0-9;]*m", "", result.stderr or ""
    )
    result.output = stdouterr
    # Print container output for debugging in every test run.
    print("\n--- CONTAINER OUTPUT START ---")
    print(result.output)
    print("--- CONTAINER OUTPUT END ---\n")

    return result


def _assert_contains(result, snippet: str, cmd: list[str] = None) -> None:
    output = result.output + result.stderr
    if snippet not in output:
        cmd_str = " ".join(cmd) if cmd else ""
        raise AssertionError(
            f"Expected to find '{snippet}' in container output.\n"
            f"STDOUT:\n{result.output}\n"
            f"STDERR:\n{result.stderr}\n"
            f"Combined output:\n{output}\n"
            f"Container command:\n{cmd_str}"
        )


def _extract_mount_rows(output: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    in_table = False
    for raw_line in (output or "").splitlines():
        line = raw_line.rstrip()
        if not in_table:
            if line.startswith(" Path") and "Writeable" in line:
                in_table = True
            continue
        if not line.strip():
            break
        if line.lstrip().startswith("Path"):
            continue
        if set(line.strip()) <= {"-", "+"}:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 6:
            continue
        path = parts[0].strip()
        rows[path] = parts[1:6]
    return rows


def _assert_mount_row(
    result,
    path: str,
    *,
    write: str | None = None,
    mount: str | None = None,
    ramdisk: str | None = None,
    performance: str | None = None,
    dataloss: str | None = None,
) -> None:
    rows = _extract_mount_rows(result.output)
    if path not in rows:
        raise AssertionError(
            f"Mount table row for {path} not found. Rows: {sorted(rows)}\nOutput:\n{result.output}"
        )
    columns = rows[path]
    labels = ["Writeable", "Mount", "RAMDisk", "Performance", "DataLoss"]
    expectations = [write, mount, ramdisk, performance, dataloss]
    for idx, expected in enumerate(expectations):
        if expected is None:
            continue
        actual = columns[idx]
        if actual != expected:
            raise AssertionError(
                f"{path} {labels[idx]} expected {expected}, got {actual}.\n"
                f"Rows: {rows}\nOutput:\n{result.output}"
            )


def _setup_zero_perm_dir(paths: dict[str, pathlib.Path], key: str) -> None:
    """Set up a directory with files and zero permissions for testing."""
    if key in ["app_db", "app_config"]:
        # Files already exist from _setup_mount_tree seeding
        pass
    else:
        # Create a dummy file for other directories
        (paths[key] / "dummy.txt").write_text("dummy")

    # Chmod all files in the directory to 000
    for f in paths[key].iterdir():
        f.chmod(0)

    # Chmod the directory itself to 000
    paths[key].chmod(0)


def _restore_zero_perm_dir(paths: dict[str, pathlib.Path], key: str) -> None:
    """Restore permissions after zero perm test."""
    # Chmod directory back to 700
    paths[key].chmod(0o700)

    # Chmod files back to appropriate permissions
    for f in paths[key].iterdir():
        if f.name in ["app.db", "app.conf"]:
            f.chmod(0o600)
        else:
            f.chmod(0o644)


def test_missing_capabilities_triggers_warning(tmp_path: pathlib.Path) -> None:
    """Test missing required capabilities - simulates insufficient container privileges.

    5. Missing Required Capabilities: Simulates running without NET_ADMIN, NET_RAW,
    NET_BIND_SERVICE capabilities. Required for ARP scanning and network operations.
    Expected: "exec /bin/sh: operation not permitted" error, guidance to add capabilities.

    Check script: N/A (capability check happens at container runtime)
    Sample message: "exec /bin/sh: operation not permitted"
    """
    paths = _setup_mount_tree(tmp_path, "missing_caps")
    volumes = _build_volume_args_for_keys(paths, {"data"})
    result = _run_container(
        "missing-caps",
        volumes,
        drop_caps=["ALL"],
    )
    _assert_contains(result, "exec /bin/sh: operation not permitted", result.args)
    assert result.returncode != 0


def test_running_as_root_is_blocked(tmp_path: pathlib.Path) -> None:
    """Test running as root user - simulates insecure container execution.

    6. Running as Root User: Simulates running container as root (UID 0) instead of
    dedicated netalertx user. Warning about security risks, special permission fix mode.
    Expected: Warning about security risks, guidance to use UID 20211.

    Check script: /entrypoint.d/0-storage-permission.sh
    Sample message: "🚨 CRITICAL SECURITY ALERT: NetAlertX is running as ROOT (UID 0)!"
    """
    paths = _setup_mount_tree(tmp_path, "run_as_root")
    volumes = _build_volume_args_for_keys(paths, {"data", "nginx_conf"})
    result = _run_container(
        "run-as-root",
        volumes,
        user="0",
    )
    _assert_contains(result, "NetAlertX is running as ROOT", result.args)
    _assert_contains(result, "Permissions fixed for read-write paths.", result.args)
    assert (
        result.returncode == 0
    )  # container warns but continues running, then terminated by test framework


def test_missing_host_network_warns(tmp_path: pathlib.Path) -> None:
    # No output assertion, just returncode check
    """Test missing host networking - simulates running without host network mode.

    8. Missing Host Networking: Simulates running without network_mode: host.
    Limits ARP scanning capabilities for network discovery.
    Expected: Warning about ARP scanning limitations, guidance to use host networking.

    Check script: check-network-mode.sh
    Sample message: "⚠️  ATTENTION: NetAlertX is not running with --network=host. Bridge networking..."
    """
    data_volume = _seed_data_volume()
    config_volume = _seed_config_volume()
    result = None
    try:
        result = _run_container(
            "missing-host-network",
            None,
            network_mode=None,
            volume_specs=[
                f"{data_volume}:{VOLUME_MAP['data']}",
                f"{config_volume}:{VOLUME_MAP['app_config']}",
            ],
            sleep_seconds=5,
        )
    finally:
        _remove_docker_volume(config_volume)
        _remove_docker_volume(data_volume)
    assert result is not None
    _assert_contains(result, "not running with --network=host", result.args)


# NOTE: The following runtime-behavior tests depended on the entrypoint continuing even when
# /data was mounted without write permissions. With fail-fast enabled we must supply a pre-owned
# (UID/GID 20211) data volume, which this dev container cannot provide for bind mounts. Once the
# docker tests switch to compose-managed fixtures, restore these cases by moving them back to the
# top level.



def test_missing_app_conf_triggers_seed(tmp_path: pathlib.Path) -> None:
    """Test missing configuration file seeding - simulates corrupted/missing app.conf.

    9. Missing Configuration File: Simulates corrupted/missing app.conf.
    Container automatically regenerates default configuration on startup.
    Expected: Automatic regeneration of default configuration.

    Check script: /entrypoint.d/15-first-run-config.sh
    Sample message: "Default configuration written to"
    """
    base = tmp_path / "missing_app_conf_base"
    paths = _setup_fixed_mount_tree(base)
    for key in ["data", "app_db", "app_config"]:
        paths[key].chmod(0o777)
        _chown_netalertx(paths[key])
    (paths["app_config"] / "testfile.txt").write_text("test")
    volumes = _build_volume_args_for_keys(paths, {"data"})
    result = _run_container("missing-app-conf", volumes, sleep_seconds=5)
    _assert_contains(result, "Default configuration written to", result.args)
    assert result.returncode == 0


def test_missing_app_db_triggers_seed(tmp_path: pathlib.Path) -> None:
    """Test missing database file seeding - simulates corrupted/missing app.db.

    10. Missing Database File: Simulates corrupted/missing app.db.
    Container automatically creates initial database schema on startup.
    Expected: Automatic creation of initial database schema.

    Check script: /entrypoint.d/20-first-run-db.sh
    Sample message: "Building initial database schema"
    """
    data_volume = _seed_data_volume()
    config_volume = _seed_config_volume()
    # Prepare a minimal writable config that still contains TIMEZONE for plugin_helper
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "/bin/sh",
            "-v",
            f"{config_volume}:/data",
            IMAGE,
            "-c",
            "printf \"TIMEZONE='UTC'\\n\" >/data/app.conf && chown 20211:20211 /data/app.conf",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    result = None
    db_file_check = None
    try:
        result = _run_container(
            "missing-app-db",
            None,
            user="20211:20211",
            sleep_seconds=5,
            wait_for_exit=True,
            volume_specs=[
                f"{data_volume}:{VOLUME_MAP['data']}",
                f"{config_volume}:{VOLUME_MAP['app_config']}",
            ],
        )
    finally:
        db_file_check = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{data_volume}:/data",
                IMAGE,
                "/bin/sh",
                "-c",
                "test -f /data/db/app.db",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _remove_docker_volume(config_volume)
        _remove_docker_volume(data_volume)
    assert db_file_check is not None and db_file_check.returncode == 0
    assert result is not None
    assert result.returncode != 0


def test_custom_port_without_writable_conf(tmp_path: pathlib.Path) -> None:
    """Test custom port configuration without writable nginx config mount.

    4. Custom Port Without Nginx Config Mount: Simulates setting custom LISTEN_ADDR/PORT
    without mounting nginx config. Container starts but uses default address.
    Expected: Container starts but uses default address, warning about missing config mount.

    Check script: check-nginx-config.sh
    Sample messages: "⚠️  ATTENTION: Nginx configuration mount /tmp/nginx/active-config is missing."
                        "⚠️  ATTENTION: Unable to write to /tmp/nginx/active-config/netalertx.conf."
    """
    data_volume = _seed_data_volume()
    config_volume = _seed_config_volume()
    paths = _setup_mount_tree(tmp_path, "custom_port_ro_conf")
    for key in ["data", "app_db", "app_config", "app_log", "app_api", "services_run"]:
        paths[key].chmod(0o777)
        _chown_netalertx(paths[key])
    volumes = _build_volume_args_for_keys(
        paths,
        {"app_log", "app_api", "services_run"},
    )
    extra_args = [
        "--tmpfs",
        f"{VOLUME_MAP['nginx_conf']}:uid=20211,gid=20211,mode=500",
    ]
    try:
        result = _run_container(
            "custom-port-ro-conf",
            volumes,
            env={"PORT": "24444", "LISTEN_ADDR": "127.0.0.1"},
            user="20211:20211",
            extra_args=extra_args,
            volume_specs=[
                f"{data_volume}:{VOLUME_MAP['data']}",
                f"{config_volume}:{VOLUME_MAP['app_config']}",
            ],
            sleep_seconds=5,
        )
        _assert_contains(result, "Unable to write to", result.args)
        _assert_contains(
            result, f"{VOLUME_MAP['nginx_conf']}/netalertx.conf", result.args
        )
        assert result.returncode != 0
    finally:
        _remove_docker_volume(config_volume)
        _remove_docker_volume(data_volume)

def test_excessive_capabilities_warning(tmp_path: pathlib.Path) -> None:
    """Test excessive capabilities detection - simulates container with extra capabilities.

    11. Excessive Capabilities: Simulates container with capabilities beyond the required
    NET_ADMIN, NET_RAW, and NET_BIND_SERVICE.
    Expected: Warning about excessive capabilities detected.

    Check script: 90-excessive-capabilities.sh
    Sample message: "Excessive capabilities detected"
    """
    data_volume = _seed_data_volume()
    config_volume = _seed_config_volume()
    try:
        result = _run_container(
            "excessive-caps",
            None,
            extra_args=["--cap-add=SYS_ADMIN", "--cap-add=NET_BROADCAST"],
            sleep_seconds=5,
            volume_specs=[
                f"{data_volume}:{VOLUME_MAP['data']}",
                f"{config_volume}:{VOLUME_MAP['app_config']}",
            ],
        )
        _assert_contains(result, "Excessive capabilities detected", result.args)
        _assert_contains(result, "bounding caps:", result.args)
    finally:
        _remove_docker_volume(config_volume)
        _remove_docker_volume(data_volume)

def test_appliance_integrity_read_write_mode(tmp_path: pathlib.Path) -> None:
    """Test appliance integrity - simulates running with read-write root filesystem.

    12. Appliance Integrity: Simulates running container with read-write root filesystem
    instead of read-only mode.
    Expected: Warning about running in read-write mode instead of read-only.

    Check script: 95-appliance-integrity.sh
    Sample message: "Container is running as read-write, not in read-only mode"
    """
    data_volume = _seed_data_volume()
    config_volume = _seed_config_volume()
    try:
        result = _run_container(
            "appliance-integrity",
            None,
            sleep_seconds=5,
            volume_specs=[
                f"{data_volume}:{VOLUME_MAP['data']}",
                f"{config_volume}:{VOLUME_MAP['app_config']}",
            ],
        )
    finally:
        _remove_docker_volume(config_volume)
        _remove_docker_volume(data_volume)
    _assert_contains(
        result, "Container is running as read-write, not in read-only mode", result.args
    )


def test_zero_permissions_app_db_dir(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: Mounts table shows ❌ for writeable status, configuration issues detected.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_app_db")
    _setup_zero_perm_dir(paths, "app_db")
    volumes = _build_volume_args_for_keys(paths, {"data"})
    try:
        result = _run_container(
            "chmod-app-db",
            volumes,
            user="20211:20211",
            wait_for_exit=True,
        )
        # Check that the mounts table shows the app_db directory as not writeable
        _assert_mount_row(result, VOLUME_MAP["app_db"], write="❌")
        # Check that configuration issues are detected
        _assert_contains(result, "Configuration issues detected", result.args)
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "app_db")


def test_zero_permissions_app_config_dir(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: Mounts table shows ❌ for writeable status, configuration issues detected.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_app_config")
    _setup_zero_perm_dir(paths, "app_config")
    volumes = _build_volume_args_for_keys(paths, {"data"})
    try:
        result = _run_container(
            "chmod-app-config",
            volumes,
            user="20211:20211",
            wait_for_exit=True,
        )
        # Check that the mounts table shows the app_config directory as not writeable
        _assert_mount_row(result, VOLUME_MAP["app_config"], write="❌")
        # Check that configuration issues are detected
        _assert_contains(result, "Configuration issues detected", result.args)
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "app_config")


def test_mandatory_folders_creation(tmp_path: pathlib.Path) -> None:
    """Test mandatory folders creation - simulates missing plugins log directory.

    1. Mandatory Folders: Simulates missing required directories and log files.
    Container automatically creates plugins log, system services run log/tmp directories,
    and required log files on startup.
    Expected: Automatic creation of all required directories and files.

    Check script: 25-mandatory-folders.sh
    Sample message: "Creating Plugins log"
    """
    paths = _setup_mount_tree(tmp_path, "mandatory_folders")
    # Remove the plugins log directory to simulate missing mandatory folder
    plugins_log_dir = paths["app_log"] / "plugins"
    if plugins_log_dir.exists():
        shutil.rmtree(plugins_log_dir)

    # Ensure other directories are writable and owned by netalertx user so container gets past mounts.py
    for key in [
        "app_db",
        "app_config",
        "app_log",
        "app_api",
        "services_run",
        "nginx_conf",
    ]:
        paths[key].chmod(0o777)
        _chown_netalertx(paths[key])  # Ensure all directories are owned by netalertx

    volumes = _build_volume_args_for_keys(paths, {"data"})
    result = _run_container(
        "mandatory-folders", volumes, user="20211:20211", sleep_seconds=5
    )
    _assert_contains(result, "Creating Plugins log", result.args)
    # The container will fail at writable config due to permission issues, but we just want to verify
    # that mandatory folders creation ran successfully


def test_writable_config_validation(tmp_path: pathlib.Path) -> None:
    """Test writable config validation - simulates read-only config file.

    3. Writable Config Validation: Simulates config file with read-only permissions.
    Container verifies it can read from and write to critical config and database files.
    Expected: "Read permission denied" warning for config file.

    Check script: 30-writable-config.sh
    Sample message: "Read permission denied"
    """
    paths = _setup_mount_tree(tmp_path, "writable_config")
    # Make config file unreadable/unwritable to the container user to force the check
    config_file = paths["app_config"] / "app.conf"
    _chown_root(config_file)
    config_file.chmod(0o000)

    # Ensure directories are writable and owned by netalertx user so container gets past mounts.py
    for key in [
        "app_db",
        "app_config",
        "app_log",
        "app_api",
        "services_run",
        "nginx_conf",
    ]:
        paths[key].chmod(0o777)
        _chown_netalertx(paths[key])

    volumes = _build_volume_args_for_keys(paths, {"data"})
    result = _run_container(
        "writable-config", volumes, user="20211:20211", sleep_seconds=5.0
    )
    _assert_contains(result, "Read permission denied", result.args)


def test_mount_analysis_ram_disk_performance(tmp_path: pathlib.Path) -> None:
    """Test mount analysis for RAM disk performance issues.

    Tests 10-mounts.py detection of persistent paths on RAM disks (tmpfs) which can cause
    performance issues and data loss on container restart.
    Expected: Mounts table shows ❌ for RAMDisk on persistent paths, performance warnings.

    Check script: 10-mounts.py
    Sample message: "Configuration issues detected"
    """
    paths = _setup_mount_tree(tmp_path, "ram_disk_mount")
    # Mount persistent paths (db, config) on tmpfs to simulate RAM disk
    volumes = [
        (str(paths["app_log"]), VOLUME_MAP["app_log"], False),
        (str(paths["app_api"]), VOLUME_MAP["app_api"], False),
        (str(paths["services_run"]), VOLUME_MAP["services_run"], False),
        (str(paths["nginx_conf"]), VOLUME_MAP["nginx_conf"], False),
    ]
    # Use tmpfs mounts for persistent paths with proper permissions
    extra_args = [
        "--tmpfs",
        f"{VOLUME_MAP['app_db']}:uid=20211,gid=20211,mode=755",
        "--tmpfs",
        f"{VOLUME_MAP['app_config']}:uid=20211,gid=20211,mode=755",
    ]
    result = _run_container(
        "ram-disk-mount", volumes=volumes, extra_args=extra_args, user="20211:20211"
    )
    # Check that mounts table shows RAM disk detection for persistent paths
    _assert_mount_row(
        result,
        VOLUME_MAP["app_db"],
        write="✅",
        mount="✅",
        ramdisk="❌",
        performance="➖",
        dataloss="❌",
    )
    _assert_mount_row(
        result,
        VOLUME_MAP["app_config"],
        write="✅",
        mount="✅",
        ramdisk="❌",
        performance="➖",
        dataloss="❌",
    )
    # Check that configuration issues are detected due to dataloss risk
    _assert_contains(result, "Configuration issues detected", result.args)
    assert result.returncode != 0


def test_mount_analysis_dataloss_risk(tmp_path: pathlib.Path) -> None:
    """Test mount analysis for dataloss risk on non-persistent filesystems.

    Tests 10-mounts.py detection when persistent database/config paths are
    mounted on non-persistent filesystems (tmpfs, ramfs).
    Expected: Mounts table shows dataloss risk warnings for persistent paths on tmpfs.

    Check script: 10-mounts.py
    Sample message: "Configuration issues detected"
    """
    paths = _setup_mount_tree(tmp_path, "dataloss_risk")
    # Mount persistent paths (db, config) on tmpfs to simulate non-persistent storage
    volumes = [
        (str(paths["app_log"]), VOLUME_MAP["app_log"], False),
        (str(paths["app_api"]), VOLUME_MAP["app_api"], False),
        (str(paths["services_run"]), VOLUME_MAP["services_run"], False),
        (str(paths["nginx_conf"]), VOLUME_MAP["nginx_conf"], False),
    ]
    # Use tmpfs mounts for persistent paths with proper permissions
    extra_args = [
        "--tmpfs",
        f"{VOLUME_MAP['app_db']}:uid=20211,gid=20211,mode=755",
        "--tmpfs",
        f"{VOLUME_MAP['app_config']}:uid=20211,gid=20211,mode=755",
    ]
    result = _run_container(
        "dataloss-risk", volumes=volumes, extra_args=extra_args, user="20211:20211"
    )
    # Check that mounts table shows dataloss risk for persistent paths on tmpfs
    _assert_mount_row(
        result,
        VOLUME_MAP["app_db"],
        write="✅",
        mount="✅",
        ramdisk="❌",
        performance="➖",
        dataloss="❌",
    )
    _assert_mount_row(
        result,
        VOLUME_MAP["app_config"],
        write="✅",
        mount="✅",
        ramdisk="❌",
        performance="➖",
        dataloss="❌",
    )
    # Check that configuration issues are detected due to dataloss risk
    _assert_contains(result, "Configuration issues detected", result.args)
    assert result.returncode != 0
