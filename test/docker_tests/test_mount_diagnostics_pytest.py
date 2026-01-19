#!/usr/bin/env python3
"""
Pytest-based Mount Diagnostic Tests for NetAlertX

Tests all possible mount configurations for each path to validate the diagnostic tool.
Uses pytest framework for proper test discovery and execution.

FAIL-SOFT PHILOSOPHY:
The container is designed to "Fail Soft" in restricted environments.
- If capabilities (like CAP_CHOWN) are missing, it warns but proceeds.
- If mounts are suboptimal (RAM disk), it warns but proceeds.
- This ensures compatibility with strict security policies (e.g., read-only root, dropped caps).

TODO: Future Robustness & Compatibility Tests
1. Symlink Attacks: Verify behavior when a writable directory is mounted via a symlink.
   Hypothesis: The tool might misidentify the mount status or path.
2. OverlayFS/Copy-up Scenarios: Investigate behavior on filesystems like Synology's OverlayFS.
   Hypothesis: Files might appear writable but fail on specific operations (locking, mmap).
3. Text-based Output: Refactor output to support text-based status (e.g., [OK], [FAIL])
   instead of emojis for better compatibility with terminals that don't support unicode.

All tests use the mounts table. For reference, the mounts table looks like this:

 Path                    | Writeable | Mount | RAMDisk | Performance | DataLoss
-------------------------+-----------+-------+---------+-------------+---------
 /data/db                |     ✅    |   ❌  |    ➖   |      ➖     |    ❌
 /data/config            |     ✅    |   ❌  |    ➖   |      ➖     |    ❌
 /tmp/api                |     ✅    |   ❌  |    ❌   |      ❌     |    ✅
 /tmp/log                |     ✅    |   ❌  |    ❌   |      ❌     |    ✅
 /tmp/run                |     ✅    |   ❌  |    ❌   |      ❌     |    ✅
 /tmp/nginx/active-config|     ✅    |   ❌  |    ❌   |      ❌     |    ✅

Table Assertions:
- Use assert_table_row(output, path, writeable=True/False/None, mount=True/False/None, ...)
- Emojis are converted: ✅=True, ❌=False, ➖=None
- Example: assert_table_row(output, "/data/db", writeable=True, mount=False, dataloss=False)

"""

import os
import subprocess
import sys
import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# Test configurations directory
CONFIG_DIR = Path(__file__).parent / "configurations"
CONTAINER_PATHS = {
    "db": "/data/db",
    "config": "/data/config",
    "api": os.environ.get("NETALERTX_API", "/tmp/api"),
    "log": "/tmp/log",
    "run": "/tmp/run",
    "active_config": "/tmp/nginx/active-config",
}

TROUBLESHOOTING_URLS = [
    "https://docs.netalertx.com/docker-troubleshooting/file-permissions",
    "https://docs.netalertx.com/docker-troubleshooting/mount-configuration-issues",
    "https://docs.netalertx.com/docker-troubleshooting/incorrect-user",
    "https://docs.netalertx.com/docker-troubleshooting/missing-capabilities",
]


def capture_project_mandatory_required_audit_stream(container_name: str) -> subprocess.Popen[str]:
    """Stream container logs to stdout for auditing; required to stay enabled."""

    proc = subprocess.Popen(
        ["docker", "logs", "-f", container_name],
        stdout=sys.stdout,  # Do not touch stdout/stderr, required for audit purposes.
        stderr=sys.stderr,
        text=True,
    )
    return proc


@dataclass
class MountTableRow:
    """Represents a parsed row from the mount diagnostic table."""

    path: str
    readable: bool
    writeable: bool
    mount: bool
    ramdisk: Optional[bool]  # None for ➖
    performance: Optional[bool]  # None for ➖
    dataloss: bool


class _Unset:
    """Sentinel object for optional expectations."""


UNSET = _Unset()
Expectation = Optional[bool] | _Unset


def _expected_to_emoji(value: Optional[bool]) -> str:
    if value is True:
        return "✅"
    if value is False:
        return "❌"
    return "➖"


