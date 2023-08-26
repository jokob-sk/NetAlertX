## Descripción general

Un plugin que permite importar dispositivos desde archivos DHCP.leases.

### Uso

- Especifique las rutas completas de todos los archivos `dhcp.leases` que desea importar y observar en la configuración `DHCPLSS_paths_to_check`.
- Asigne las rutas especificadas en la configuración `DHCPLSS_paths_to_check` en su archivo `docker-compose.yml`.

#### Ejemplo:


Extracto `docker-compose.yml`:

```yaml
    volumes:
      ...
      # Mapeo de diferentes archivos dhcp.leases
      - /first/location/dhcp.leases:/mnt/dhcp1.leases
      - /second/location/dhcp.leases:/mnt/dhcp2.leases      
      ...
```

Configuración `DHCPLSS_paths_to_check`: 

```python
DHCPLSS_paths_to_check = ['/mnt/dhcp1.leases','/mnt/dhcp2.leases']
```

### Notas

- No se necesita ninguna configuración específica.

- Este complemento espera que los archivos dhcp.leases tengan el formato **dhcpd.leases**, que es diferente al formato que utiliza PiHole.
[dhcpd.leases(5) - Linux man page]( https://linux.die.net/man/5/dhcpd.leases#:~:text=This%20database%20is%20a%20free,file%20is%20the%20current%20one.) 

Formato de archivo de ejemplo:  _(no todas las líneas son obligatorias)_

```
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
