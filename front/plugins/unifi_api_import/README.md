## Overview

Unifi import plugin using the Site Manager API.

> [!TIP]
> The Site Manager API doesn't seems to have feature parity with the old API yet, so certain limitations apply.  

### Quick setup guide

Navigate to your UniFi Site Manager _Settings -> Control Plane -> Integrations_.

- `UNIFIAPI_api_key` : You can generate your API key under the _Your API Keys_ section.
- `UNIFIAPI_base_url` : You can find your base url in the _API Request Format_ section, e.g. `https://192.168.100.1/proxy/network/integration/`
- `UNIFIAPI_api_version` : You can find your version as part of the url in the _API Request Format_ section, e.g. `v1`
- `UNIFIAPI_verify_ssl` : To skip SSL with you don't have an SSL certificate

### Usage

- Head to **Settings** > **Plugin name** to adjust the default values.

### Notes

- Version: 1.0.0
- Author: `jokob-sk`
- Release Date: `Aug 2025`