def parse_mount_table(output: str) -> List[MountTableRow]:
    """Parse the mount diagnostic table from stdout."""
    rows = []

    # Find the table in the output
    lines = output.split("\n")
    table_start = None

    for i, line in enumerate(lines):
        if line.startswith(" Path ") and "|" in line:
            table_start = i
            break

    if table_start is None:
        return rows

    # Skip header and separator lines
    data_lines = lines[table_start + 2 :]

    for line in data_lines:
        if "|" not in line or line.strip() == "":
            continue

        # Split by | and clean up
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 7:
            continue

        path = parts[0]
        if not path:
            continue

        # Convert emojis to boolean/none
        def emoji_to_bool(emoji: str) -> Optional[bool]:
            emoji = emoji.strip()
            if emoji == "✅":
                return True
            elif emoji == "❌":
                return False
            elif emoji == "➖":
                return None
            return None

        try:
            row = MountTableRow(
                path=path,
                readable=emoji_to_bool(parts[1]),
                writeable=emoji_to_bool(parts[2]),
                mount=emoji_to_bool(parts[3]),
                ramdisk=emoji_to_bool(parts[4]),
                performance=emoji_to_bool(parts[5]),
                dataloss=emoji_to_bool(parts[6]),
            )
            rows.append(row)
        except (IndexError, ValueError):
            continue

    return rows


def assert_has_troubleshooting_url(output: str) -> None:
    """Ensure at least one troubleshooting link is present in the output."""

    for url in TROUBLESHOOTING_URLS:
        if url in output:
            return

    pytest.fail(
        "Expected troubleshooting URL in output; got none of "
        f"{TROUBLESHOOTING_URLS}"
    )


def assert_table_row(
    output: str,
    expected_path: str,
    readable: Expectation = UNSET,
    writeable: Expectation = UNSET,
    mount: Expectation = UNSET,
    ramdisk: Expectation = UNSET,
    performance: Expectation = UNSET,
    dataloss: Expectation = UNSET,
) -> MountTableRow:
    """Assert that a specific table row matches expected values."""
    rows = parse_mount_table(output)

    # Find the row for the expected path
    matching_row = None
    for row in rows:
        if row.path == expected_path:
            matching_row = row
            break

    assert matching_row is not None, (
        f"Path '{expected_path}' not found in table. Available paths: {[r.path for r in rows]}"
    )

    raw_line = None
    for line in output.splitlines():
        if line.strip().startswith(expected_path):
            raw_line = line
            break

    assert raw_line is not None, f"Raw table line for '{expected_path}' not found in output."

    raw_parts = [part.strip() for part in raw_line.split("|")]
    assert len(raw_parts) >= 7, f"Malformed table row for '{expected_path}': {raw_line}"

    def _check(field_name: str, expected: Expectation, actual: Optional[bool], column_index: int) -> None:
        if expected is UNSET:
            return
        assert actual == expected, (
            f"Path '{expected_path}': expected {field_name}={expected}, got {actual}"
        )
        expected_emoji = _expected_to_emoji(expected)
        assert raw_parts[column_index] == expected_emoji, (
            f"Path '{expected_path}': expected emoji {expected_emoji} for {field_name}, "
            f"got '{raw_parts[column_index]}' in row: {raw_line}"
        )

    _check("readable", readable, matching_row.readable, 1)
    _check("writeable", writeable, matching_row.writeable, 2)
    _check("mount", mount, matching_row.mount, 3)
    _check("ramdisk", ramdisk, matching_row.ramdisk, 4)
    _check("performance", performance, matching_row.performance, 5)
    _check("dataloss", dataloss, matching_row.dataloss, 6)

    return matching_row


@dataclass
class TestScenario:
    """Represents a test scenario for a specific path configuration."""

    __test__ = False  # Prevent pytest from collecting this as a test class
    name: str
    path_var: str
    container_path: str
    is_persistent: bool
    docker_compose: str
    expected_issues: List[str]  # List of expected issue types
    expected_exit_code: int  # Expected container exit code


