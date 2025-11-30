#!/usr/bin/env python3
"""
Pytest-based Mount Diagnostic Tests for NetAlertX

Tests all possible mount configurations for each path to validate the diagnostic tool.
Uses pytest framework for proper test discovery and execution.

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


@dataclass
class MountTableRow:
    """Represents a parsed row from the mount diagnostic table."""

    path: str
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
        if len(parts) < 6:
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
                writeable=emoji_to_bool(parts[1]),
                mount=emoji_to_bool(parts[2]),
                ramdisk=emoji_to_bool(parts[3]),
                performance=emoji_to_bool(parts[4]),
                dataloss=emoji_to_bool(parts[5]),
            )
            rows.append(row)
        except (IndexError, ValueError):
            continue

    return rows


def assert_table_row(
    output: str,
    expected_path: str,
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
    assert len(raw_parts) >= 6, f"Malformed table row for '{expected_path}': {raw_line}"

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

    _check("writeable", writeable, matching_row.writeable, 1)
    _check("mount", mount, matching_row.mount, 2)
    _check("ramdisk", ramdisk, matching_row.ramdisk, 3)
    _check("performance", performance, matching_row.performance, 4)
    _check("dataloss", dataloss, matching_row.dataloss, 5)

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
    result = subprocess.run(
        ["docker", "images", "-q", image_name], capture_output=True, text=True
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

            # Determine expected exit code
            expected_exit_code = 1 if expected_issues else 0

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
    print(
        "Note: If this output feels too large for your context window, redirect it to a file and read it back instead of deleting it."
    )
    print(result.stdout or "<no stdout>")
    if result.stderr:
        print("--- logs stderr ---")
        print(result.stderr)
    print("=== end docker compose logs ===\n")


def validate_scenario_table_output(output: str, test_scenario: TestScenario) -> None:
    """Validate the diagnostic table for scenarios that should report issues."""

    if not test_scenario.expected_issues:
        return

    try:
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
                elif test_scenario.name == "active_config_no-mount":
                    assert_table_row(
                        output,
                        CONTAINER_PATHS["active_config"],
                        mount=True,
                        ramdisk=True,
                        performance=True,
                        dataloss=True,
                    )
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
    subprocess.run(
        base_cmd + ["down", "-v"], capture_output=True, timeout=30, env=compose_env
    )

    cmd_up = base_cmd + ["up", "-d"]

    try:
        result_up = subprocess.run(
            cmd_up, capture_output=True, text=True, timeout=20, env=compose_env
        )
        if result_up.returncode != 0:
            ensure_logs("compose up failed")
            pytest.fail(
                f"Failed to start container: {result_up.stderr}\n"
                f"STDOUT: {result_up.stdout}"
            )

        # Wait for container to be ready
        import time

        time.sleep(1)

        # Check if container is still running
        container_name = f"netalertx-test-mount-{test_scenario.name}"
        result_ps = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={container_name}"],
            capture_output=True,
            text=True,
        )

        if not result_ps.stdout.strip():
            # Container exited - check the exit code
            result_inspect = subprocess.run(
                ["docker", "inspect", container_name, "--format={{.State.ExitCode}}"],
                capture_output=True,
                text=True,
            )
            actual_exit_code = int(result_inspect.stdout.strip())

            # Assert the exit code matches expected
            if actual_exit_code != test_scenario.expected_exit_code:
                ensure_logs("unexpected exit code")
                pytest.fail(
                    f"Container {container_name} exited with code {actual_exit_code}, "
                    f"expected {test_scenario.expected_exit_code}"
                )
            # Check the logs to see if it detected the expected issues
            result_logs = subprocess.run(
                ["docker", "logs", container_name], capture_output=True, text=True
            )

            logs = result_logs.stdout + result_logs.stderr

            if test_scenario.expected_issues:
                validate_scenario_table_output(logs, test_scenario)

            return  # Test passed - container correctly detected issues and exited

        # Container is still running - run diagnostic tool
        cmd_exec = [
            "docker",
            "exec",
            "--user",
            "netalertx",
            container_name,
            "python3",
            "/entrypoint.d/10-mounts.py",
        ]
        result_exec = subprocess.run(
            cmd_exec, capture_output=True, text=True, timeout=30
        )
        diagnostic_output = result_exec.stdout + result_exec.stderr

        # The diagnostic tool returns 1 for unwritable paths except active_config, which only warns
        if (test_scenario.name.startswith("active_config_") and "unwritable" in test_scenario.name):
            expected_tool_exit = 0
        elif "unwritable" in test_scenario.name:
            expected_tool_exit = 1
        else:
            expected_tool_exit = 0

        if result_exec.returncode != expected_tool_exit:
            ensure_logs("diagnostic exit code mismatch")
            pytest.fail(
                f"Diagnostic tool failed (expected {expected_tool_exit}, got {result_exec.returncode}): {result_exec.stderr}"
            )

        if test_scenario.expected_issues:
            validate_scenario_table_output(diagnostic_output, test_scenario)
            assert "⚠️" in diagnostic_output, (
                f"Issue scenario {test_scenario.name} should include a warning symbol, got: {result_exec.stderr}"
            )
        else:
            # Should have table output but no warning message
            assert "Path" in result_exec.stdout, (
                f"Good config {test_scenario.name} should show table, got: {result_exec.stdout}"
            )
            assert "⚠️" not in diagnostic_output, (
                f"Good config {test_scenario.name} should not show warning, got stderr: {result_exec.stderr}"
            )
        return  # Test passed - diagnostic output validated

    finally:
        # Stop container
        subprocess.run(
            base_cmd + ["down", "-v"], capture_output=True, timeout=30, env=compose_env
        )


def test_table_parsing():
    """Test the table parsing and assertion functions."""

    sample_output = """
 Path                | Writeable | Mount | RAMDisk | Performance | DataLoss
---------------------+-----------+-------+---------+-------------+----------
/data/db            |     ✅    |   ❌  |    ➖   |      ➖     |    ❌
/tmp/api            |     ✅    |   ✅  |    ✅   |      ✅     |    ✅
"""

    # Test parsing
    rows = parse_mount_table(sample_output)
    assert len(rows) == 2

    # Test assertions
    assert_table_row(
        sample_output,
        "/data/db",
        writeable=True,
        mount=False,
        ramdisk=None,
        performance=None,
        dataloss=False,
    )
    assert_table_row(
        sample_output,
        CONTAINER_PATHS["api"],
        writeable=True,
        mount=True,
        ramdisk=True,
        performance=True,
        dataloss=True,
    )
