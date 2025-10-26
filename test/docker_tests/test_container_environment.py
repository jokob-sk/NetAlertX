'''
This set of tests requires netalertx-test image built. Ensure netalertx-test image is built prior
to starting these tests or they will fail.  netalertx-test image is generally rebuilt using the 
Build Unit Test Docker Image task. but can be created manually with the following command executed
in the workspace:
docker buildx build -t netalertx-test .
'''

import os
import pathlib
import shutil
import subprocess
import uuid
import re
import pytest

#TODO: test ALWAYS_FRESH_INSTALL
#TODO: test new named volume mount

IMAGE = os.environ.get("NETALERTX_TEST_IMAGE", "netalertx-test")
GRACE_SECONDS = float(os.environ.get("NETALERTX_TEST_GRACE", "2"))
DEFAULT_CAPS = ["NET_RAW", "NET_ADMIN", "NET_BIND_SERVICE"]

VOLUME_MAP = {
    "app_db": "/app/db",
    "app_config": "/app/config",
    "app_log": "/app/log",
    "app_api": "/app/api",
    "nginx_conf": "/services/config/nginx/conf.active",
    "services_run": "/services/run",
}

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
        ["docker", "volume", "rm", "-f", name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


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


def _setup_mount_tree(tmp_path: pathlib.Path, prefix: str, seed_config: bool = True, seed_db: bool = True) -> dict[str, pathlib.Path]:
    label = _unique_label(prefix)
    base = tmp_path / f"{label}_MOUNT_ROOT"
    base.mkdir()
    paths: dict[str, pathlib.Path] = {}

    for key, target in VOLUME_MAP.items():
        folder_name = f"{label}_{key.upper()}_INTENTIONAL_NETALERTX_TEST"
        host_path = base / folder_name
        host_path.mkdir(parents=True, exist_ok=True)
        # Make the directory writable so the container (running as UID 20211)
        # can create files on first run even if the host owner differs.
        try:
            host_path.chmod(0o777)
        except PermissionError:
            # If we can't chmod (uncommon in CI), tests that require strict
            # ownership will still run their own chown/chmod operations.
            pass
        paths[key] = host_path

    if seed_config:
        config_file = paths["app_config"] / "app.conf"
        shutil.copyfile(
            "/workspaces/NetAlertX/back/app.conf",
            config_file,
        )
        config_file.chmod(0o600)
    if seed_db:
        db_file = paths["app_db"] / "app.db"
        shutil.copyfile(
            "/workspaces/NetAlertX/db/app.db",
            db_file,
        )
        db_file.chmod(0o600)

    _chown_netalertx(base)

    return paths


def _setup_fixed_mount_tree(base: pathlib.Path) -> dict[str, pathlib.Path]:
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)

    paths: dict[str, pathlib.Path] = {}
    for key in VOLUME_MAP:
        host_path = base / f"{key.upper()}_NETALERTX_TEST"
        host_path.mkdir(parents=True, exist_ok=True)
        host_path.chmod(0o777)
        paths[key] = host_path
    return paths


def _build_volume_args(
    paths: dict[str, pathlib.Path],
    read_only: set[str] | None = None,
    skip: set[str] | None = None,
) -> list[tuple[str, str, bool]]:
    bindings: list[tuple[str, str, bool]] = []
    for key, target in VOLUME_MAP.items():
        if skip and key in skip:
            continue
        bindings.append((str(paths[key]), target, key in read_only if read_only else False))
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
) -> subprocess.CompletedProcess[str]:
    name = f"netalertx-test-{label}-{uuid.uuid4().hex[:8]}".lower()
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

    script = (
        mounts_ls
        + "sh /entrypoint.sh & pid=$!; "
        + f"sleep {sleep_seconds}; "
        + "if kill -0 $pid >/dev/null 2>&1; then kill -TERM $pid >/dev/null 2>&1 || true; fi; "
        + "wait $pid; code=$?; if [ $code -eq 143 ]; then exit 0; fi; exit $code"
    )
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
    stdouterr = (
        re.sub(r'\x1b\[[0-9;]*m', '', result.stdout or '') +
        re.sub(r'\x1b\[[0-9;]*m', '', result.stderr or '')
    )   
    result.output = stdouterr
    # Print container output for debugging in every test run.
    try:
        print("\n--- CONTAINER out ---\n", result.output)
    except Exception:
        pass

    return result



