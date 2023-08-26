## Descripción general

Un plugin que permite importar dispositivos desde un controlador UniFi.

### Uso

Especifique las siguientes configuraciones en la sección Configuración de PiAlert:

- `UNFIMP_username`: nombre de usuario utilizado para iniciar sesión en el controlador UNIFI.
- `UNFIMP_password`: contraseña utilizada para iniciar sesión en el controlador UNIFI.
- `UNFIMP_host`: URL del host o dirección IP donde está alojado el controlador UNIFI (excluyendo http://)
- `UNFIMP_sites`: nombre de los sitios (generalmente 'predeterminado', verifique la URL en la interfaz de usuario de su controlador UniFi si no está seguro. La identificación del sitio se encuentra en la siguiente parte de la URL: `https://192.168.1.1:8443/manage /sitio/este-es-el-id-del-sitio/configuración/`).
- `Protocolo_UNFIMP` - https:// o http://
- `UNFIMP_port` - Generalmente 8443

### Notas

- Actualmente sólo se utiliza para importar dispositivos, no su estado, tipo o mapa de red.
- Se recomienda crear un usuario de solo lectura en su controlador UniFi
