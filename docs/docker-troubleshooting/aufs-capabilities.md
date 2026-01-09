
# AUFS Legacy Storage Driver Support

## Issue Description

NetAlertX automatically detects the legacy `aufs` storage driver, which is commonly found on older Synology NAS devices (DSM 6.x/7.0.x) or Linux systems where the underlying filesystem lacks `d_type` support. This occurs on older ext4 and other filesystems which did not support capabilites at time of last formatting.  While ext4 currently support capabilities and filesystem overlays, older variants of ext4 did not and require a reformat to enable the support.  Old variants result in docker choosing `aufs` and newer may use `overlayfs`. 

**The Technical Limitation:**
AUFS (Another Union File System) does not support or preserve extended file attributes (`xattrs`) during Docker image extraction. NetAlertX relies on these attributes to grant granular privileges (`CAP_NET_RAW` and `CAP_NET_ADMIN`) to network scanning binaries like `arp-scan`, `nmap`, and `nbtscan`.

**The Result:**
When the container runs as a standard non-root user (default) on AUFS, these binaries are stripped of their capabilities. Consequently, layer-2 network discovery will fail silently, find zero devices, or exit with "Operation not permitted" errors.

## Operational Logic

The container is designed to inspect the runtime environment at startup (`/root-entrypoint.sh`). It respects user configuration first, falling back to safe defaults (with warnings) where necessary.

**Behavior Matrix:**

| Filesystem | PUID Config | Runtime User | Outcome |
| :--- | :--- | :--- | :--- |
| **Modern (Overlay2/Btrfs)** | Unset | `20211` | **Secure.** Full functionality via preserved `setcap`. |
| **Legacy (AUFS)** | Unset | `20211` | **Degraded.** Logs warning. L2 scans fail due to missing perms. |
| **Legacy (AUFS)** | `PUID=0` | `Root` | **Functional.** Root privileges bypass capability requirements. |
| **Legacy (AUFS)** | `PUID=1000` | `1000` | **Degraded.** Logs warning. L2 scans fail due to missing perms. |

### Warning Log
When AUFS is detected without root privileges, the system emits the following warning during startup:
> ⚠️  WARNING: Reduced functionality (AUFS + non-root user).
> 
> AUFS strips Linux file capabilities, so tools like arp-scan, nmap, and nbtscan fail when NetAlertX runs as a non-root PUID.
>
> **Action:** Set PUID=0 on AUFS hosts for full functionality.


## Security Ramifications

To mitigate the AUFS limitation, the recommended fix is to run the application as the **root** user (`PUID=0`).

* **Least Privilege:** Even when running as root, NetAlertX applies `cap_drop: - ALL` and re-adds only the strictly necessary capabilities (`NET_RAW`, `NET_ADMIN`). This maintains a "least privilege" posture, though it is inherently less secure than running as a specific UID.
* **Attack Surface:** Running as UID 0 increases the theoretical attack surface. If the container were compromised, the attacker would have root access *inside* the container (though still isolated from the host by the Docker runtime).
* **Legacy Risks:** Reliance on the deprecated AUFS driver often indicates an older OS kernel or filesystem configuration, which may carry its own unpatched vulnerabilities compared to modern `overlay2` or `btrfs` setups.


## How to Correct the Issue

Choose the scenario that best matches your environment and security requirements.

### Scenario A: Modern Systems (Recommended)
**Context:** Systems using `overlay2`, `btrfs`, or `zfs`.
**Action:** No action required. The system auto-configures `PUID=20211`.

```yaml
services:
  netalertx:
    image: netalertx/netalertx
    # No PUID/PGID needed; defaults to secure non-root

```

### Scenario B: Legacy/Synology AUFS (The Fix)

**Context:** Synology DSM 6.x/7.x or Linux hosts using AUFS.
**Action:** Explicitly elevate to root. This bypasses the need for file capabilities because Root inherits runtime capabilities directly from Docker.

```yaml
services:
  netalertx:
    image: netalertx/netalertx
    environment:
      - PUID=0  # Required for arp-scan/nmap on AUFS
      - PGID=0

```

### Scenario C: Forced Non-Root on AUFS

**Context:** Strict security compliance requires non-root, even if it breaks functionality.
**Action:** The warning will persist. The Web UI and Database will function, but network discovery (ARP/Nmap) will be severely limited.

```yaml
services:
  netalertx:
    image: netalertx/netalertx
    environment:
      - PUID=1000
      - PGID=1000
    # Note: cap_add is ineffective here due to AUFS stripping the binary's file caps

```


## Infrastructure Upgrades (Long-term Fix)

To solve the root cause and run securely as non-root, you must migrate off the AUFS driver.

### 1. Switch to Btrfs (Synology Recommended)

If your NAS supports it, creating a new volume formatted as **Btrfs** allows Docker to use the native `btrfs` storage driver.

* **Benefit:** This driver fully supports extended attributes and Copy-on-Write (CoW), creating the most robust environment for Docker.

### 2. Reformat Ext4 with `d_type` Support

If you must use `ext4`, the issue is likely that your volume lacks `d_type` support (common on older volumes created before DSM 6).

* **Fix:** Back up your data and reformat the volume.
* **Result:** Modern formatting usually enables `d_type` by default. This allows Docker to automatically select the modern **`overlay2`** driver instead of failing back to AUFS.


## Technical Implementation

### Detection Mechanism

The logic resides in `_detect_storage_driver()` within `/root-entrypoint.sh`. It parses the root mount point (`/`) to identify the underlying driver.

```bash
# Modern (overlay2) - Pass
overlay / overlay rw,relatime,lowerdir=...

# Legacy (AUFS) - Triggers Warning
none / aufs rw,relatime,si=...

```

### Verification & Troubleshooting

**1. Confirm Storage Driver**
If your host is using ext4 you might be defaulting to aufs:

```bash
docker info | grep "Storage Driver"
# OR inside the container:
docker exec netalertx grep " / " /proc/mounts

```

**2. Verify Capability Loss**
If scans fail, check if the binary permissions were stripped.

* **Modern FS:** Returns `cap_net_admin,cap_net_raw+eip`
* **AUFS:** Returns empty output (stripped)

```bash
docker exec netalertx getcap /usr/sbin/arp-scan

```

**3. Simulating AUFS (Dev/Test)**
Developers can force the AUFS logic path on a modern machine by mocking the mounts file. Note: Docker often restricts direct bind-mounts of host `/proc` paths, so the test suite uses an environment-variable injection instead (see `test_puid_pgid.py`).

```bash
# Create mock mounts content and encode it as base64
echo "none / aufs rw,relatime 0 0" | base64

# Run the container passing the encoded mounts via NETALERTX_PROC_MOUNTS_B64
# (the entrypoint decodes this and uses it instead of reading /proc/mounts directly)
docker run --rm -e NETALERTX_PROC_MOUNTS_B64="bm9uZSAvIGF1ZnMgcncs..." netalertx/netalertx
```

## Additional Resources

* **Docker Storage Drivers:** [Use the OverlayFS storage driver](https://docs.docker.com/storage/storagedriver/overlayfs-driver/)
* **Synology Docker Guide:** [Synology Docker Storage Drivers](https://www.google.com/search?q=https://kb.synology.com/en-global/DSM/tutorial/How_to_use_Docker_on_Synology_NAS)
* **Configuration Guidance:** [DOCKER_COMPOSE.md](https://github.com/jokob-sk/NetAlertX/blob/main/docs/DOCKER_COMPOSE.md)