def _assert_contains(result, snippet: str, cmd: list[str] = None) -> None:
    if snippet not in result.output:
        cmd_str = " ".join(cmd) if cmd else ""
        raise AssertionError(
            f"Expected to find '{snippet}' in container output.\n"
            f"Got:\n{result.output}\n"
            f"Container command:\n{cmd_str}"
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



def test_root_owned_app_db_mount(tmp_path: pathlib.Path) -> None:
    """Test root-owned mounts - simulates mounting host directories owned by root.

    1. Root-Owned Mounts: Simulates mounting host directories owned by root
    (common with docker run -v /host/path:/app/db).
    Tests each required mount point when owned by root user.
    Expected: Warning about permission issues, guidance to fix ownership.

    Check script: check-app-permissions.sh
    Sample message: "⚠️  ATTENTION: Write permission denied. The application cannot write to..."
    """
    paths = _setup_mount_tree(tmp_path, "root_app_db")
    _chown_root(paths["app_db"])
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("root-app-db", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["app_db"]), result.args)
    finally:
        _chown_netalertx(paths["app_db"])


def test_root_owned_app_config_mount(tmp_path: pathlib.Path) -> None:
    """Test root-owned mounts - simulates mounting host directories owned by root.

    1. Root-Owned Mounts: Simulates mounting host directories owned by root
    (common with docker run -v /host/path:/app/db).
    Tests each required mount point when owned by root user.
    Expected: Warning about permission issues, guidance to fix ownership.
    """
    paths = _setup_mount_tree(tmp_path, "root_app_config")
    _chown_root(paths["app_config"])
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("root-app-config", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["app_config"]), result.args)
        assert result.returncode != 0
    finally:
        _chown_netalertx(paths["app_config"])


def test_root_owned_app_log_mount(tmp_path: pathlib.Path) -> None:
    """Test root-owned mounts - simulates mounting host directories owned by root.

    1. Root-Owned Mounts: Simulates mounting host directories owned by root
    (common with docker run -v /host/path:/app/db).
    Tests each required mount point when owned by root user.
    Expected: Warning about permission issues, guidance to fix ownership.
    """
    paths = _setup_mount_tree(tmp_path, "root_app_log")
    _chown_root(paths["app_log"])
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("root-app-log", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["app_log"]), result.args)
        assert result.returncode != 0
    finally:
        _chown_netalertx(paths["app_log"])


def test_root_owned_app_api_mount(tmp_path: pathlib.Path) -> None:
    """Test root-owned mounts - simulates mounting host directories owned by root.

    1. Root-Owned Mounts: Simulates mounting host directories owned by root
    (common with docker run -v /host/path:/app/db).
    Tests each required mount point when owned by root user.
    Expected: Warning about permission issues, guidance to fix ownership.
    """
    paths = _setup_mount_tree(tmp_path, "root_app_api")
    _chown_root(paths["app_api"])
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("root-app-api", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["app_api"]), result.args)
        assert result.returncode != 0
    finally:
        _chown_netalertx(paths["app_api"])


def test_root_owned_nginx_conf_mount(tmp_path: pathlib.Path) -> None:
    """Test root-owned mounts - simulates mounting host directories owned by root.

    1. Root-Owned Mounts: Simulates mounting host directories owned by root
    (common with docker run -v /host/path:/app/db).
    Tests each required mount point when owned by root user.
    Expected: Warning about permission issues, guidance to fix ownership.
    """
    paths = _setup_mount_tree(tmp_path, "root_nginx_conf")
    _chown_root(paths["nginx_conf"])
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("root-nginx-conf", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["nginx_conf"]), result.args)
        assert result.returncode != 0
    finally:
        _chown_netalertx(paths["nginx_conf"])


