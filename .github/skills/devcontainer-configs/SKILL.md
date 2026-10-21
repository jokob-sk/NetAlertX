---
name: netalertx-devcontainer-configs
description: Generate devcontainer configuration files. Use this when asked to generate devcontainer configs, update devcontainer template, or regenerate devcontainer.
---

# Devcontainer Config Generation

Generates devcontainer configs from the template. Must be run after changes to devcontainer configuration.

## Command

```bash
/workspaces/NetAlertX/.devcontainer/scripts/generate-configs.sh
```

## What It Does

Combines and merges template configurations into the final config used by VS Code.

## When to Run

- After modifying `.devcontainer/` template files
- After changing devcontainer features or settings
- Before committing devcontainer changes

## Note

This affects only the devcontainer configuration. It has no bearing on the production or test Docker image.

## Dockerfile Generation (separate from the config generation above)

`.devcontainer/Dockerfile` is itself a **generated file** — `generate-dockerfile.sh` combines the root `Dockerfile` with `.devcontainer/resources/devcontainer-Dockerfile`. Never review or edit `.devcontainer/Dockerfile` directly; dependency/build-step changes belong in the root `Dockerfile`, regenerate after.

Two build-time gotchas that have caused real review confusion:
- **Source repo files are not available during the Docker build phase** — they're mounted into the container after it starts. A `COPY` referencing a source file will fail at build time; config that depends on repo content has to be handled at runtime (a setup script), not a build step.
- Under modern BuildKit, `COPY` with a glob pattern that matches nothing (e.g. `.[V]ERSION`) succeeds silently — copies nothing, doesn't fail the build. Don't assume a missing optional file will surface as a build error.
