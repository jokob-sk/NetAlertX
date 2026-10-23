"""Check the PHP runtime installed in the Docker test environment."""

import os
import re
import shutil
import subprocess

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("ENVIRONMENT") != "alpine",
    reason="PHP package checks require the Alpine Docker environment",
)


@pytest.mark.parametrize("binary", ["php83", "php-fpm83", "php-cgi83"])
def test_php_security_version(binary):
    """Require the PHP 8.3 security release in every installed SAPI."""
    executable = shutil.which(binary)
    assert executable is not None, f"Missing required PHP binary: {binary}"

    result = subprocess.run(
        [executable, "-v"], capture_output=True, text=True, check=True, timeout=60
    )
    match = re.search(r"PHP (\d+)\.(\d+)\.(\d+)", result.stdout)
    assert match is not None, result.stdout
    version = tuple(int(part) for part in match.groups())
    assert version[:2] == (8, 3), f"Unexpected PHP branch for {binary}: {result.stdout}"
    assert version >= (8, 3, 36), (
        f"{binary} is affected by CVE-2026-109618/CVE-2026-109619: {result.stdout}"
    )
