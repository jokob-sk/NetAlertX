#!/usr/bin/env python3
"""
Flag PRs that add a system package (root Dockerfile) or a Python dependency
(root requirements.txt) without touching the sibling build targets that also
need it. See docs/PLUGINS_DEV.md#conventions-checklist and the
plugin-review skill's "a new dependency has to reach every build target"
check - a package added only to the Alpine Dockerfile leaves Dockerfile.debian
(a separately-maintained apt-based target, docs/BUILDS.md) without it, and a
Python package added only to the root requirements.txt may still be needed by
install/ubuntu24 or install/proxmox's own non-Docker install methods.

This can't know whether a given package is actually needed on the other
target (a real difference is legitimate and common), only that the PR didn't
touch the sibling file at all - a signal worth a human glance, not a
mechanical verdict. Exit non-zero (the CI step calling this is non-blocking).

    python3 scripts/check_dependency_mirroring.py origin/main
"""

import subprocess
import sys

GROUPS = [
    ["Dockerfile", "Dockerfile.debian"],
    ["requirements.txt", "install/ubuntu24/requirements.txt", "install/proxmox/requirements.txt"],
]


def changed_files(base_ref):
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        capture_output=True, text=True, check=True,
    )
    return set(result.stdout.splitlines())


def main():
    if len(sys.argv) != 2:
        print("usage: check_dependency_mirroring.py <base-ref>", file=sys.stderr)
        return 2

    changed = changed_files(sys.argv[1])
    problems = []
    for group in GROUPS:
        touched = [path for path in group if path in changed]
        untouched = [path for path in group if path not in changed]
        if touched and untouched:
            problems.append(
                f"- touched {', '.join(touched)} but not {', '.join(untouched)}."
            )

    if problems:
        print("Possible dependency-mirroring gap (a new package may need the other file(s) too):")
        print("\n".join(problems))
        print("\nIf the change is genuinely target-specific (e.g. a Debian-only fix, or a "
              "dependency only the Docker build needs), ignore this. Otherwise check whether "
              "the other file(s) need the same package - see "
              "docs/PLUGINS_DEV.md#conventions-checklist.")
        return 1

    print("No dependency-mirroring gap detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
