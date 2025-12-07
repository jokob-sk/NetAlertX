## Overview

A plugin allowing for importing devices from the PiHole database. This is an import plugin using an SQLite database as a source.

### Usage

- You need to specify the following settings:
  - `PIHOLE_RUN` is used to enable the import by setting it e.g. to `schedule` or `once`   (pre-set to `disabled`)
  - `PIHOLE_RUN_SCHD` is to configure how often the plugin is executed if `PIHOLE_RUN` is set to `schedule` (pre-set to every 30 min)
  - `PIHOLE_DB_PATH` setting must match the location of your PiHole database (pre-set to `/etc/pihole/pihole-FTL.db`)

## Troubleshooting

### Permission problems:

NetAlertX cannot read Pi-hole DB (`/etc/pihole/pihole-FTL.db`) due to permissions:

```
[Plugins] ⚠ ERROR: ATTACH DATABASE failed with SQL ERROR: unable to open database: /etc/pihole/pihole-FTL.db
```

#### Solution:

1. **Mount full Pi-hole directory (read-only):**

```yaml
volumes:
  - /etc/pihole:/etc/pihole:ro
```

2. **Add NetAlertX to Pi-hole group:**

```yaml
group_add:
  - 1001  # check with `getent group pihole`
```

**Verify:**

```bash
docker exec -it netalertx id
# groups=1001,...  ✅ pihole group included
```

#### Notes:

* Avoid mounting single DB files.
* Keep mount read-only (`:ro`) to protect Pi-hole data.
* Use `group_add` instead of chmod.


