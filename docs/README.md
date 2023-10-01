## Documentation overview

In the app hover over settings or fields/labels or click blue in-app ❔ (question-mark) icons to get to relevant documentation pages.

![In-app help](/docs/img/GENERAL/in-app-help.png)

There is also an in-app Help / FAQ section that should be answering frequently asked questions.

### 📥 Installation

 ⚠ Only tested as a [docker container - follow these instructions here](https://github.com/jokob-sk/Pi.Alert/blob/main/dockerfiles/README.md). 
 > Check out [leiweibau's fork](https://github.com/leiweibau/Pi.Alert/) if you want to install Pi.Alert on the server directly or original instructions for [pucherot's original code](https://github.com/pucherot/Pi.Alert/)


### 📚 Table of contents

#### 🐛 Debugging help & tips

- [Debugging tips](/docs/DEBUG_TIPS.md)
- [Invalid JSON errors debug help](/docs/DEBUG_INVALID_JSON.md)

#### 🔝 Popular/Suggested

- [Network treemap configuration](/docs/NETWORK_TREE.md)
- [SMTP server config](/docs/SMTP.md)
- [Subnets and VLANs configuration for arp-scan](/docs/SUBNETS.md)
- [Home Assistant](/docs/HOME_ASSISTANT.md)
- [Bulk edit devices](/docs/DEVICES_BULK_EDITING.md)

#### ⚙ System Management

- [Manage devices (legacy docs)](/docs/DEVICE_MANAGEMENT.md)
- [Random MAC/MAC icon meaning (legacy docs)](/docs/RANDOM_MAC.md)
- [Custom Icons configuration and support](/docs/ICONS.md)

#### 🔎 Examples

- [N8N webhook example](/docs/WEBHOOK_N8N.md)

#### ♻ Misc

- [Version history (legacy)](/docs/VERSIONS_HISTORY.md)
- [Reverse proxy (Nginx, Apache, SWAG)](/docs/REVERSE_PROXY.md)

#### 👩‍💻For Developers👨‍💻

- [APP code structure](/pialert/README.md)
- [Database structure](/docs/DATABASE.md)
- [API endpoints details](/docs/API.md)
- [Plugin system details and how to develop your own](/front/plugins/README.md)
- [Settings system](/docs/SETTINGS_SYSTEM.md)
- [New Version notifications](/docs/VERSIONS.md)
- [Frontend development tips](/docs/FRONTEND_DEVELOPMENT.md)
- [Webhook secrets](/docs/WEBHOOK_SECRET.md)

Feel free to suggest or submit new docs via a PR. 

## 👨‍💻 Development priorities

Priorities from highest to lowest:

* 🔼 Fixing core functionality bugs not solvable with workarounds
* 🔵 New core functionality unlocking other opportunities (e.g.: plugins) 
* 🔵 Refactoring enabling faster implementation of future functionality 
* 🔽 (low) UI functionality & improvements (PRs welcome 😉)

Design philosophy: Focus on core functionality and leverage existing apps and tools to make PiAlert integrate into other workflows. 

Examples: 

    1. Supporting apprise makes more sense than implementing multiple individual notification gateways
    2. Implementing regular expression support across settings for validation makes more sense than validating one setting with a specific expression. 

UI-specific requests are a low priority as the framework picked by the original developer is not very extensible (and afaik doesn't support components) and has limited mobile support. Also, I argue the value proposition is smaller than working on something else.

Feel free to submit PRs if interested. try to **keep the PRs small/on-topic** so they are easier to review and approve. 

That being said, I'd reconsider if more people and or recurring sponsors file a request 😉.

## 🙏 Feature requests

Please be as detailed as possible with **workarounds** you considered and why a native feature is the better way. This gives me better context and will make it more likely to be implemented. Ideally, a feature request should be in the format "I want to be able to do XYZ so that ZYX. I considered these approaches XYZ".

## ➕ Pull requests (PRs)

If you submit a PR please:

1. Check that your changes are backward compatible with existing installations and with a blank setup. 
2. Existing features should always be preserved. 
3. Keep the PR small, on-topic and don't change code that is not necessary for the PR to work
4. New features code should ideally be re-usable for different purposes, not be for a very narrow use-case.
5. New functionality should ideally be implemented via the Plugins system, if possible.

Suggested test cases:

- Blank setup with no DB or config
- Existing DB / config
- Sending a notification (e. g. Delete a device and wait for a scan to run) and testing all notification gateways, especially:
-   Email, Apprise (e.g. via Telegram), webhook (e.g. via Discord), MQTT (e.g. via HomeAssitant)
- Saving settings
- Test a couple of plugins
- Check the Error log for anything unusual

Some additional context:

* Permanent settings/config is stored in the `pialert.conf` file
* Currently temporary (session?) settings are stored in the `Parameters` DB table as key-value pairs. This table is wiped during a container rebuild/restart and its values are re-initialized from cookies/session data from the browser. 

## 🐛 Submitting an issue or bug

Before submitting a new issue please spend a couple of minutes on research:

* Check [🛑 Common issues](https://github.com/jokob-sk/Pi.Alert/tree/main/dockerfiles#-common-issues) 
* Check [💡 Closed issues](https://github.com/jokob-sk/Pi.Alert/issues?q=is%3Aissue+is%3Aclosed) if a similar issue was solved in the past.
* When submitting an issue ❗[enable debug](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/DEBUG_TIPS.md)❗

⚠ Please follow the pre-defined issue template to resolve your issue faster.
