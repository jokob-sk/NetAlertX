# 📖 Documentation Overview

## ℹ️ In-App Help

<details>
  <summary>🔍 How to access in-app help</summary>

  - Hover over settings, fields, or labels.
  - Click the blue ❔ (question-mark) icons.
  - Access the in-app **Help / FAQ** section for frequently asked questions.

  ![In-app help](/docs/img/GENERAL/in-app-help.png)

</details>

---

## 📥 Installation

### 🐳 Docker (Fully Supported)
The recommended installation method is via Docker.  
👉 [Follow the official installation guide](https://github.com/jokob-sk/NetAlertX/blob/main/dockerfiles/README.md).

### 💻 Bare-Metal / On-Server (Experimental)
- 🧪 [(Experimental) On-hardware installation](https://github.com/jokob-sk/NetAlertX/blob/main/docs/HW_INSTALL.md)  
- Alternative bare-metal forks:
  - ✅ [leiweibau's fork](https://github.com/leiweibau/Pi.Alert/) (maintained)
  - ❌ [pucherot's original code](https://github.com/pucherot/Pi.Alert/) (unmaintained)

---

## 📚 Table of Contents

### ⚙ Initial Setup
- [Getting Started & Configuration](/docs/INITIAL_SETUP.md)
- [Synology Guide](/docs/SYNOLOGY_GUIDE.md)
- [Subnets & VLANs Configuration](/docs/SUBNETS.md)
- [Scanning Remote Networks](/docs/REMOTE_NETWORKS.md)
- [SMTP Server Configuration](/docs/SMTP.md)
- [Custom Icons Setup](/docs/ICONS.md)
- [Notifications Setup](/docs/NOTIFICATIONS.md)
- [Reverse DNS Name Resolution](/docs/REVERSE_DNS.md)
- [Network Treemap Configuration](/docs/NETWORK_TREE.md)
- [Backups & Data Retention](/docs/BACKUPS.md)
- [Plugins Overview](/front/plugins/README.md)

### 🐛 Debugging & Troubleshooting
- [General Debugging Tips](/docs/DEBUG_TIPS.md)
- [UI Not Showing Debug](/docs/WEB_UI_PORT_DEBUG.md)
- [Invalid JSON Errors](/docs/DEBUG_INVALID_JSON.md)
- [Plugin Troubleshooting](/docs/DEBUG_PLUGINS.md)
- [File Permissions Issues](/docs/FILE_PERMISSIONS.md)
- [Performance Optimization](/docs/PERFORMANCE.md)

### 🔝 Popular & Suggested Guides
- [Home Assistant Integration](/docs/HOME_ASSISTANT.md)
- [Bulk Device Editing](/docs/DEVICES_BULK_EDITING.md)

### ⚙ System Management
- [Device Management (Legacy Docs)](/docs/DEVICE_MANAGEMENT.md)
- [Random MAC & MAC Icon Meaning](/docs/RANDOM_MAC.md)

### 🔎 Practical Examples
- [N8N Webhook Integration](/docs/WEBHOOK_N8N.md)

### 🔄 Miscellaneous
- [Version History (Legacy)](/docs/VERSIONS_HISTORY.md)
- [Reverse Proxy Setup (Nginx, Apache, SWAG)](/docs/REVERSE_PROXY.md)
- [Updating the Application](/docs/UPDATES.md)
- [Authelia Setup (Draft)](/docs/AUTHELIA.md)

### 👩‍💻 For Developers
- [Developer Environment Setup](/docs/DEV_ENV_SETUP.md)
- [Server Code Structure](/server/README.md)
- [Database Schema & Details](/docs/DATABASE.md)
- [API Endpoints Overview](/docs/API.md)
- [Plugin Development Guide](/docs/PLUGINS_DEV.md)
- [Settings System Details](/docs/SETTINGS_SYSTEM.md)
- [Version Update Notifications](/docs/VERSIONS.md)
- [Frontend Development Notes](/docs/FRONTEND_DEVELOPMENT.md)
- [Webhook Secret Handling](/docs/WEBHOOK_SECRET.md)

---

## 👨‍💻 Development Priorities

**Priority Order (Highest to Lowest):**
1. 🔼 Fixing core bugs that lack workarounds.
2. 🔵 Adding core functionality that unlocks other features (e.g., plugins).
3. 🔵 Refactoring to enable faster development.
4. 🔽 UI improvements (PRs welcome).

💡 **Design Philosophy:**  
Focus on core functionality and integrate with existing tools rather than reinventing the wheel.  
Examples:
- Using **Apprise** for notifications instead of implementing multiple separate gateways.
- Implementing **regex-based validation** instead of one-off validation for each setting.

📌 **Note on UI requests:**  
UI changes have lower priority due to framework limitations and mobile support constraints.  
PRs are welcome, but **keep them small & focused**.

---

## 🙏 Feature Requests

Please include:
- The **goal** (e.g., *"I want to do X so that Y..."*).
- Workarounds you've tried.
- Why a built-in feature is the better solution.

Example format:
> *I want to be able to do XYZ so that ZYX. I considered these approaches XYZ, but they have these limitations...*

---

## ➕ Contributing & Pull Requests

**Before submitting a PR, please ensure:**
✔ Changes are **backward-compatible** with existing installs.  
✔ No unnecessary changes are made.  
✔ New features are **reusable**, not narrowly scoped.  
✔ Features are implemented via **plugins** if possible.  

### ✅ Suggested Test Cases
- Fresh install (no DB/config).
- Existing DB/config compatibility.
- Notification testing:
  - 📧 Email  
  - 🔔 Apprise (e.g., Telegram)  
  - 🌐 Webhook (e.g., Discord)  
  - 📡 MQTT (e.g., Home Assistant)  
- Settings persistence.
- Plugin functionality.
- Error log inspection.

### 🔎 Important Notes:
- **Persistent settings** are stored in `app.conf`.
- **Session-based settings** are stored in the `Parameters` DB table and reset on container restart.

---

## 🐛 Reporting Bugs

Before opening an issue:
- 🔍 [Check common issues](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_TIPS.md#common-issues).
- 📌 [Look at closed issues](https://github.com/jokob-sk/NetAlertX/issues?q=is%3Aissue+is%3Aclosed).
- ⚠ **Enable debugging** before reporting: [Debug Guide](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEBUG_TIPS.md).

❗ **Follow the issue template** for faster resolution.
