## Overview

A plugin to publish a notification via the NTFY gateway. Enable sending notifications via <a target="_blank" href="https://ntfy.sh/">NTFY</a>. Supports authentication. 

### Usage

- Go to settings and fill in relevant details.

## Reverse proxy / tunnel authentication

If your ntfy instance sits behind a reverse proxy or tunnel that authenticates requests itself (Pangolin, Tailscale, Cloudflare Access, ...), the proxy usually expects its own credential *in addition to* any ntfy token. Two optional settings cover this.

Both are independent of `NTFY_TOKEN` / `NTFY_USER` / `NTFY_PASSWORD` — those still control authentication against ntfy itself and are unaffected.

### Custom headers

Sends extra HTTP headers with the request. Prefer this over the query string for anything secret.

`NTFY_CUSTOM_HEADERS` is a list. Add one entry per header, in the format `Name: Value`:

```text
X-Proxy-Token: p_abc123.def456ghi789
```

Proxies that need more than one header work the same way — add a second entry. Pangolin, for example:

```text
P-Access-Token-Id: abc123
P-Access-Token: def456ghi789
```

Other common examples:

| Proxy | Entry |
|---|---|
| Pangolin (single token) | `P-Token: tokenId.tokenValue` |
| Cloudflare Access | `CF-Access-Client-Id: abc123.access` |
| Generic bearer gateway | `X-Auth-Token: eyJhbGciOi...` |

The first `:` separates the name from the value, so a value may itself contain colons. Whitespace around the name and around the value is trimmed, so a stray space or a trailing newline pasted in from a text file is harmless.

An entry is skipped, with a warning in the log, when:

- it is not in `Name: Value` form, or either side is empty
- the same name is listed twice
- the name collides with a header the plugin has already set for this request (`Title`, `Actions`, `Priority`, `Tags`, plus `Authorization` when an ntfy token or username/password is configured)
- after trimming, the name or the value still contains a newline or a non-ASCII character, neither of which can be sent in an HTTP header

Skipping applies to that entry only — the remaining headers are still sent and the notification still goes out. The collision rule means a custom header can never clobber your ntfy credentials. With no ntfy credentials configured there is no `Authorization` header to clash with, so you are free to use that name for the proxy.

### URL query string

Appends a query string to the ntfy request URL, for proxies that authenticate via a query parameter instead of a header.

| Setting | Sample value |
|---|---|
| `NTFY_URL_QUERY_STRING` | `p_token=tokenId.tokenValue` |

A leading `?` is optional — both `p_token=...` and `?p_token=...` work. Multiple parameters are supported: `p_token=abc&source=netalertx`.

Note that query strings are commonly recorded in proxy and web-server access logs, so for secrets the custom headers above are the safer option. The plugin redacts the query string from any error message it logs.
