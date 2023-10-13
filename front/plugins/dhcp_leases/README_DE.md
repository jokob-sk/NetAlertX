## Übersicht

Ein Plugin zum Importieren von Geräten aus dhcp.leases-Dateien.

### Verwendung

- Absolute Pfade der `dhcp.leases`-Dateien, welche importiert werden sollen, in der `DHCPLSS_paths_to_check`-Einstellung angeben.
- Angegebene Pfade in der `DHCPLSS_paths_to_check`-Einstellung in der `docker-compose.yml`-Datei mapppen.

#### Beispiel

Auszug aus `docker-compose.yml`:

```yaml
    volumes:
      ...
      # mapping different dhcp.leases files
      - /first/location/dhcp.leases:/mnt/dhcp1.leases
      - /second/location/dhcp.leases:/mnt/dhcp2.leases      
      ...
```

`DHCPLSS_paths_to_check`-Einstellung:

```python
DHCPLSS_paths_to_check = ['/mnt/dhcp1.leases','/mnt/dhcp2.leases']
```

### Notizen

- Keine spezifische Konfiguration benötigt.

- Dieses Plugin erwartet dhcp.leases-Dateien im **dhcp.leases**-Format, welches sich vom von PiHole genutzten Format unterscheidet. [dhcpd.leases(5) - Linux man page]( https://linux.die.net/man/5/dhcpd.leases#:~:text=This%20database%20is%20a%20free,file%20is%20the%20current%20one.)

Beispiel Dateiformat:  _(nicht alle Zeilen werden benötigt)_

```text
lease 192.168.79.15 {
  starts 0 2016/08/21 13:25:45;
  ends 0 2016/08/21 19:25:45;
  cltt 0 2016/08/21 13:25:45;
  binding state active;
  next binding state free;
  rewind binding state free;
  hardware ethernet 8c:1a:bf:11:00:ea;
  uid "\001\214\032\277\021\000\352";
  option agent.circuit-id 0:17;
  option agent.remote-id c0:a8:9:5;
  client-hostname "android-8182e21c852776e7";
}  
```