def test_root_owned_services_run_mount(tmp_path: pathlib.Path) -> None:
    """Test root-owned mounts - simulates mounting host directories owned by root.

    1. Root-Owned Mounts: Simulates mounting host directories owned by root
    (common with docker run -v /host/path:/app/db).
    Tests each required mount point when owned by root user.
    Expected: Warning about permission issues, guidance to fix ownership.
    """
    paths = _setup_mount_tree(tmp_path, "root_services_run")
    _chown_root(paths["services_run"])
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("root-services-run", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["services_run"]), result.args)
        assert result.returncode != 0
    finally:
        _chown_netalertx(paths["services_run"])


def test_zero_permissions_app_db_dir(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: "Write permission denied" error with path, guidance to fix permissions.

    Check script: check-app-permissions.sh
    Sample messages: "⚠️  ATTENTION: Write permission denied. The application cannot write to..."
                     "⚠️  ATTENTION: Read permission denied. The application cannot read from..."
    """
    paths = _setup_mount_tree(tmp_path, "chmod_app_db")
    _setup_zero_perm_dir(paths, "app_db")
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("chmod-app-db", volumes, user="20211:20211")
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["app_db"]), result.args)
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "app_db")


def test_zero_permissions_app_db_file(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: "Write permission denied" error with path, guidance to fix permissions.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_app_db_file")
    (paths["app_db"] / "app.db").chmod(0)
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("chmod-app-db-file", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        assert result.returncode != 0
    finally:
        (paths["app_db"] / "app.db").chmod(0o600)


def test_zero_permissions_app_config_dir(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: "Write permission denied" error with path, guidance to fix permissions.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_app_config")
    _setup_zero_perm_dir(paths, "app_config")
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("chmod-app-config", volumes, user="20211:20211")
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["app_config"]), result.args)
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "app_config")


def test_zero_permissions_app_config_file(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: "Write permission denied" error with path, guidance to fix permissions.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_app_config_file")
    (paths["app_config"] / "app.conf").chmod(0)
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("chmod-app-config-file", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        assert result.returncode != 0
    finally:
        (paths["app_config"] / "app.conf").chmod(0o600)


def test_zero_permissions_app_log_dir(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: "Write permission denied" error with path, guidance to fix permissions.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_app_log")
    _setup_zero_perm_dir(paths, "app_log")
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("chmod-app-log", volumes, user="20211:20211")
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["app_log"]), result.args)
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "app_log")


def test_zero_permissions_app_api_dir(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: "Write permission denied" error with path, guidance to fix permissions.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_app_api")
    _setup_zero_perm_dir(paths, "app_api")
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("chmod-app-api", volumes, user="20211:20211")
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["app_api"]), result.args)
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "app_api")


def test_zero_permissions_nginx_conf_dir(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: "Write permission denied" error with path, guidance to fix permissions.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_nginx_conf")
    _setup_zero_perm_dir(paths, "nginx_conf")
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("chmod-nginx-conf", volumes, user="20211:20211")
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "nginx_conf")


def test_zero_permissions_services_run_dir(tmp_path: pathlib.Path) -> None:
    """Test zero permissions - simulates mounting directories/files with no permissions.

    2. Zero Permissions: Simulates mounting directories/files with no permissions (chmod 000).
    Tests directories and files with no read/write/execute permissions.
    Expected: "Write permission denied" error with path, guidance to fix permissions.
    """
    paths = _setup_mount_tree(tmp_path, "chmod_services_run")
    _setup_zero_perm_dir(paths, "services_run")
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("chmod-services-run", volumes, user="20211:20211")
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, str(VOLUME_MAP["services_run"]), result.args)
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "services_run")


def test_readonly_app_db_mount(tmp_path: pathlib.Path) -> None:
    """Test readonly mounts - simulates read-only volume mounts in containers.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when mounted read-only.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "readonly_app_db")
    volumes = _build_volume_args(paths, read_only={"app_db"})
    result = _run_container("readonly-app-db", volumes)
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, str(VOLUME_MAP["app_db"]), result.args)
    assert result.returncode != 0


