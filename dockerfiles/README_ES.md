[![Docker](https://img.shields.io/github/actions/workflow/status/jokob-sk/Pi.Alert/docker_prod.yml?label=Build&logo=GitHub)](https://github.com/jokob-sk/Pi.Alert/actions/workflows/docker_prod.yml)
[![GitHub Committed](https://img.shields.io/github/last-commit/jokob-sk/Pi.Alert?color=40ba12&label=Committed&logo=GitHub&logoColor=fff)](https://github.com/jokob-sk/Pi.Alert)
[![Docker Size](https://img.shields.io/docker/image-size/jokobsk/pi.alert?label=Tamaño&logo=Docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/pi.alert)
[![Docker Pulls](https://img.shields.io/docker/pulls/jokobsk/pi.alert?label=Pulls&logo=docker&color=0aa8d2&logoColor=fff)](https://hub.docker.com/r/jokobsk/pi.alert)
[![Docker Pushed](https://img.shields.io/badge/dynamic/json?color=0aa8d2&logoColor=fff&label=Pushed&query=last_updated&url=https%3A%2F%2Fhub.docker.com%2Fv2%2Frepositories%2Fjokobsk%2Fpi.alert%2F&logo=docker&link=http://left&link=https://hub.docker.com/repository/docker/jokobsk/pi.alert)](https://hub.docker.com/r/jokobsk/pi.alert)

# 🐳 Una imagen docker para Pi.Alert

🐳 [Docker hub](https://registry.hub.docker.com/r/jokobsk/pi.alert) | 📑 [Instrucciones para Docker](https://github.com/jokob-sk/Pi.Alert/blob/main/dockerfiles/README.md) | 🆕 [Release notes](https://github.com/jokob-sk/Pi.Alert/releases) | 📚 [Todos los Docs](https://github.com/jokob-sk/Pi.Alert/tree/main/docs)

<a href="https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/devices_split.png" target="_blank">
  <img src="https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/devices_split.png" width="300px" />
</a>
<a href="https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/network.png" target="_blank">
  <img src="https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/network.png" width="300px" />
</a>


## 📕 Uso básico

- Tendrás que ejecutar el contenedor en la red del host, por ejemplo: 

```yaml
docker run -d --rm --network=host \
  -v local/path/pialert/config:/home/pi/pialert/config \
  -v local/path/pialert/db:/home/pi/pialert/db \
  -e TZ=Europe/Berlin \
  -e PORT=20211 \
  jokobsk/pi.alert:latest
  ```
- El escaneo inicial puede tardar hasta 15 minutos (con 50 dispositivos y MQTT). Los siguientes pueden durar entre 3 y 5 minutos, así que espere a que se ejecuten todos los escaneos.

### Variables de entorno Docker

| Variable | Descripción | Predeterminado |
| :------------- |:-------------| -----:|
| `PORT`      |Puerto de la interfaz web  |  `20211` |
|`TZ` |Zona horaria para mostrar correctamente las estadísticas. Encuentre su zona horaria [aquí](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)  |  `Europe/Berlin` |
|`HOST_USER_GID`    |ID de usuario (UID) para asignar el usuario del contenedor a un usuario del servidor con suficientes permisos de lectura y escritura en los archivos asignados   |  `1000` |
|`HOST_USER_ID` |ID de grupo de usuarios (GID) para asignar el grupo de usuarios del contenedor a un grupo de usuarios del servidor con suficientes permisos de lectura y escritura en los archivos asignados    |    `1000` |

### Rutas Docker

| | Ruta | Descripción |
| :------------- | :------------- |:-------------| 
| **Obligatorio** | `:/home/pi/pialert/config` | Carpeta que contendrá el archivo `pialert.conf` (para más detalles, véase más abajo)  | 
| **Obligatorio** | `:/home/pi/pialert/db` | Carpeta que contendrá el archivo `pialert.db`  | 
|Opcional| `:/home/pi/pialert/front/log` |  Carpeta de registros útil para depurar si tiene problemas al configurar el contenedor  | 
|Opcional| `:/etc/pihole/pihole-FTL.db` |  Archivo de base de datos `pihole-FTL.db` de PiHole. Necesario si desea utilizar PiHole  | 
|Opcional| `:/etc/pihole/dhcp.leases` |  Archivo `dhcp.leases` de PiHole. Obligatorio si desea utilizar el archivo `dhcp.leases` de PiHole. Tiene que coincidir con la correspondiente entrada de configuración `DHCPLSS_paths_to_check`. (La ruta en el contenedor debe contener `pihole`)| 
|Opcional| `:/home/pi/pialert/front/api` |  Una simple [API endpoint](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/API.md) que contiene archivos json estáticos (pero actualizados regularmente) y otros archivos.   | 


### Configurar (`pialert.conf`)

- Si no está disponible, la aplicación genera un archivo `pialert.conf` y `pialert.db` por defecto en la primera ejecución.
- La forma preferida es gestionar la configuración a través de la sección "Configuración" de la interfaz de usuario.
- Puede modificar [pialert.conf](https://github.com/jokob-sk/Pi.Alert/tree/main/config) directamente, si es necesario.

#### Ajustes importantes

Estos son los ajustes más importantes para obtener al menos alguna salida en la pantalla de tus Dispositivos. Por lo general, sólo se utiliza un enfoque, pero usted debe ser capaz de combinar estos enfoques.

##### Para arp-scan: ARPSCAN_RUN, SCAN_SUBNETS

- ❗ Para usar el método arp-scan, necesitas configurar la variable `SCAN_SUBNETS`. Consulte la documentación sobre cómo [configurar SUBNETS, VLANs y limitaciones](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/SUBNETS.md) 

##### Para pihole: PIHOLE_RUN, DHCPLSS_RUN

Hay dos maneras de importar dispositivos PiHole. A través del plugin de importación PiHole (PIHOLE) o del plugin DHCP leases (DHCPLSS).

**PiHole (Sincronización de dispositivos)**

* `PIHOLE_RUN`: Necesitas mapear `:/etc/pihole/pihole-FTL.db` en el fichero `docker-compose.yml` si activas esta opción.

**DHCP Leases (Importación de dispositivos)**

* `DHCPLSS_RUN`: Es necesario mapear `:/etc/pihole/dhcp.leases` en el fichero `docker-compose.yml` si se activa esta opción. 
* La configuración anterior tiene que coincidir con una entrada de configuración correspondiente `DHCPLSS_paths_to_check` (la ruta en el contenedor debe contener `pihole` ya que PiHole utiliza un formato diferente del archivo `dhcp.leases`).

> Se recomienda utilizar el mismo intervalo de programación para todos los plugins responsables de descubrir nuevos dispositivos.

### **Problemas comunes** 

💡 Antes de crear una nueva incidencia, comprueba si ya se ha resuelto una [incidencia similar](https://github.com/jokob-sk/Pi.Alert/issues?q=is%3Aissue+is%3Aclosed). 

⚠ Compruebe también los problemas comunes y los [consejos de depuración](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/DEBUG_TIPS.md). 

## 📄 Ejemplos

### Ejemplo 1

```yaml
version: "3"
services:
  pialert:
    container_name: pialert
    # Utilice la siguiente línea si desea probar la última imagen de desarrollo
    # image: "jokobsk/pi.alert_dev:latest" 
    image: "jokobsk/pi.alert:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - local/path/pialert/config:/home/pi/pialert/config
      - local/path/pialert/db:/home/pi/pialert/db      
      # (optional) useful for debugging if you have issues setting up the container
      - local/path/logs:/home/pi/pialert/front/log
    environment:
      - TZ=Europe/Berlin      
      - HOST_USER_ID=1000
      - HOST_USER_GID=1000
      - PORT=20211
```

Para ejecutar el contenedor ejecute: `sudo docker-compose up -d`

### Ejemplo 2

Ejemplo de [SeimuS](https://github.com/SeimusS).

```yaml
  pialert:
    container_name: PiAlert
    hostname: PiAlert
    privileged: true
    # Utilice la siguiente línea si desea probar la última imagen de desarrollo
    # image: "jokobsk/pi.alert_dev:latest" 
    image: jokobsk/pi.alert:latest
    environment:
      - TZ=Europe/Bratislava
    restart: always
    volumes:
      - ./pialert/pialert_db:/home/pi/pialert/db
      - ./pialert/pialert_config:/home/pi/pialert/config
    network_mode: host
```

Para ejecutar el contenedor ejecute: `sudo docker-compose up -d`

### Ejemplo 3

`docker-compose.yml` 

```yaml
version: "3"
services:
  pialert:
    container_name: pialert
    # Utilice la siguiente línea si desea probar la última imagen de desarrollo
    # image: "jokobsk/pi.alert_dev:latest" 
    image: "jokobsk/pi.alert:latest"      
    network_mode: "host"        
    restart: unless-stopped
    volumes:
      - ${APP_DATA_LOCATION}/pialert/config:/home/pi/pialert/config
      - ${APP_DATA_LOCATION}/pialert/db/pialert.db:/home/pi/pialert/db/pialert.db      
      # (optional) useful for debugging if you have issues setting up the container
      - ${LOGS_LOCATION}:/home/pi/pialert/front/log
    environment:
      - TZ=${TZ}      
      - HOST_USER_ID=${HOST_USER_ID}
      - HOST_USER_GID=${HOST_USER_GID}
      - PORT=${PORT}
```

`.env` file

```yaml
#VARIABLES DE RUTA GLOBAL

APP_DATA_LOCATION=/path/to/docker_appdata
APP_CONFIG_LOCATION=/path/to/docker_config
LOGS_LOCATION=/path/to/docker_logs

#VARIABLES DE ENTORNO

TZ=Europe/Paris
HOST_USER_ID=1000
HOST_USER_GID=1000
PORT=20211

#VARIABLES DE DESARROLLO

DEV_LOCATION=/path/to/local/source/code
```

Para ejecutar el contenedor ejecute: `sudo docker-compose --env-file /path/to/.env up`

### Example 4

Por cortesía de [pbek](https://github.com/pbek). El volumen `pialert_db` es utilizado por el directorio db. Los dos archivos de configuración se montan directamente desde una carpeta local a sus lugares en la carpeta config. Puedes hacer una copia de seguridad de la carpeta `docker-compose.yaml` y de la carpeta docker volumes.


```yaml
  pialert:
    # Utilice la siguiente línea si desea probar la última imagen de desarrollo
    # image: "jokobsk/pi.alert_dev:latest" 
    image: jokobsk/pi.alert
    ports:
      - "80:20211/tcp"
    environment:
      - TZ=Europe/Vienna
    networks:
      local:
        ipv4_address: 192.168.1.2
    restart: unless-stopped
    volumes:
      - pialert_db:/home/pi/pialert/db
      - ./pialert/pialert.conf:/home/pi/pialert/config/pialert.conf      
```

## 🏅 Reconocimientos

Muchas gracias a <a href="https://github.com/Macleykun">@Macleykun</a> por ayudarme en consejos y trucos para Dockerfile(s):

<a href="https://github.com/Macleykun">
  <img src="https://avatars.githubusercontent.com/u/26381427?size=50"> 
</a>

Muchas gracias a <a href="https://github.com/cvc90">@cvc90</a> por ayudarme y realizar esta traduccion:

<a href="https://github.com/cvc90">
  <img src="https://avatars.githubusercontent.com/u/76731844?size=50"> 
</a>

## ☕ Apóyame

<a href="https://github.com/sponsors/jokob-sk" target="_blank"><img src="https://i.imgur.com/X6p5ACK.png" alt="Sponsor Me on GitHub" style="height: 30px !important;width: 117px !important;" width="150px" ></a>
<a href="https://www.buymeacoffee.com/jokobsk" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 30px !important;width: 117px !important;" width="117px" height="30px" ></a>
<a href="https://www.patreon.com/user?u=84385063" target="_blank"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Patreon_logo_with_wordmark.svg/512px-Patreon_logo_with_wordmark.svg.png" alt="Support me on patreon" style="height: 30px !important;width: 117px !important;" width="117px" ></a>

BTC: 1N8tupjeCK12qRVU2XrV17WvKK7LCawyZM