@pytest.fixture(scope="session")
def netalertx_test_image():
    """Ensure the netalertx-test image exists."""
    image_name = os.environ.get("NETALERTX_TEST_IMAGE", "netalertx-test")

    # Check if image exists
    try:
        result = subprocess.run(
            ["docker", "images", "-q", image_name],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("Docker CLI not found; skipping docker-based mount diagnostics tests.")
    except subprocess.TimeoutExpired:
        pytest.skip("Docker is not responding; skipping docker-based mount diagnostics tests.")

    if result.returncode != 0:
        pytest.skip(
            f"Docker returned error while checking images (rc={result.returncode}): {result.stderr.strip() or '<no stderr>'}"
        )

    if not result.stdout.strip():
        pytest.skip(f"NetAlertX test image '{image_name}' not found. Build it first.")

    return image_name


@pytest.fixture
def test_scenario(request):
    """Fixture that provides test scenarios."""
    return request.param


def create_test_scenarios() -> List[TestScenario]:
    """Create all test scenarios."""

    scenarios = []

    # Define paths to test
    paths = [
        ("db", CONTAINER_PATHS["db"], True, "NETALERTX_DB"),
        ("config", CONTAINER_PATHS["config"], True, "NETALERTX_CONFIG"),
        ("api", CONTAINER_PATHS["api"], False, "NETALERTX_API"),
        ("log", CONTAINER_PATHS["log"], False, "NETALERTX_LOG"),
        ("run", CONTAINER_PATHS["run"], False, "SYSTEM_SERVICES_RUN"),
        (
            "active_config",
            CONTAINER_PATHS["active_config"],
            False,
            "SYSTEM_SERVICES_ACTIVE_CONFIG",
        ),
    ]

    # Test scenarios for each path
    test_scenarios = [
        ("no-mount", ["table_issues", "warning_message"]),  # Always issues
        ("ramdisk", []),  # Good for non-persistent, bad for persistent
        (
            "mounted",
            ["table_issues", "warning_message"],
        ),  # Bad for non-persistent, good for persistent
        ("unwritable", ["table_issues", "warning_message"]),  # Always issues
    ]

    for path_name, container_path, is_persistent, env_var in paths:
        for scenario_name, base_expected_issues in test_scenarios:
            # Adjust expected issues based on persistence and scenario
            expected_issues = list(base_expected_issues)  # Copy the list

            if scenario_name == "ramdisk" and is_persistent:
                # Ramdisk is bad for persistent paths
                expected_issues = ["table_issues", "warning_message"]
            elif scenario_name == "mounted" and is_persistent:
                # Mounted is good for persistent paths
                expected_issues = []
            elif path_name == "active_config" and scenario_name == "unwritable":
                # active_config unwritable: RAM disk issues detected
                expected_issues = ["table_issues", "warning_message"]
            elif path_name == "active_config" and scenario_name == "no-mount":
                # Active config now lives on the internal tmpfs by default; missing host mount is healthy
                expected_issues = []
            compose_file = f"docker-compose.mount-test.{path_name}_{scenario_name}.yml"

            # Diagnostics should warn but keep the container running; expect success
            expected_exit_code = 0

            scenarios.append(
                TestScenario(
                    name=f"{path_name}_{scenario_name}",
                    path_var=env_var,
                    container_path=container_path,
                    is_persistent=is_persistent,
                    docker_compose=compose_file,
                    expected_issues=expected_issues,
                    expected_exit_code=expected_exit_code,
                )
            )

    # Focused coverage: mounted-but-unreadable (-wx) scenarios.
    # These are intentionally not part of the full matrix to avoid runtime bloat.
    scenarios.extend(
        [
            TestScenario(  # Will no longer fail due to the root-entrypoint fix
                name="data_noread",
                path_var="NETALERTX_DATA",
                container_path="/data",
                is_persistent=True,
                docker_compose="docker-compose.mount-test.data_noread.yml",
                expected_issues=[],
                expected_exit_code=0,
            ),
            TestScenario(  # Will no longer fail due to the root-entrypoint fix
                name="db_noread",
                path_var="NETALERTX_DB",
                container_path="/data/db",
                is_persistent=True,
                docker_compose="docker-compose.mount-test.db_noread.yml",
                expected_issues=[],
                expected_exit_code=0,
            ),
            TestScenario(
                name="tmp_noread",
                path_var="SYSTEM_SERVICES_RUN_TMP",
                container_path="/tmp",
                is_persistent=False,
                docker_compose="docker-compose.mount-test.tmp_noread.yml",
                expected_issues=["table_issues", "warning_message"],
                expected_exit_code=0,
            ),
            TestScenario(
                name="api_noread",
                path_var="NETALERTX_API",
                container_path=CONTAINER_PATHS["api"],
                is_persistent=False,
                docker_compose="docker-compose.mount-test.api_noread.yml",
                expected_issues=["table_issues", "warning_message"],
                expected_exit_code=0,
            ),
        ]
    )

    return scenarios


def _print_compose_logs(
    compose_file: Path,
    project_name: str,
    reason: str,
    env: dict[str, str] | None = None,
) -> None:
    """Dump docker compose logs for debugging when a test fails."""

    env = env or os.environ.copy()
    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "-p",
        project_name,
        "logs",
        "--no-color",
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        env=env,
    )
    print("\n=== docker compose logs (DO NOT REMOVE) ===")
    print(f"Reason: {reason}")
    print("Command:", " ".join(cmd))
    print(result.stdout or "<no stdout>")
    if result.stderr:
        print("--- logs stderr ---")
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
    print("=== end docker compose logs ===\n")


