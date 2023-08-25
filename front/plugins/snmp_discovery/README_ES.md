## Descripción general

Un plugin para importar dispositivos desde un enrutador o conmutador habilitado para SNMP. El uso de SNMP ofrece una manera eficiente de descubrir dispositivos IPv4 en una o más redes/subredes/vlan.

### Uso

Especifique las siguientes configuraciones en la sección Configuración de PiAlert:

- `SNMPDSC_routers`: una lista de comandos `snmpwalk` para ejecutar en direcciones IP de computadoras/conmutadores con SNMP activado. Por ejemplo:

   - `snmpwalk -v 2c -c public -OXsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2`
   - `snmpwalk -v 2c -c public -Oxsq 192.168.1.1 .1.3.6.1.2.1.3.1.1.2` (nota: `x` minúscula)


### Configurar Cisco IOS

Habilite el servicio SNMP de IOS y restrinja a la IP/subred seleccionada (interna).

````
! Add standard ip access-list 10
ip access-list standard 10
 permit 192.168.1.0 0.0.0.255
 permit host 192.168.2.10
!
! Enable IOS snmp server with Read Only community 'mysnmpcommunitysecret' name.
! Restrict connections to access-list 10
snmp-server community mysnmpcommunitysecret RO 10
````

Confirmar SNMP habilitado
````
show snmp
````

### Notas

- Sólo se admite IPv4.
- El OID SNMP `.1.1.1.3.6.1.2.1.3.1.1.2` es específico para la tabla ARP IPv4 de dispositivos. Este OID se ha probado en Cisco ISR y otros dispositivos L3. El soporte puede variar entre otros proveedores/dispositivos.
- Salida esperada (ingesta) en formato `iso.3.6.1.2.1.3.1.1.2.3.1.192.168.1.2 "6C 6C 6C 6C 6C 6C "`.