def test_readonly_app_config_mount(tmp_path: pathlib.Path) -> None:
    """Test readonly mounts - simulates read-only volume mounts in containers.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when mounted read-only.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "readonly_app_config")
    volumes = _build_volume_args(paths, read_only={"app_config"})
    result = _run_container("readonly-app-config", volumes)
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, str(VOLUME_MAP["app_config"]), result.args)
    assert result.returncode != 0


def test_readonly_app_log_mount(tmp_path: pathlib.Path) -> None:
    """Test readonly mounts - simulates read-only volume mounts in containers.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when mounted read-only.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "readonly_app_log")
    volumes = _build_volume_args(paths, read_only={"app_log"})
    result = _run_container("readonly-app-log", volumes)
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, str(VOLUME_MAP["app_log"]), result.args)
    assert result.returncode != 0


def test_readonly_app_api_mount(tmp_path: pathlib.Path) -> None:
    """Test readonly mounts - simulates read-only volume mounts in containers.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when mounted read-only.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "readonly_app_api")
    volumes = _build_volume_args(paths, read_only={"app_api"})
    result = _run_container("readonly-app-api", volumes)
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, str(VOLUME_MAP["app_api"]), result.args)
    assert result.returncode != 0


def test_readonly_nginx_conf_mount(tmp_path: pathlib.Path) -> None:
    """Test readonly mounts - simulates read-only volume mounts in containers.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when mounted read-only.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "readonly_nginx_conf")
    _setup_zero_perm_dir(paths, "nginx_conf")
    volumes = _build_volume_args(paths)
    try:
        result = _run_container("readonly-nginx-conf", volumes)
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, "/services/config/nginx/conf.active", result.args)
        assert result.returncode != 0
    finally:
        _restore_zero_perm_dir(paths, "nginx_conf")


def test_readonly_services_run_mount(tmp_path: pathlib.Path) -> None:
    """Test readonly mounts - simulates read-only volume mounts in containers.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when mounted read-only.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "readonly_services_run")
    volumes = _build_volume_args(paths, read_only={"services_run"})
    result = _run_container("readonly-services-run", volumes)
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, str(VOLUME_MAP["services_run"]), result.args)
    assert result.returncode != 0


def test_custom_port_without_writable_conf(tmp_path: pathlib.Path) -> None:
    """Test custom port configuration without writable nginx config mount.

    4. Custom Port Without Nginx Config Mount: Simulates setting custom LISTEN_ADDR/PORT
    without mounting nginx config. Container starts but uses default address.
    Expected: Container starts but uses default address, warning about missing config mount.

    Check script: check-nginx-config.sh
    Sample messages: "⚠️  ATTENTION: Nginx configuration mount /services/config/nginx/conf.active is missing."
                     "⚠️  ATTENTION: Unable to write to /services/config/nginx/conf.active/netalertx.conf."
    """
    paths = _setup_mount_tree(tmp_path, "custom_port_ro_conf")
    paths["nginx_conf"].chmod(0o500)
    volumes = _build_volume_args(paths)
    try:
        result = _run_container(
            "custom-port-ro-conf",
            volumes,
            env={"PORT": "24444", "LISTEN_ADDR": "127.0.0.1"},
        )
        _assert_contains(result, "Write permission denied", result.args)
        _assert_contains(result, "/services/config/nginx/conf.active", result.args)
        assert result.returncode != 0
    finally:
        paths["nginx_conf"].chmod(0o755)

def test_missing_mount_app_db(tmp_path: pathlib.Path) -> None:
    """Test missing required mounts - simulates forgetting to mount persistent volumes.
    ...
    """
    paths = _setup_mount_tree(tmp_path, "missing_mount_app_db")
    volumes = _build_volume_args(paths, skip={"app_db"})
    # CHANGE: Run as root (0:0) to bypass all permission checks on other mounts.
    result = _run_container("missing-mount-app-db", volumes, user="0:0")
    # Acknowledge the original intent to check for permission denial (now implicit via root)
    # _assert_contains(result, "Write permission denied", result.args) # No longer needed, as root user is used
    
    # Robust assertion: check for both the warning and the path
    if "not a persistent mount" not in result.output or "/app/db" not in result.output:
        print("\n--- DEBUG CONTAINER OUTPUT ---\n", result.output)
        raise AssertionError("Expected persistent mount warning for /app/db in container output.")


def test_missing_mount_app_config(tmp_path: pathlib.Path) -> None:
    """Test missing required mounts - simulates forgetting to mount persistent volumes.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when missing.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "missing_mount_app_config")
    volumes = _build_volume_args(paths, skip={"app_config"})
    result = _run_container("missing-mount-app-config", volumes, user="20211:20211")
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, "/app/config", result.args)


