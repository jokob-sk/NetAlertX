## Übersicht

Ein Plugin zur Erkennung von Geräten mittels ARP-Tabellen von RFC1213-konformen Routern oder Switches. Die Verwendung von SNMP ermöglicht einen effizienten Weg um IPv4-Geräte in einem oder mehreren Netzwerken/Subnetzwerken/VLANs zu erkennen.

### Verwendung

Die folgenden Einstellungen in der Einstellungen-Seite von PiAlert setzen:

- `SNMPDSC_routers` - Eine Liste an <code>snmpwalk</code>-Befehle, welche auf IP-Adressen von SNMP-aktivierte Routern/Switches ausgeführt werden. Beispiel:

  - `snmpwalk -v 2c -c public -OXsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2`
  - `snmpwalk -v 2c -c public -Oxsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2` (Notiz: kleingeschriebenes `x`)

### Cisco IOS Setup

IOS SNMP Service aktivieren und auf das ausgewählte (interne) Subnetz limitieren.

```text
! Add standard ip access-list 10
ip access-list standard 10
 permit 192.168.1.0 0.0.0.255
 permit host 192.168.2.10
!
! Enable IOS snmp server with Read Only community 'mysnmpcommunitysecret' name.
! Restrict connections to access-list 10
snmp-server community mysnmpcommunitysecret RO 10
````

SNMP-Status überprüfen.

```text
show snmp
```

### Notizen

- Nur IPv4 wird unterstützt.
- Die SNMP OID `.1.1.1.3.6.1.2.1.3.1.1.2` ist speziell für IPv4 ARP-Tabellen von Geräten. Diese OID wurde getestet mit Cicso ISRs und anderen L3-Geräten. Unterstützung kann zwischen verschiedenen Herstellern / Geräten variieren.
- Erwatetes Ausgabeformat ist `iso.3.6.1.2.1.3.1.1.2.3.1.192.168.1.2 "6C 6C 6C 6C 6C 6C "`.
