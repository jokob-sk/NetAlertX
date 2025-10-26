# Metrics API Endpoint

The `/metrics` endpoint exposes **Prometheus-compatible metrics** for NetAlertX, including aggregate device counts and per-device status.

---

## Endpoint Details

* **GET** `/metrics` → Returns metrics in plain text.
* **Host**: NetAlertX server
* **Port**: As configured in `GRAPHQL_PORT` (default: `20212`)

---

## Example Output

```text
netalertx_connected_devices 31
netalertx_offline_devices 54
netalertx_down_devices 0
netalertx_new_devices 0
netalertx_archived_devices 31
netalertx_favorite_devices 2
netalertx_my_devices 54

netalertx_device_status{device="Net - Huawei", mac="Internet", ip="1111.111.111.111", vendor="None", first_connection="2021-01-01 00:00:00", last_connection="2025-08-04 17:57:00", dev_type="Router", device_status="Online"} 1
netalertx_device_status{device="Net - USG", mac="74:ac:74:ac:74:ac", ip="192.168.1.1", vendor="Ubiquiti Networks Inc.", first_connection="2022-02-12 22:05:00", last_connection="2025-06-07 08:16:49", dev_type="Firewall", device_status="Archived"} 1
netalertx_device_status{device="Raspberry Pi 4 LAN", mac="74:ac:74:ac:74:74", ip="192.168.1.9", vendor="Raspberry Pi Trading Ltd", first_connection="2022-02-12 22:05:00", last_connection="2025-08-04 17:57:00", dev_type="Singleboard Computer (SBC)", device_status="Online"} 1
...
```

---

## Metrics Overview

### 1. Aggregate Device Counts

| Metric                        | Description                              |
| ----------------------------- | ---------------------------------------- |
| `netalertx_connected_devices` | Devices currently connected              |
| `netalertx_offline_devices`   | Devices currently offline                |
| `netalertx_down_devices`      | Down/unreachable devices                 |
| `netalertx_new_devices`       | Recently detected devices                |
| `netalertx_archived_devices`  | Archived devices                         |
| `netalertx_favorite_devices`  | User-marked favorites                    |
| `netalertx_my_devices`        | Devices associated with the current user |

---

### 2. Per-Device Status

Metric: `netalertx_device_status`
Each device has labels:

* `device`: friendly name
* `mac`: MAC address (or placeholder)
* `ip`: last recorded IP
* `vendor`: manufacturer or "None"
* `first_connection`: timestamp of first detection
* `last_connection`: most recent contact
* `dev_type`: device type/category
* `device_status`: current status (`Online`, `Offline`, `Archived`, `Down`, …)

Metric value is always `1` (presence indicator).

---

## Querying with `curl`

```sh
curl 'http://<server_ip>:<GRAPHQL_PORT>/metrics' \
  -H 'Authorization: Bearer <API_TOKEN>' \
  -H 'Accept: text/plain'
```

Replace placeholders:

* `<server_ip>` – NetAlertX host IP/hostname
* `<GRAPHQL_PORT>` – configured port (default `20212`)
* `<API_TOKEN>` – your API token

---

## Prometheus Scraping Configuration

```yaml
scrape_configs:
  - job_name: 'netalertx'
    metrics_path: /metrics
    scheme: http
    scrape_interval: 60s
    static_configs:
      - targets: ['<server_ip>:<GRAPHQL_PORT>']
    authorization:
      type: Bearer
      credentials: <API_TOKEN>
```

---

## Grafana Dashboard Template

Sample template JSON: [Download](./samples/API/Grafana_Dashboard.json)