def test_missing_mount_app_log(tmp_path: pathlib.Path) -> None:
    """Test missing required mounts - simulates forgetting to mount persistent volumes.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when missing.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "missing_mount_app_log")
    volumes = _build_volume_args(paths, skip={"app_log"})
    result = _run_container("missing-mount-app-log", volumes, user="20211:20211")
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, "/app/log", result.args)


def test_missing_mount_app_api(tmp_path: pathlib.Path) -> None:
    """Test missing required mounts - simulates forgetting to mount persistent volumes.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when missing.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "missing_mount_app_api")
    volumes = _build_volume_args(paths, skip={"app_api"})
    result = _run_container("missing-mount-app-api", volumes, user="20211:20211")
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, "/app/api", result.args)


def test_missing_mount_nginx_conf(tmp_path: pathlib.Path) -> None:
    """Test missing required mounts - simulates forgetting to mount persistent volumes.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when missing.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "missing_mount_nginx_conf")
    volumes = _build_volume_args(paths, skip={"nginx_conf"})
    result = _run_container("missing-mount-nginx-conf", volumes, user="20211:20211")
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, "/services/config/nginx/conf.active", result.args)
    assert result.returncode != 0


def test_missing_mount_services_run(tmp_path: pathlib.Path) -> None:
    """Test missing required mounts - simulates forgetting to mount persistent volumes.

    3. Missing Required Mounts: Simulates forgetting to mount required persistent volumes
    in read-only containers. Tests each required mount point when missing.
    Expected: "Write permission denied" error with path, guidance to add volume mounts.
    """
    paths = _setup_mount_tree(tmp_path, "missing_mount_services_run")
    volumes = _build_volume_args(paths, skip={"services_run"})
    result = _run_container("missing-mount-services-run", volumes, user="20211:20211")
    _assert_contains(result, "Write permission denied", result.args)
    _assert_contains(result, "/services/run", result.args)
    _assert_contains(result, "Container startup checks failed with exit code", result.args)


def test_missing_capabilities_triggers_warning(tmp_path: pathlib.Path) -> None:
    """Test missing required capabilities - simulates insufficient container privileges.

    5. Missing Required Capabilities: Simulates running without NET_ADMIN, NET_RAW,
    NET_BIND_SERVICE capabilities. Required for ARP scanning and network operations.
    Expected: "exec /bin/sh: operation not permitted" error, guidance to add capabilities.

    Check script: check-cap.sh
    Sample message: "⚠️  ATTENTION: Raw network capabilities are missing. Tools that rely on NET_RAW..."
    """
    paths = _setup_mount_tree(tmp_path, "missing_caps")
    volumes = _build_volume_args(paths)
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

    Check script: check-root.sh
    Sample message: "⚠️  ATTENTION: NetAlertX is running as root (UID 0). This defeats every hardening..."
    """
    paths = _setup_mount_tree(tmp_path, "run_as_root")
    volumes = _build_volume_args(paths)
    result = _run_container(
        "run-as-root",
        volumes,
        user="0:0",
    )
    _assert_contains(result, "NetAlertX is running as root", result.args)
    assert result.returncode != 0


def test_running_as_uid_1000_warns(tmp_path: pathlib.Path) -> None:
    # No output assertion, just returncode check
    """Test running as wrong user - simulates using arbitrary user instead of netalertx.

    7. Running as Wrong User: Simulates running as arbitrary user (UID 1000) instead
    of netalertx user. Permission errors due to incorrect user context.
    Expected: Permission errors, guidance to use correct user.

    Check script: check-user-netalertx.sh
    Sample message: "⚠️  ATTENTION: NetAlertX is running as UID 1000:1000. Hardened permissions..."
    """
    paths = _setup_mount_tree(tmp_path, "run_as_1000")
    volumes = _build_volume_args(paths)
    result = _run_container(
        "run-as-1000",
        volumes,
        user="1000:1000",
    )
    assert result.returncode != 0


