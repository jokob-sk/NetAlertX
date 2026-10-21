## Overview

Imports connected devices from an OpenWRT router via its LuCI RPC API.

### Usage

- Point the plugin at your router's address and a login with access to LuCI RPC. A read-only user is recommended over using your admin account.
- If your router uses a self-signed HTTPS certificate, you'll need to disable certificate verification for the import to succeed. Disabling verification means the plugin can no longer confirm it's actually talking to your router, letting a network attacker impersonate it and capture your login credentials - prefer installing a certificate from a trusted CA on the router. If that isn't possible, only do this on a trusted network, and use a read-only account rather than admin.

### Other info

- Version: 1.0
- Author: [vaga9938](https://github.com/vaga9938)
- Release Date: 28-Dec-2024