def validate_scenario_table_output(output: str, test_scenario: TestScenario) -> None:
    """Validate the diagnostic table for scenarios that should report issues."""

    if not test_scenario.expected_issues:
        if test_scenario.name in ("data_noread", "db_noread"):
            # Cannot fix chmod 0300 (write-only) when running as user; expect R=❌, W=✅, dataloss=✅
            assert_table_row(
                output,
                test_scenario.container_path,
                readable=False,
                writeable=True,
                mount=True,
                ramdisk=None,
                performance=None,
                dataloss=True,
            )
        return

    try:
        if test_scenario.name.endswith("_noread"):
            # Mounted but unreadable: R should fail, W should succeed, and the mount itself
            # should otherwise be correctly configured.
            if test_scenario.container_path.startswith("/data"):
                # Persistent paths: mounted, not a ramdisk, no dataloss flag.
                assert_table_row(
                    output,
                    test_scenario.container_path,
                    readable=False,
                    writeable=True,
                    mount=True,
                    ramdisk=None,
                    performance=None,
                    dataloss=True,
                )
            else:
                # Ramdisk paths: mounted tmpfs, ramdisk ok, performance ok.
                assert_table_row(
                    output,
                    test_scenario.container_path,
                    readable=False,
                    writeable=True,
                    mount=True,
                    ramdisk=True,
                    performance=True,
                    dataloss=True,
                )
            return

        if test_scenario.name.startswith("db_"):
            if test_scenario.name == "db_ramdisk":
                assert_table_row(
                    output,
                    CONTAINER_PATHS["db"],
                    mount=True,
                    ramdisk=False,
                    dataloss=False,
                )
            elif test_scenario.name == "db_no-mount":
                assert_table_row(
                    output, CONTAINER_PATHS["db"], mount=False, dataloss=False
                )
            elif test_scenario.name == "db_unwritable":
                assert_table_row(output, CONTAINER_PATHS["db"], writeable=False)

        elif test_scenario.name.startswith("config_"):
            if test_scenario.name == "config_ramdisk":
                assert_table_row(
                    output,
                    CONTAINER_PATHS["config"],
                    mount=True,
                    ramdisk=False,
                    dataloss=False,
                )
            elif test_scenario.name == "config_no-mount":
                assert_table_row(
                    output, CONTAINER_PATHS["config"], mount=False, dataloss=False
                )
            elif test_scenario.name == "config_unwritable":
                assert_table_row(output, CONTAINER_PATHS["config"], writeable=False)

        elif test_scenario.name.startswith("api_"):
            if test_scenario.name == "api_mounted":
                assert_table_row(
                    output, CONTAINER_PATHS["api"], mount=True, performance=False
                )
            elif test_scenario.name == "api_no-mount":
                assert_table_row(
                    output, CONTAINER_PATHS["api"], mount=False, performance=False
                )
            elif test_scenario.name == "api_unwritable":
                assert_table_row(output, CONTAINER_PATHS["api"], writeable=False)

        elif test_scenario.name.startswith("log_"):
            if test_scenario.name == "log_mounted":
                assert_table_row(
                    output, CONTAINER_PATHS["log"], mount=True, performance=False
                )
            elif test_scenario.name == "log_no-mount":
                assert_table_row(
                    output, CONTAINER_PATHS["log"], mount=False, performance=False
                )
            elif test_scenario.name == "log_unwritable":
                assert_table_row(output, CONTAINER_PATHS["log"], writeable=False)

        elif test_scenario.name.startswith("run_"):
            if test_scenario.name == "run_mounted":
                assert_table_row(
                    output, CONTAINER_PATHS["run"], mount=True, performance=False
                )
            elif test_scenario.name == "run_no-mount":
                assert_table_row(
                    output, CONTAINER_PATHS["run"], mount=False, performance=False
                )
            elif test_scenario.name == "run_unwritable":
                assert_table_row(output, CONTAINER_PATHS["run"], writeable=False)

        elif test_scenario.name.startswith("active_config_"):
            if test_scenario.name == "active_config_mounted":
                assert_table_row(
                    output,
                    CONTAINER_PATHS["active_config"],
                    mount=True,
                    performance=False,
                )
            # active_config_no-mount is considered healthy (internal tmpfs), so no validation needed here.
            elif test_scenario.name == "active_config_unwritable":
                assert_table_row(
                    output,
                    CONTAINER_PATHS["active_config"],
                    ramdisk=False,
                    performance=False,
                )

    except AssertionError as e:
        pytest.fail(f"Table validation failed for {test_scenario.name}: {e}")


