# NetAlertX Multi-Folder Workspace

This repository uses a multi-folder workspace configuration to provide easy access to runtime directories.

## Opening the Multi-Folder Workspace

After the devcontainer builds, open the workspace file to access all folders:

1. **File** → **Open Workspace from File**
2. Select `NetAlertX.code-workspace`

Or use Command Palette (Ctrl+Shift+P / Cmd+Shift+P):
- Type: `Workspaces: Open Workspace from File`
- Select `NetAlertX.code-workspace`

## Workspace Folders

The workspace includes:
- **NetAlertX** - Main source code
- **/tmp** - Runtime temporary files
- **/tmp/api** - API response cache (JSON files)
- **/tmp/log** - Application and plugin logs

## Testing Configuration

Pytest is configured to only discover tests in the main `test/` directory, not in `/tmp` folders.
