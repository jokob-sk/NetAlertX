import subprocess


def test_run_docker_compose_returns_output(monkeypatch, tmp_path):
    """Unit test that verifies `_run_docker_compose` returns a CompletedProcess
    instance with an `output` attribute (combined stdout+stderr). This uses
    monkeypatched subprocess.run to avoid invoking Docker.
    """
    from test.docker_tests import test_docker_compose_scenarios as mod

    # Prepare a dummy compose file path
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services: {}")

    # Prepare a sequence of CompletedProcess objects to be returned by fake `run`
    cps = [
        subprocess.CompletedProcess([], 0, stdout="down-initial\n", stderr=""),
        subprocess.CompletedProcess(["up"], 0, stdout="up-out\n", stderr=""),
        subprocess.CompletedProcess(["logs"], 0, stdout="log-out\n", stderr=""),
        # ps_proc: return valid container entries
        subprocess.CompletedProcess(["ps"], 0, stdout="test-container Running 0\n", stderr=""),
        subprocess.CompletedProcess([], 0, stdout="down-final\n", stderr=""),
    ]

    def fake_run(*_, **__):
        try:
            return cps.pop(0)
        except IndexError:
            # Safety: return a harmless CompletedProcess
            return subprocess.CompletedProcess([], 0, stdout="", stderr="")

    # Monkeypatch subprocess.run used inside the module
    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    # Call under test
    result = mod._run_docker_compose(compose_file, "proj-test", timeout=1, detached=False)

    # The returned object must have the combined `output` attribute
    assert hasattr(result, "output")
    assert "up-out" in result.output
    assert "log-out" in result.output