@pytest.mark.parametrize("test_scenario", create_test_scenarios(), ids=lambda s: s.name)
@pytest.mark.docker
def test_mount_diagnostic(netalertx_test_image, test_scenario):
    """Test that the mount diagnostic tool correctly identifies issues for each configuration."""

    # Use the pre-generated docker-compose file
    compose_file = CONFIG_DIR / "mount-tests" / test_scenario.docker_compose
    assert compose_file.exists(), f"Docker compose file not found: {compose_file}"

    # Start container
    project_name = f"mount-test-{test_scenario.name.replace('_', '-')}"
    compose_env = os.environ.copy()
    base_cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "-p",
        project_name,
    ]
    logs_emitted = False

    def ensure_logs(reason: str) -> None:
        nonlocal logs_emitted
        if logs_emitted:
            return
        _print_compose_logs(compose_file, project_name, reason, env=compose_env)
        logs_emitted = True

    # Remove any existing containers with the same project name
    result = subprocess.run(
        base_cmd + ["down", "-v"], capture_output=True, text=True, timeout=30, env=compose_env
    )
    print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
    print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.

    # Pre-initialize volumes for _noread scenarios that use persistent volumes
    if test_scenario.name in ["data_noread", "db_noread"]:
        path_to_chmod = test_scenario.container_path
        # We need to run as root to chown/chmod, then the main container runs as 20211
        # Note: We use 'netalertx' service but override user and entrypoint
        init_cmd = base_cmd + [
            "run",
            "--rm",
            "--cap-add",
            "FOWNER",
            "--user",
            "0",
            "--entrypoint",
            "/bin/sh",
            "netalertx",
            "-c",
            f"mkdir -p {path_to_chmod} && chown 20211:20211 {path_to_chmod} && chmod 0300 {path_to_chmod}",
        ]
        result_init = subprocess.run(
            init_cmd, capture_output=True, text=True, timeout=30, env=compose_env
        )
        if result_init.returncode != 0:
            pytest.fail(f"Failed to initialize volume permissions: {result_init.stderr}")

    # The compose files use a fixed container name; ensure no stale container blocks the run.
    container_name = f"netalertx-test-mount-{test_scenario.name}"
    result = subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=compose_env,
    )
    print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
    print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.

    cmd_up = base_cmd + ["up", "-d"]

    try:
        audit_proc: subprocess.Popen[str] | None = None
        result_up = subprocess.run(
            cmd_up, capture_output=True, text=True, timeout=20, env=compose_env
        )
        print(result_up.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result_up.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        if result_up.returncode != 0:
            ensure_logs("compose up failed")
            pytest.fail(
                f"Failed to start container: {result_up.stderr}\n"
                f"STDOUT: {result_up.stdout}"
            )

        audit_proc = capture_project_mandatory_required_audit_stream(container_name)

        # Wait for container to be ready
        import time
        # Container is still running - validate the diagnostics already run at startup
        # Give entrypoint scripts a moment to finish outputting to logs
        time.sleep(2)

        result_logs = subprocess.run(
            ["docker", "logs", container_name], capture_output=True, text=True, timeout=30
        )
        diagnostic_output = result_logs.stdout + result_logs.stderr

        # Always surface diagnostic output for visibility
        print("\n[diagnostic output from startup logs]\n", diagnostic_output)

        # Always validate the table output, even when expected_issues is empty.
        validate_scenario_table_output(diagnostic_output, test_scenario)

        if test_scenario.expected_issues:
            assert_has_troubleshooting_url(diagnostic_output)
            assert "⚠️" in diagnostic_output, (
                f"Issue scenario {test_scenario.name} should include a warning symbol in startup logs"
            )
        else:
            # Should have table output but no warning message
            assert "Path" in diagnostic_output, (
                f"Good config {test_scenario.name} should show table, got: {diagnostic_output}"
            )
        return  # Test passed - diagnostic output validated via logs

    finally:
        result = subprocess.run(
            base_cmd + ["down", "-v"], capture_output=True, text=True, timeout=30, env=compose_env
        )
        print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        if audit_proc:
            try:
                audit_proc.terminate()
            except Exception:
                pass


def test_table_parsing():
    """Test the table parsing and assertion functions."""

    sample_output = """
 Path                | R | W | Mount | RAMDisk | Performance | DataLoss
---------------------+---+---+-------+---------+-------------+----------
/data/db            | ✅ | ✅ |   ❌  |    ➖   |      ➖     |    ❌
/tmp/api            | ✅ | ✅ |   ✅  |    ✅   |      ✅     |    ✅
"""

    # Test parsing
    rows = parse_mount_table(sample_output)
    assert len(rows) == 2

    # Test assertions
    assert_table_row(
        sample_output,
        "/data/db",
        readable=True,
        writeable=True,
        mount=False,
        ramdisk=None,
        performance=None,
        dataloss=False,
    )
    assert_table_row(
        sample_output,
        CONTAINER_PATHS["api"],
        readable=True,
        writeable=True,
        mount=True,
        ramdisk=True,
        performance=True,
        dataloss=True,
    )


@pytest.mark.docker
def test_cap_chown_required_when_caps_dropped():
    """Ensure startup warns (but runs) when CHOWN capability is removed."""

    compose_file = CONFIG_DIR / "mount-tests" / "docker-compose.mount-test.cap_chown_missing.yml"
    assert compose_file.exists(), "CAP_CHOWN test compose file missing"

    project_name = "mount-test-cap-chown-missing"
    compose_env = os.environ.copy()
    base_cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "-p",
        project_name,
    ]

    container_name = "netalertx-test-mount-cap_chown_missing"

    result = subprocess.run(
        [*base_cmd, "down", "-v"], capture_output=True, text=True, timeout=30, env=compose_env
    )
    print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
    print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
    result = subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=compose_env,
    )
    print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
    print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.

    cmd_up = [*base_cmd, "up", "-d"]

    try:
        result_up = subprocess.run(
            cmd_up, capture_output=True, text=True, timeout=20, env=compose_env
        )
        if result_up.returncode != 0:
            _print_compose_logs(compose_file, project_name, "compose up failed", env=compose_env)
            pytest.fail(
                f"Failed to start container: {result_up.stderr}\nSTDOUT: {result_up.stdout}"
            )

        import time

        time.sleep(1)

        result_inspect = subprocess.run(
            ["docker", "inspect", container_name, "--format={{.State.ExitCode}}"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        exit_code = int(result_inspect.stdout.strip() or "0")

        logs_result = subprocess.run(
            ["docker", "logs", container_name],
            capture_output=True,
            text=True,
            timeout=15,
        )
        print(logs_result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(logs_result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        logs = logs_result.stdout + logs_result.stderr

        assert exit_code == 0, f"Container should continue with warnings; got exit {exit_code}"
        # Wording may vary; ensure a chown-related warning is present and capability name
        assert "chown" in logs.lower()
        assert (
            "cap_chown" in logs.lower() or "cap chown" in logs.lower() or "cap_chown" in logs or "capabilities (chown" in logs.lower()
        )
        assert_has_troubleshooting_url(logs)

    finally:
        result = subprocess.run(
            [*base_cmd, "down", "-v"], capture_output=True, text=True, timeout=30, env=compose_env
        )
        print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
