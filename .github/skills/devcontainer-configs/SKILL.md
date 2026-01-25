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
