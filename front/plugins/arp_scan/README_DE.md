## Übersicht

ARP-Scan ist ein Kommandozeilen-Werkzeug, welches das ARP-Protokoll nutzt, um IP-Hosts im lokalen Netzwerk zu erkennen und identifizieren. Eine Alternative zum ARP-Scan ist die Aktivierung der PiHole-Integration (`PIHOLE_RUN`) in den Einstellungen. Die Dauer des ARP-Scan (und andere Netzwerkscan-Plugins, welche die `SCAN_SUBNETS`-Einstellung nutzen) ist abhängig von der Anzahl der zu prüfenden IP-Adressen. Daher ist es wichtig, dies mit größter Vorsicht und den korrekten Netzwerkmasken und -interfaces zu konfigurieren. Die [Subnetz-Dokumentation](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/SUBNETS.md) ansehen für mehr Hilfe zum Aufsetzen von VLANs, welche VLANs unterstützt werden und zum Herausfinden der Netzwerkmaske und -interfaces.

### Verwendung

- Zur Einstellungen-Seite gehen und die `SCAN_SUBNETS`-Einstellung anhand der [Subnetz-Dokumentation](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/SUBNETS.md) konfigurieren
- Das Plugin aktivieren, indem der `RUN`-Parameter von `disabled` auf den gewünschten Ausführzeitpunkt gesetzt wird (normalerweise: `schedule`)
  - Zeitplan in der `ARPSCAN_RUN_SCHD`-Einstellung setzen
- Zeitlimit nach Bedarf in der `ARPSCAN_RUN_TIMEOUT`-Einstellung setzen
- SPEICHERN
- Auf Ausführung des nächsten Scans warten
