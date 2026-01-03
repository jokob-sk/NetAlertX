"""PUID/PGID runtime user support tests.

These tests exercise the root-priming entrypoint (/root-entrypoint.sh).
They run in NETALERTX_CHECK_ONLY mode to avoid starting long-running services.
"""

from __future__ import annotations

import os
import subprocess
import uuid

import pytest


IMAGE = os.environ.get("NETALERTX_TEST_IMAGE", "netalertx-test")

pytestmark = [pytest.mark.docker]


def _run_root_entrypoint(
    *,
    env: dict[str, str] | None = None,
    volumes: list[str] | None = None,
    extra_args: list[str] | None = None,
    add_chown_cap: bool = True,
    user: str | None = None,
) -> subprocess.CompletedProcess[str]:
    name = f"netalertx-test-puidpgid-{uuid.uuid4().hex[:8]}".lower()

    cmd = [
        "docker",
        "run",
        "--rm",
        "--cap-drop",
        "ALL",
        "--name",
        name,
        "--network",
        "host",
    ]

    if add_chown_cap:
        cmd.extend(["--cap-add", "CHOWN"])

    cmd.extend([
        "--cap-add",
        "NET_RAW",
        "--cap-add",
        "NET_ADMIN",
        "--cap-add",
        "NET_BIND_SERVICE",
        "--cap-add",
        "SETUID",
        "--cap-add",
        "SETGID",
        "--tmpfs",
        "/tmp:mode=777",
        "-e",
        "NETALERTX_CHECK_ONLY=1",
    ])

    if extra_args:
        cmd.extend(extra_args)

    if user:
        cmd.extend(["--user", user])

    if volumes:
        for volume in volumes:
            cmd.extend(["-v", volume])

    if env:
        for key, value in env.items():
            cmd.extend(["-e", f"{key}={value}"])

    cmd.extend(["--entrypoint", "/root-entrypoint.sh"])
    cmd.append(IMAGE)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
    print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
    return result


@pytest.mark.feature_complete
def test_default_puid_pgid_ok() -> None:
    result = _run_root_entrypoint(env={"SKIP_TESTS": "1"})
    assert result.returncode == 0, result.stderr


@pytest.mark.feature_complete
@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"PUID": "0;rm -rf /", "PGID": "1000"}, "invalid characters"),
        ({"PUID": "$(id)", "PGID": "1000"}, "invalid characters"),
        ({"PUID": "-1", "PGID": "1000"}, "invalid characters"),
    ],
)
def test_invalid_puid_pgid_rejected(env: dict[str, str], expected: str) -> None:
    env = {**env}
    env.pop("SKIP_TESTS", None)
    result = _run_root_entrypoint(env=env)
    combined = (result.stdout or "") + (result.stderr or "")
    assert result.returncode != 0

    if expected == "invalid characters":
        assert any(token in combined for token in ("invalid characters", "invalid", "non-numeric")), (
            f"Expected an invalid-puid message variant in output, got: {combined}"
        )
    else:
        assert expected in combined


@pytest.mark.feature_complete
def test_legacy_user_mode_skips_puid_pgid() -> None:
    result = _run_root_entrypoint(
        env={"PUID": "1000", "PGID": "1000"},
        user="20211:20211",
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0
    # Accept flexible phrasing but ensure intent is present
    assert (
        ("PUID/PGID" in combined and "will not be applied" in combined) or ("continuing as current user" in combined.lower())
    )


@pytest.mark.feature_complete
def test_synology_like_fresh_volume_is_primed() -> None:
    """Simulate a fresh named volume that is root-owned and missing copy-up content."""

    volume = f"nax_test_data_{uuid.uuid4().hex[:8]}".lower()

    try:
        result = subprocess.run(["docker", "volume", "create", volume], check=True, capture_output=True, text=True, timeout=15)
        print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.

        # Seed volume with root-owned dirs/files similar to Synology behavior.
        seed_cmd = (
            "mkdir -p /data/config /data/db && "
            "touch /data/config/app.conf /data/db/app.db && "
            "chown -R 0:0 /data && chmod -R 0755 /data && "
            "chmod 0644 /data/config/app.conf /data/db/app.db"
        )
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--userns",
                "host",
                "--user",
                "0:0",
                "-v",
                f"{volume}:/data",
                "--entrypoint",
                "/bin/sh",
                "alpine:3.22",
                "-c",
                seed_cmd,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.

        # Run NetAlertX in priming mode targeting 1000:1000.
        result = _run_root_entrypoint(
            env={"PUID": "1000", "PGID": "1000", "SKIP_TESTS": "1"},
            volumes=[f"{volume}:/data"],
        )
        assert result.returncode == 0, (result.stdout + result.stderr)

        # Verify volume ownership flipped.
        stat_cmd = "stat -c '%u:%g' /data /data/config /data/db"
        stat_proc = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--userns",
                "host",
                "--user",
                "0:0",
                "-v",
                f"{volume}:/data",
                "--entrypoint",
                "/bin/sh",
                "alpine:3.22",
                "-c",
                stat_cmd,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(stat_proc.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(stat_proc.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        lines = [line.strip() for line in (stat_proc.stdout or "").splitlines() if line.strip()]
        assert lines and all(line == "1000:1000" for line in lines), lines

    finally:
        result = subprocess.run(["docker", "volume", "rm", "-f", volume], check=False, capture_output=True, text=True, timeout=15)
        print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.


@pytest.mark.feature_complete
def test_missing_cap_chown_fails_priming() -> None:
    """Verify that priming fails when CAP_CHOWN is missing and ownership change is needed."""

    volume = f"nax_test_data_nochown_{uuid.uuid4().hex[:8]}".lower()

    try:
        result = subprocess.run(["docker", "volume", "create", volume], check=True, capture_output=True, text=True, timeout=15)
        print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.

        # Seed volume with UID 1000 ownership (simulating existing data or host mount)
        seed_cmd = (
            "mkdir -p /data/config /data/db && "
            "touch /data/config/app.conf /data/db/app.db && "
            "chown -R 1000:1000 /data && chmod -R 0755 /data"
        )
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--userns",
                "host",
                "--user",
                "0:0",
                "-v",
                f"{volume}:/data",
                "--entrypoint",
                "/bin/sh",
                "alpine:3.22",
                "-c",
                seed_cmd,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.

        # Run NetAlertX with PUID 20212 (default) but WITHOUT CAP_CHOWN.
        # It should warn but continue running.
        result = _run_root_entrypoint(
            env={"PUID": "20212", "PGID": "20212", "SKIP_TESTS": "1"},
            volumes=[f"{volume}:/data"],
            add_chown_cap=False,
        )

        combined = (result.stdout or "") + (result.stderr or "")
        assert result.returncode == 0, "Container should continue with warnings when CAP_CHOWN is absent"
        assert (
            "chown" in combined.lower() or "permission denied" in combined.lower() or "failed to chown" in combined.lower()
        )
        assert (
            "missing-capabilities" in combined or "docs/docker-troubleshooting/missing-capabilities.md" in combined or "permission denied" in combined.lower()
        )

    finally:
        result = subprocess.run(["docker", "volume", "rm", "-f", volume], check=False, capture_output=True, text=True, timeout=15)
        print(result.stdout)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
        print(result.stderr)  # DO NOT REMOVE OR MODIFY - MANDATORY LOGGING FOR DEBUGGING & CI.
