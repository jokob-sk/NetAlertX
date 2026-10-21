---
name: netalertx-install-scripts
description: Read before editing anything under install/ (production-filesystem/, ubuntu24/, etc.) or reviewing a PR that touches it. Covers uninstall safety, why check-*.sh scripts don't all exit the same way, and what's legacy vs. active.
---

# Install Scripts

Conventions mined from real review comments on `install/*` PRs (#1214, #1230, #1235) — not derived from reading the scripts alone, so check current behavior before relying on any of these if the surrounding code has since changed.

## Uninstall safety

`install/*/uninstall.sh` must only remove NetAlertX's own files (`/app` and its own data) — never touch system packages it depends on (PHP, nginx, avahi, etc.) or other shared system components. A hardware/bare-metal install shares the host with other software; removing a system package on uninstall can break things NetAlertX didn't install.

## `check-*.sh` scripts don't all exit the same way — by design

`install/production-filesystem/services/scripts/check-*.sh` scripts are **not uniform** in whether a failure is fatal:
- Some are fail-fast on purpose: `check-first-run-config.sh` exits non-zero on a critical failure (can't create the config dir, can't copy default config) so the container doesn't start in a broken state.
- Some are warning-only on purpose: `check-ramdisk.sh` exits 0 even when it detects a real issue, letting the app start anyway with suboptimal config.

Don't assume one check's exit-code convention applies to another — check what that specific script is actually guarding before suggesting a change to its exit behavior.

## `/back` is legacy, not the active code path

`back/cron_script.sh` (and the rest of `/back`) is legacy, kept only for compatibility with older/external components. The active, maintained version is `install/production-filesystem/services/scripts/cron_script.sh`. Changes to `/back` are out of scope for most PRs unless the PR is specifically about compatibility with whatever still depends on it.

## Build-time vs. runtime, and generated files

See the `devcontainer-configs`/`devcontainer-management` skills for the Dockerfile-generation and build-vs-runtime-file-availability rules — the same "source files aren't present at Docker build time" constraint applies to `install/production-filesystem/build/*` scripts, not just the devcontainer image.
