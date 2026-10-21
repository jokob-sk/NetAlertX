---
name: mcp-activation
description: Enables live interaction with the NetAlertX runtime. This skill configures the Model Context Protocol (MCP) connection, granting full API access for debugging, troubleshooting, and real-time operations including database queries, network scans, and device management.
---

# MCP Activation Skill

This skill configures the environment to expose the Model Context Protocol (MCP) server to AI agents running inside the devcontainer.

## Prerequisites

1. **Devcontainer connected:** You must be working inside the NetAlertX devcontainer.
2. **Backend running:** The Python backend must be running — it generates `app.conf` containing the API token. Use the `devcontainer-services` skill if it's not running.

## Usage

This skill assumes you are already running within the NetAlertX devcontainer.

1.  **Generate Configurations:**
    Run the configuration generation script to extract the API Token and update the VS Code MCP settings.

    ```bash
    /workspaces/NetAlertX/.devcontainer/scripts/generate-configs.sh
    ```

2.  **Reload Window:**
    Request the user to reload the VS Code window to activate the new tools.
    > I have generated the MCP configuration. Please run the **'Developer: Reload Window'** command to activate the MCP server tools.
    > In VS Code: open the Command Palette (Windows/Linux: Ctrl+Shift+P, macOS: Cmd+Shift+P), type Developer: Reload Window, press Enter — or click the Reload button if a notification appears. 🔁
    > After you reload, tell me “Window reloaded” (or just “reloaded”) and I’ll continue.


## Why use this?

Access the live runtime API to perform operations that are not possible through static file analysis:
- **Query the database**
- **Trigger network scans**
- **Manage devices and events**
- **Troubleshoot real-time system state**