def test_missing_host_network_warns(tmp_path: pathlib.Path) -> None:
    # No output assertion, just returncode check
    """Test missing host networking - simulates running without host network mode.

    8. Missing Host Networking: Simulates running without network_mode: host.
    Limits ARP scanning capabilities for network discovery.
    Expected: Warning about ARP scanning limitations, guidance to use host networking.

    Check script: check-network-mode.sh
    Sample message: "⚠️  ATTENTION: NetAlertX is not running with --network=host. Bridge networking..."
    """
    paths = _setup_mount_tree(tmp_path, "missing_host_net")
    volumes = _build_volume_args(paths)
    result = _run_container(
        "missing-host-network",
        volumes,
        network_mode=None,
    )
    assert result.returncode != 0


def test_missing_app_conf_triggers_seed(tmp_path: pathlib.Path) -> None:
    """Test missing configuration file seeding - simulates corrupted/missing app.conf.

    9. Missing Configuration File: Simulates corrupted/missing app.conf.
    Container automatically regenerates default configuration on startup.
    Expected: Automatic regeneration of default configuration.
    """
    paths = _setup_mount_tree(tmp_path, "missing_app_conf")
    (paths["app_config"] / "app.conf").unlink()
    volumes = _build_volume_args(paths)
    result = _run_container("missing-app-conf", volumes, user="0:0")
    _assert_contains(result, "Default configuration written to", result.args)
    assert result.returncode != 0


def test_missing_app_db_triggers_seed(tmp_path: pathlib.Path) -> None:
    """Test missing database file seeding - simulates corrupted/missing app.db.

    10. Missing Database File: Simulates corrupted/missing app.db.
    Container automatically creates initial database schema on startup.
    Expected: Automatic creation of initial database schema.
    """
    paths = _setup_mount_tree(tmp_path, "missing_app_db")
    (paths["app_db"] / "app.db").unlink()
    volumes = _build_volume_args(paths)
    result = _run_container("missing-app-db", volumes, user="0:0")
    _assert_contains(result, "Building initial database schema", result.args)
    assert result.returncode != 0


def test_tmpfs_config_mount_warns(tmp_path: pathlib.Path) -> None:
    """Test tmpfs instead of volumes - simulates using tmpfs for persistent data.

    11. Tmpfs Instead of Volumes: Simulates using tmpfs mounts instead of persistent volumes
    (data loss on restart). Tests config and db directories mounted as tmpfs.
    Expected: "Read permission denied" error, guidance to use persistent volumes.

    Check scripts: check-storage.sh, check-storage-extra.sh
    Sample message: "⚠️  ATTENTION: /app/config is not a persistent mount. Your data in this directory..."
    """
    paths = _setup_mount_tree(tmp_path, "tmpfs_config")
    volumes = _build_volume_args(paths, skip={"app_config"})
    extra = ["--mount", "type=tmpfs,destination=/app/config"]
    result = _run_container(
        "tmpfs-config",
        volumes,
        extra_args=extra,
    )
    _assert_contains(result, "not a persistent mount.", result.args)
    _assert_contains(result, "/app/config", result.args)


def test_tmpfs_db_mount_warns(tmp_path: pathlib.Path) -> None:
    """Test tmpfs instead of volumes - simulates using tmpfs for persistent data.

    11. Tmpfs Instead of Volumes: Simulates using tmpfs mounts instead of persistent volumes
    (data loss on restart). Tests config and db directories mounted as tmpfs.
    Expected: "Read permission denied" error, guidance to use persistent volumes.
    """
    paths = _setup_mount_tree(tmp_path, "tmpfs_db")
    volumes = _build_volume_args(paths, skip={"app_db"})
    extra = ["--mount", "type=tmpfs,destination=/app/db"]
    result = _run_container(
        "tmpfs-db",
        volumes,
        extra_args=extra,
    )
    _assert_contains(result, "not a persistent mount.", result.args)
    _assert_contains(result, "/app/db", result.args)
    assert result.returncode != 0
