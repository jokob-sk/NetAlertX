import os
import pathlib
import subprocess
import shutil

import pytest


def _announce(request: pytest.FixtureRequest, message: str) -> None:
    reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    if reporter:  # pragma: no branch - depends on pytest runner
        reporter.write_line(message)
    else:
        print(message)


def _clean_test_mounts(project_root: pathlib.Path) -> None:
    """Clean up the test_mounts directory, handling root-owned files via Docker."""
    mounts_dir = project_root / "test_mounts"
    if not mounts_dir.exists():
        return

    # Try python removal first (faster)
    try:
        shutil.rmtree(mounts_dir)
    except PermissionError:
        # Fallback to docker for root-owned files
        # We mount the parent directory to delete the directory itself
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{project_root}:/work",
            "alpine:3.22",
            "rm", "-rf", "/work/test_mounts"
        ]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )


@pytest.fixture(scope="session")
def cleanup_artifacts(request: pytest.FixtureRequest) -> None:
    """Ensure test artifacts are cleaned up before and after the session."""
    project_root = pathlib.Path(__file__).resolve().parents[2]

    _announce(request, "[docker-tests] Cleaning up previous test artifacts...")
    _clean_test_mounts(project_root)

    yield

    _announce(request, "[docker-tests] Cleaning up test artifacts...")
    _clean_test_mounts(project_root)


@pytest.fixture(scope="session", autouse=True)
def build_netalertx_test_image(request: pytest.FixtureRequest, cleanup_artifacts: None) -> None:
    """Build the docker test image before running any docker-based tests."""

    image = os.environ.get("NETALERTX_TEST_IMAGE", "netalertx-test")

    project_root = pathlib.Path(__file__).resolve().parents[2]

    cmd = [
        "docker",
        "buildx",
        "build",
        "--load",
        "-t",
        image,
        ".",
    ]

    _announce(request, f"[docker-tests] Building test image '{image}' using docker buildx")

    env = os.environ.copy()
    env.setdefault("DOCKER_BUILDKIT", "1")

    result = subprocess.run(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        env=env,
    )

    if result.returncode != 0:
        _announce(request, f"[docker-tests] docker buildx failed for '{image}'")
        pytest.fail(
            "Docker buildx failed before running docker tests.\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    _announce(request, f"[docker-tests] docker buildx completed for '{image}'")
