## Overview

A plugin allowing for importing devices from the PiHole database. This is an import plugin using an SQLite database as a source. 


### Usage

- You need to specify the following settings:
  - `PIHOLE_RUN` is used to enable the import by setting it e.g. to `schedule` or `once`   (pre-set to `disabled`)
  - `PIHOLE_RUN_SCHD` is to configure how often the plugin is executed if `PIHOLE_RUN` is set to `schedule` (pre-set to every 30 min)
  - `PIHOLE_DB_PATH` setting must match the location of your PiHole database (pre-set to `/etc/pihole/pihole-FTL.db`)
