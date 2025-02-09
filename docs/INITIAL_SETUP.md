# ⚙ Initial Setup

## 📁 Configuration Files

- On first run, the app generates a default `app.conf` and `app.db` if unavailable.
- Preferred method: Use the **Settings UI**.
- If the UI is inaccessible, manually edit [`app.conf`](https://github.com/jokob-sk/NetAlertX/tree/main/back) in `/app/config/`.

---

## 🖥️ Setting Up Scanners

- Define networks to scan by entering accessible subnets.
- Default plugin: **ARPSCAN** → Requires at least one valid subnet + interface in `SCAN_SUBNETS`.
- 📖 [Subnet & VLAN setup guide](./SUBNETS.md) (for troubleshooting and advanced scenarios).

### 🔄 PiHole Sync
- If using **PiHole**, devices can be synced automatically.  
- 📖 [PiHole configuration guide](./PIHOLE_GUIDE.md).

### 📦 Bulk Import
> [!NOTE]  
> You can bulk-import devices via the [CSV import method](./DEVICES_BULK_EDITING.md).

---

## 🌍 Community Guides

- Various community-written configuration guides in **Chinese, Korean, German, French**.  
- 📖 [Community Guides](./COMMUNITY_GUIDES.md)  

> ⚠️ **Note:** These guides may be outdated. Always refer to the official documentation first.

---

## 🛠️ Common Issues

Before creating a new issue:

- Check if a similar issue was [already resolved](https://github.com/jokob-sk/NetAlertX/issues?q=is%3Aissue+is%3Aclosed).
- Review [common debugging tips](./DEBUG_TIPS.md).
- Check [Common Issues](./COMMON_ISSUES.md)
