import os
import pathlib
import subprocess

import pytest


def _announce(request: pytest.FixtureRequest, message: str) -> None:
    reporter = request.config.pluginmanager.get_plugin("terminalreporter")
    if reporter:  # pragma: no branch - depends on pytest runner
        reporter.write_line(message)
    else:
        print(message)


@pytest.fixture(scope="session", autouse=True)
def build_netalertx_test_image(request: pytest.FixtureRequest) -> None:
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
