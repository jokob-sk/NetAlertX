# Net Tools API Endpoints

The Net Tools API provides **network diagnostic utilities**, including Wake-on-LAN, traceroute, speed testing, DNS resolution, nmap scanning, and internet connection information.

All endpoints require **authorization** via Bearer token.

---

## Endpoints

### 1. Wake-on-LAN

* **POST** `/nettools/wakeonlan`
  Sends a Wake-on-LAN packet to wake a device.

**Request Body** (JSON):

```json
{
  "devMac": "AA:BB:CC:DD:EE:FF"
}
```

**Response** (success):

```json
{
  "success": true,
  "message": "WOL packet sent",
  "output": "Sent magic packet to AA:BB:CC:DD:EE:FF"
}
```

**Error Responses**:

* Invalid MAC address → HTTP 400
* Command failure → HTTP 500

---

### 2. Traceroute

* **POST** `/nettools/traceroute`
  Performs a traceroute to a specified IP address.

**Request Body**:

```json
{
  "devLastIP": "192.168.1.1"
}
```

**Response** (success):

```json
{
  "success": true,
  "output": "traceroute output as string"
}
```

**Error Responses**:

* Invalid IP → HTTP 400
* Traceroute command failure → HTTP 500

---

### 3. Speedtest

* **GET** `/nettools/speedtest`
  Runs an internet speed test using `speedtest-cli`.

**Response** (success):

```json
{
  "success": true,
  "output": [
    "Ping: 15 ms",
    "Download: 120.5 Mbit/s",
    "Upload: 22.4 Mbit/s"
  ]
}
```

**Error Responses**:

* Command failure → HTTP 500

---

### 4. DNS Lookup (nslookup)

* **POST** `/nettools/nslookup`
  Resolves an IP address or hostname using `nslookup`.

**Request Body**:

```json
{
  "devLastIP": "8.8.8.8"
}
```

**Response** (success):

```json
{
  "success": true,
  "output": [
    "Server: 8.8.8.8",
    "Address: 8.8.8.8#53",
    "Name: google-public-dns-a.google.com"
  ]
}
```

**Error Responses**:

* Missing or invalid `devLastIP` → HTTP 400
* Command failure → HTTP 500

---

### 5. Nmap Scan

* **POST** `/nettools/nmap`
  Runs an nmap scan on a target IP address or range.

**Request Body**:

```json
{
  "scan": "192.168.1.0/24",
  "mode": "fast"
}
```

**Supported Modes**:

| Mode            | nmap Arguments |
| --------------- | -------------- |
| `fast`          | `-F`           |
| `normal`        | default        |
| `detail`        | `-A`           |
| `skipdiscovery` | `-Pn`          |

**Response** (success):

```json
{
  "success": true,
  "mode": "fast",
  "ip": "192.168.1.0/24",
  "output": [
    "Starting Nmap 7.91",
    "Host 192.168.1.1 is up",
    "... scan results ..."
  ]
}
```

**Error Responses**:

* Invalid IP → HTTP 400
* Invalid mode → HTTP 400
* Command failure → HTTP 500

---

### 6. Internet Connection Info

* **GET** `/nettools/internetinfo`
  Fetches public internet connection information using `ipinfo.io`.

**Response** (success):

```json
{
  "success": true,
  "output": "IP: 203.0.113.5 City: Sydney Country: AU Org: Example ISP"
}
```

**Error Responses**:

* Failed request or empty response → HTTP 500

---

## Example `curl` Requests

**Wake-on-LAN**:

```sh
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/nettools/wakeonlan" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{"devMac":"AA:BB:CC:DD:EE:FF"}'
```

**Traceroute**:

```sh
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/nettools/traceroute" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{"devLastIP":"192.168.1.1"}'
```

**Speedtest**:

```sh
curl "http://<server_ip>:<GRAPHQL_PORT>/nettools/speedtest" \
  -H "Authorization: Bearer <API_TOKEN>"
```

**Nslookup**:

```sh
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/nettools/nslookup" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{"devLastIP":"8.8.8.8"}'
```

**Nmap Scan**:

```sh
curl -X POST "http://<server_ip>:<GRAPHQL_PORT>/nettools/nmap" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  --data '{"scan":"192.168.1.0/24","mode":"fast"}'
```

**Internet Info**:

```sh
curl "http://<server_ip>:<GRAPHQL_PORT>/nettools/internetinfo" \
  -H "Authorization: Bearer <API_TOKEN>"
```
