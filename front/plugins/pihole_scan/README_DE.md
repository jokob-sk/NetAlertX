## Übersicht

Ein Plugin zur Gerätesynchronisierung aus einer PiHole-Datenbank. Dies ist ein Import-Plugin, welches eine SQLite-Datenbank als Datenquelle nutzt.

### Verwendung

Die folgenden Einstellungen müssen gesetzt werden:

- `PIHOLE_RUN` wird verwendet um den Import zu aktivieren, z.B. `schedule` oder `once` (Standard: `disabled`)
- `PIHOLE_RUN_SCHD` wird verwendet um festzulegen, wie of das Plugin ausgeführt wird, wenn `PIHOLE_RUN` eingestellt ist auf `schedule` (Standard: alle 30 Minuten)
- `PIHOLE_DB_PATH` muss mit dem Pfad der PiHole-Datenbank übereinstimmen (Standard: `/etc/pihole/pihole-FTL.db`)
