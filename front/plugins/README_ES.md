## 📚 Documentos para plugins individuales 

### 🏴 Traducciones comunitarias de este archivo

* <a href="https://github.com/jokob-sk/Pi.Alert/blob/main/front/plugins/README.md">
   <img src="https://github.com/lipis/flag-icons/blob/main/flags/4x3/us.svg" alt="README.md" style="height: 20px !important;width: 20px !important;"> Ingles (Americano)
  </a> 

* <a href="https://github.com/jokob-sk/Pi.Alert/blob/main/front/plugins/README_DE.md">
   <img src="https://github.com/lipis/flag-icons/blob/main/flags/4x3/de.svg" alt="README.md" style="height: 20px !important;width: 20px !important;"> Alemán (Alemania)
  </a> 

### 🔌 Plugins y 📚 Documentos

| Requerido   | CurrentScan | Prefijo único         | Tipo de plugin         | Enlace + Documentos                                      | 
|-------------|-------------|-----------------------|------------------------|----------------------------------------------------------|
|             |    Sí       | ARPSCAN               | Script                 | [arp_scan](/front/plugins/arp_scan/)          |
|             |             | CSVBCKP               | Script                 | [csv_backup](/front/plugins/csv_backup/)      |
|             |    Sí       | DHCPLSS               | Script                 | [dhcp_leases](/front/plugins/dhcp_leases/)    |
|             |             | DHCPSRVS              | Script                 | [dhcp_servers](/front/plugins/dhcp_servers/) |
|     Sí      |             | NEWDEV                | Template               | [newdev_template](/front/plugins/newdev_template/) |
|             |             | NMAP                  | Script                 | [nmap_scan](/front/plugins/nmap_scan/)            |
|             |    Sí       | PIHOLE                | External SQLite DB     | [pihole_scan](/front/plugins/pihole_scan/)    |
|             |             | SETPWD                | Script                 | [set_password](/front/plugins/set_password/)    |
|             |             | SNMPDSC               | Script                 | [snmp_discovery](/front/plugins/snmp_discovery/) |
|             |    Sí*      | UNDIS                 | Script                 | [undiscoverables](/front/plugins/undiscoverables/) |
|             |    Sí       | UNFIMP                | Script                 | [unifi_import](/front/plugins/unifi_import/)    |
|             |             | WEBMON                | Script                 | [website_monitor](/front/plugins/website_monitor/) |
|     N/A     |             | N/A                   | SQL query              | No hay ningún ejemplo disponible, pero los complementos basados en SQLite externo funcionan de manera muy similar |

>* El complemento Undiscoverables (`UNDIS`) inserta solo dispositivos ficticios especificados por el usuario.

> [!NOTE] 
> Puede desactivar los complementos a través de Configuración o ignorarlos por completo colocando un archivo `ignore_plugin` en el directorio de complementos. La diferencia es que los complementos ignorados no aparecen en ninguna parte de la interfaz de usuario (Configuración, Detalles del dispositivo, páginas de complementos). La aplicación omite por completo los complementos ignorados. Los complementos de detección de dispositivos insertan valores en la tabla de base de datos "CurrentScan". Es seguro ignorar los complementos que no son necesarios; sin embargo, tiene sentido tener habilitados al menos algunos complementos de detección de dispositivos (que insertan entradas en la tabla `CurrentScan`), como ARPSCAN o PIHOLE.  

> Se recomienda utilizar el mismo intervalo de programación para todos los complementos responsables de descubrir nuevos dispositivos.

## 🌟 Crear un plugin personalizado: Descripción general

| ![Screen 1][screen1] | ![Screen 2][screen2] | ![Screen 3][screen3] | 
|----------------------|----------------------| ----------------------| 
| ![Screen 4][screen4] |  ![Screen 5][screen5] | 

PiAlert viene con un sistema de complementos para enviar eventos desde scripts de terceros a la interfaz de usuario y luego enviar notificaciones, si lo desea. La funcionalidad principal destacada que admite este sistema de complementos es:

* creación dinámica de una interfaz de usuario simple para interactuar con los objetos descubiertos,
* filtrado de valores mostrados en la interfaz de usuario de dispositivos
* configuración superficial de complementos en la interfaz de usuario,
* diferentes tipos de columnas para los valores informados, por ejemplo. vincular de nuevo a un dispositivo
* importar objetos a tablas de bases de datos PiAlert existentes

> (Actualmente, no se admite la actualización/sobrescritura de objetos existentes..)

Ejemplos de casos de uso de plugins podrían ser:

* Monitorear un servicio web y avisarme si está caído
* Importar dispositivos desde archivos dhcp.leases en lugar/complementario al uso de PiHole o arp-scans
* Creación de tablas de UI ad-hoc a partir de datos existentes en la base de datos PiAlert, p.e. para mostrar todos los puertos abiertos en los dispositivos, para enumerar los dispositivos que se desconectaron en la última hora, etc.
* Usar otros métodos de descubrimiento de dispositivos en la red e importar los datos como dispositivos nuevos
* Creación de un script para crear dispositivos FALSOS según la entrada del usuario a través de configuraciones personalizadas
* ...en este punto, la limitación es más la creatividad que la capacidad (puede haber casos extremos y la necesidad de admitir más controles de formulario para la entrada del usuario fuera de las configuraciones personalizadas, pero probablemente se entienda la idea)

Si desea desarrollar un plugin, verifique la estructura del complemento existente. Una vez que el usuario guarda la configuración, debe eliminarla manualmente del archivo `pialert.conf` si desea reinicializarla desde el `config.json` del complemento.

Nuevamente, lea atentamente lo siguiente si desea contribuir usted mismo con un complemento. Este archivo de documentación puede estar desactualizado, así que verifique también los complementos de muestra.

## ⚠ Aviso legal

Siga lo siguiente con mucho cuidado y consulte los plugin(s) de ejemplo si desea escribir uno usted mismo. La interfaz de usuario del complemento no es mi prioridad en este momento, y estaré encantado de aprobar PRs si está interesado en ampliar/mejorar la experiencia de la interfaz de usuario. Mejoras de ejemplo para tomar:

* Hacer que las tablas se puedan ordenar/filtrar
* Utilizar el mismo enfoque para mostrar los datos de la tabla que en la sección Dispositivos (resuelve arriba)
* Agregar controles de formulario admitidos para mostrar los datos (los actualmente admitidos se enumeran en la sección "Configuración de la interfaz de usuario en definiciones de columna de base de datos" a continuación)
*...

## ❗ Problemas conocidos:

Es de esperar que estos problemas se solucionen con el tiempo, así que no los informe. En cambio, si sabe cómo, no dude en investigar y enviar un PR para solucionar lo siguiente. Mantenga los RP pequeños ya que es más fácil aprobarlos:

* Los objetos de plugins existentes a veces no se interpretan correctamente y en su lugar se crea un nuevo objeto, lo que genera entradas duplicadas.
* Ocasionalmente (experimentado dos veces) se cuelga el archivo de script del complemento de procesamiento.
La interfaz de usuario muestra valores obsoletos hasta que se actualizan los puntos finales de la API.

## Descripción general de la estructura del archivo del plugin

> ⚠️El nombre de la carpeta debe ser el mismo que el valor del nombre del código en: `"code_name": "<value>"`
> El prefijo único debe ser único en comparación con los otros prefijos de configuración, por ejemplo: el prefijo `APPRISE` ya está en uso. 

  | Archivo | Requerido (tipo de plugin) | Descripción | 
  |----------------------|----------------------|----------------------| 
  | `config.json` | Sí | Contiene la configuración del complemento (manifiesto), incluida la configuración disponible para el usuario. |
  | `script.py` |  Sí (script) | El script Python en sí |
  | `last_result.log` | Sí (script) |El archivo utilizado para la interfaz entre PiAlert y el plugin (script).  |
  | `script.log` | No | Salida de registro (recomendado) |
  | `README.md` | No | Cualquier consideración de configuración o descripción general (recomendado) |

Más sobre detalles a continuación.

### Orden de columnas y valores

  | Orden | Columna representada | Requerido | Descripción | 
  |----------------------|----------------------|----------------------|----------------------| 
  | 0 | `Object_PrimaryID` | Sí | El ID principal utilizado para agrupar eventos en. |
  | 1 | `Object_SecondaryID` | No | ID secundaria opcional para crear una relación entre otras entidades, como una dirección MAC |
  | 2 | `DateTime` | Sí | Cuando el evento ocurrió en el formato `2023-01-02 15:56:30` |
  | 3 | `Watched_Value1` | Sí | Un valor que se observa y los usuarios pueden recibir notificaciones si cambia en comparación con la entrada guardada anteriormente. Por ejemplo dirección IP |
  | 4 | `Watched_Value2` | No | Como en el caso anterior |
  | 5 | `Watched_Value3` | No | Como en el caso anterior  |
  | 6 | `Watched_Value4` | No | Como en el caso anterior  |
  | 7 | `Extra` | No | Cualquier otro dato que desee pasar y mostrar en PiAlert y las notificaciones |
  | 8 | `ForeignKey` | No | Una clave externa que se puede utilizar para vincular al objeto principal (normalmente una dirección MAC) |

> [!NOTE] 
> La deduplicación se ejecuta una vez por hora en la tabla de base de datos `Plugins_Objects` y las entradas duplicadas con el mismo valor en las columnas `Object_PrimaryID`, `Object_SecondaryID`, `Plugin` (autocompletadas según el `unique_prefix` del complemento), Se eliminan los `UserData` (que se pueden completar con el tipo de columna `"type": "textbox_save"`).
# Estructura config.json

## Fuentes de datos admitidas

Actualmente, estas fuentes de datos son compatibles (valid `data_source` value). 

| Nombre | `data_source` valor | Necesita devolver una "tabla" | Descripción general (más detalles en esta página a continuación) | 
|----------------------|----------------------|----------------------|----------------------| 
| Script | `script` | No | Ejecuta cualquier comando de Linux en la configuración `CMD`. |
| Pialert DB query | `pialert-db-query` | Sí | Ejecuta una consulta SQL en la base de datos PiAlert en la configuración `CMD`. |
| Template | `template` | No | Se utiliza para generar configuraciones internas, como valores predeterminados. |
| External SQLite DB query | `sqlite-db-query` | Sí | Ejecuta una consulta SQL desde la configuración `CMD` en una base de datos SQLite externa asignada en la configuración `DB_PATH`.  |


> 🔎Ejemplo
>```json
>"data_source":  "pialert-db-query"
>```
Cualquiera de las fuentes de datos anteriores debe devolver una "tabla" con la estructura exacta descrita anteriormente.

Puede mostrar u ocultar la interfaz de usuario en la página "Complementos" y en la pestaña "Complementos" en los dispositivos a través de la propiedad `show_ui`:

> 🔎Ejemplo
>```json
> "show_ui": true,
> ```

### "data_source":  "script"

Si `data_source` está configurado en `script`, la configuración `CMD` (que usted especifica en la sección de matriz `settings` en `config.json`) debe contener un comando ejecutable de Linux, que genera un `last_result.log `archivo. Este archivo debe almacenarse en la misma carpeta que el complemento.

El contenido del archivo `last_result.log` debe contener las columnas tal como se definen en la sección "Orden y valores de las columnas" anterior. El orden de las columnas no se puede cambiar. Después de cada escaneo, debe contener solo los resultados del último escaneo/ejecución.

- El formato de `last_result.log` es un archivo tipo `csv` con la tubería `|` como separador.
- Es necesario suministrar 9 (nueve) valores, por lo que cada línea debe contener 8 separadores de tuberías. Los valores vacíos se representan con "nulo".
- No muestre "encabezados" para estas "columnas".
- Cada resultado del escaneo/entrada de evento debe estar en una nueva línea.
- Puede encontrar qué "columnas" deben estar presentes y si el valor es obligatorio u opcional, en la sección "Orden de columnas y valores".
- El orden de estas "columnas" no se puede cambiar.

### 👍 Consejos para Python script.py

El [Undicoverables plugins `script.py` file](/front/plugins/undiscoverables/script.py) es un ejemplo bueno y simple para comenzar si está considerando crear un complemento personalizado. Utiliza la [`plugin_helper.py` library](/front/plugins/plugin_helper.py) que simplifica significativamente la creación de su script personalizado.

#### 🔎 Ejemplos de last_result.log

CSV válido:

```csv

https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|null|null|null|null
https://www.duckduckgo.com|192.168.0.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|ff:ee:ff:11:ff:11

```

CSV no válido con diferentes errores en cada línea:

```csv

https://www.google.com|null|2023-01-02 15:56:30|200|0.7898||null|null|null
https://www.duckduckgo.com|null|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|
|https://www.duckduckgo.com|null|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine|null
null|192.168.1.1|2023-01-02 15:56:30|200|0.9898|null|null|Best search engine
https://www.duckduckgo.com|192.168.1.1|2023-01-02 15:56:30|null|0.9898|null|null|Best search engine
https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|||
https://www.google.com|null|2023-01-02 15:56:30|200|0.7898|

```

### "data_source":  "pialert-db-query"

Si `data_source` está configurado en `pialert-db-query`, la configuración `CMD` debe contener una consulta SQL que represente las columnas como se define en la sección "Orden y valores de las columnas" anterior. El orden de las columnas es importante.

Esta consulta SQL se ejecuta en el archivo de base de datos SQLite `pialert.db`.

>  🔎Ejemplo
> 
> SQL query example:
> 
> ```SQL
> SELECT  dv.dev_Name as Object_PrimaryID, 
>     cast(dv.dev_LastIP as VARCHAR(100)) || ':' || cast( SUBSTR(ns.Port ,0, INSTR(ns.Port , '/')) as VARCHAR(100)) as Object_SecondaryID,  
>     datetime() as DateTime,  
>     ns.Service as Watched_Value1,        
>     ns.State as Watched_Value2,
>     'null' as Watched_Value3,
>     'null' as Watched_Value4,
>     ns.Extra as Extra,
>     dv.dev_MAC as ForeignKey 
> FROM 
>     (SELECT * FROM Nmap_Scan) ns 
> LEFT JOIN 
>     (SELECT dev_Name, dev_MAC, dev_LastIP FROM Devices) dv 
> ON ns.MAC = dv.dev_MAC
> ```
> 
> Ejemplo de configuración de `CMD` requerida con la consulta anterior (puede configurar `"type": "label"` si desea que no se pueda editar en la interfaz de usuario):
> 
> ```json
> {
>             "function": "CMD",
>            "type": "text",
>            "default_value":"SELECT  dv.dev_Name as Object_PrimaryID, cast(dv.dev_LastIP as VARCHAR(100)) || ':' || cast( SUBSTR(ns.Port ,0, INSTR(ns.Port , '/')) as VARCHAR(100)) as Object_SecondaryID,  datetime() as DateTime,  ns.Service as Watched_Value1,        ns.State as Watched_Value2,        'null' as Watched_Value3,        'null' as Watched_Value4,        ns.Extra as Extra        FROM (SELECT * FROM Nmap_Scan) ns LEFT JOIN (SELECT dev_Name, dev_MAC, dev_LastIP FROM Devices) dv   ON ns.MAC = dv.dev_MAC",
>            "options": [],
>            "localized": ["name", "description"],
>            "name" : [{
>                "language_code":"en_us",
>                "string" : "SQL to run"
>            }],
>             "description": [{
>                 "language_code":"en_us",
>                 "string" : "This SQL query is used to populate the coresponding UI tables under the Plugins section."
>             }]
>         }
> ```

### "data_source":  "template"

Se utiliza para inicializar la configuración interna. Consulte el plugin `newdev_template` para obtener más detalles.

### "data_source":  "sqlite-db-query"

Puede ejecutar una consulta SQL en una base de datos externa conectada a la base de datos PiALert actual mediante un prefijo temporal `EXTERNAL.`. El archivo de base de datos SQLite externo debe asignarse en el contenedor a la ruta especificada en la configuración `DB_PATH`:

>  🔎Ejemplo
>
>```json
>  ...
>{
>        "function": "DB_PATH",
>        "type": "readonly",
>        "default_value":"/etc/pihole/pihole-FTL.db",
>        "options": [],
>        "localized": ["name", "description"],
>        "name" : [{
>            "language_code":"en_us",
>            "string" : "DB Path"
>        }],
>        "description": [{
>            "language_code":"en_us",
>            "string" : "Required setting for the <code>sqlite-db-query</code> plugin type. Is used to mount an external SQLite database and execute the SQL query stored in the <code>CMD</code> setting."
>        }]    
>    }
>  ...
>```

La consulta SQL real que desea ejecutar se almacena como una configuración "CMD", similar al tipo de complemento "pialert-db-query".

>  🔎Ejemplo
>
> Observe el prefijo "EXTERNO".
>
>```json
>{
>      "function": "CMD",
>      "type": "text",
>      "default_value":"SELECT hwaddr as Object_PrimaryID, cast('http://' || (SELECT ip FROM EXTERNAL.network_addresses WHERE network_id = id ORDER BY lastseen DESC, ip LIMIT 1) as VARCHAR(100)) || ':' || cast( SUBSTR((SELECT name FROM EXTERNAL.network_addresses WHERE network_id = id ORDER BY lastseen DESC, ip LIMIT 1), 0, INSTR((SELECT name FROM EXTERNAL.network_addresses WHERE network_id = id ORDER BY lastseen DESC, ip LIMIT 1), '/')) as VARCHAR(100)) as Object_SecondaryID, datetime() as DateTime, macVendor as Watched_Value1, lastQuery as Watched_Value2, (SELECT name FROM EXTERNAL.network_addresses WHERE network_id = id ORDER BY lastseen DESC, ip LIMIT 1) as Watched_Value3, 'null' as Watched_Value4, '' as Extra, hwaddr as ForeignKey FROM EXTERNAL.network WHERE hwaddr NOT LIKE 'ip-%' AND hwaddr <> '00:00:00:00:00:00';            ",
>      "options": [],
>      "localized": ["name", "description"],
>      "name" : [{
>          "language_code":"en_us",
>          "string" : "SQL to run"
>      }],
>      "description": [{
>          "language_code":"en_us",
>          "string" : "This SQL query is used to populate the coresponding UI tables under the Plugins section. This particular one selects data from a mapped PiHole SQLite database and maps it to the corresponding Plugin columns."
>      }]
>  }
>  ```

## 🕳 Filtros

Las entradas de complementos se pueden filtrar según los valores ingresados en los campos de filtro. El cuadro de texto/campo `txtMacFilter` contiene la dirección Mac del dispositivo actualmente visto o simplemente una dirección Mac que está disponible en la cadena de consulta `mac`.

  | Propiedad | Requerido | Descripción | 
  |----------------------|----------------------|----------------------| 
  | `compare_column` | Sí | El nombre de la columna del complemento cuyo valor se utiliza para comparar (**Lado izquierdo** de la ecuación) |
  | `compare_operator` |  Sí | Operador de comparación de JavaScript |
  | `compare_field_id` | Sí | El `id` de un campo de texto de entrada que contiene un valor se utiliza para comparar (**Lado derecho** de la ecuación)|
  | `compare_js_template` | Sí | Código JavaScript utilizado para convertir el lado izquierdo y derecho de la ecuación. `{valor}` se reemplaza con valores de entrada. |
  | `compare_use_quotes` | Sí | Si es "verdadero", entonces el resultado final de "compare_js_template" lo envolví entre comillas `"`. Úselo para comparar cadenas. |
  

> 🔎Ejemplo:
> 
> ```json
>     "data_filters": [
>         {
>             "compare_column" : "Object_PrimaryID",
>             "compare_operator" : "==",
>             "compare_field_id": "txtMacFilter",
>             "compare_js_template": "'{value}'.toString()", 
>             "compare_use_quotes": true 
>         }
>     ],
> ```

1. En la página `pluginsCore.php` hay un campo de entrada con el ID `txtMacFilter`:

```html
<input class="form-control" id="txtMacFilter" type="text" value="--">
```

2. Este campo de entrada se inicializa mediante la cadena de consulta `&mac=`.

3. Luego, la aplicación procede a utilizar este valor de Mac de este campo y lo compara con el valor del campo de la base de datos `Object_PrimaryID`. El `compare_operator` es `==`.
   
4. Ambos valores, del campo de la base de datos `Object_PrimaryID` y del `txtMacFilter` se empaquetan y evalúan con `compare_js_template`, es decir, `'{value}.toString()'`.

5. `compare_use_quotes` está establecido en `true`, por lo que `'{value}'.toString()` está entre comillas `"`.

6. Esto da como resultado, por ejemplo, este código:

```javascript
    // left part of teh expression coming from compare_column and right from the input field
    // notice the added quotes ()") around the left and right part of teh expression
    "eval('ac:82:ac:82:ac:82".toString()')" == "eval('ac:82:ac:82:ac:82".toString()')"
```

7. Los filtros solo se aplican si se especifica un filtro y `txtMacFilter` no está `indefinido` ni está vacío (`--`).

### 🗺 Mapear los resultados del complemento en una tabla de base de datos

PiAlert tomará los resultados de la ejecución del complemento e insertará estos resultados en una tabla de base de datos, si un complemento contiene la propiedad `"mapped_to_table"` en la raíz `config.json`. El mapeo de las columnas se define en la matriz `database_column_definitions`.

Este enfoque se utiliza para implementar el complemento "DHCPLSS". El script analiza todos los archivos "dhcp.leases" proporcionados, obtiene los resultados en el formato de tabla genérica descrito en la sección "Orden y valores de las columnas" anterior y toma valores individuales y los inserta en la tabla de base de datos `"CurrentScan"` en PiAlert. base de datos. Todo esto se logra mediante:

> [!NOTE] 
> Si los resultados se asignan a la tabla "CurrentScan", los datos se incluyen en el ciclo de escaneo normal, por lo que, por ejemplo, se envían notificaciones para los dispositivos.  

1) Especificar la tabla de la base de datos en la que se insertan los resultados definiendo `"mapped_to_table": "CurrentScan"` en la raíz del archivo `config.json` como se muestra a continuación:

```json
{
    "code_name": "dhcp_leases",
    "unique_prefix": "DHCPLSS",
    ...
    "data_source":  "script",
    "localized": ["display_name", "description", "icon"],
    "mapped_to_table": "CurrentScan",    
    ...
}
```

2) Definir la columna de destino con la propiedad `mapped_to_column` para columnas individuales en la matriz `database_column_definitions` del archivo `config.json`. Por ejemplo, en el complemento `DHCPLSS`, necesitaba asignar el valor de la columna `Object_PrimaryID` devuelta por el complemento a la columna `cur_MAC` en la tabla `CurrentScan` de la base de datos PiAlert. Observe el par clave-valor `"mapped_to_column": "cur_MAC"` en el siguiente ejemplo.

```json
{
            "column": "Object_PrimaryID",
            "mapped_to_column": "cur_MAC", 
            "css_classes": "col-sm-2",
            "show": true,
            "type": "device_mac",            
            "default_value":"",
            "options": [],
            "localized": ["name"],
            "name":[{
                "language_code":"en_us",
                "string" : "MAC address"
                }]
        }
```

3) Eso es todo. PiAlert se encarga del resto. Recorre los objetos descubiertos por el complemento, toma los resultados línea por línea y los inserta en la tabla de la base de datos especificada en `"mapped_to_table"`. Las columnas se traducen de las columnas del complemento genérico a la tabla de destino a través de la propiedad `"mapped_to_column"` en las definiciones de las columnas.

#### Parámetros

La matriz `params` en `config.json` se utiliza para permitir al usuario cambiar los parámetros del script ejecutado. Por ejemplo, el usuario quiere monitorear una URL específica.

> 🔎 Ejemplo:
> Pasar configuraciones definidas por el usuario a un comando. Digamos que desea tener un script que se llame con un parámetro definido por el usuario llamado "urls":
> 
> ```bash
> root@server# python3 /home/pi/pialert/front/plugins/website_monitor/script.py urls=https://google.com,https://duck.com
> ```

* Puede permitir que el usuario agregue URL a una configuración con la propiedad `función` establecida en un nombre personalizado, como `urls_to_check` (este no es un nombre reservado de la sección "Configuraciones admitidas valores de `función`" a continuación).
* Usted especifica el parámetro `urls` en la sección `params` de `config.json` de la siguiente manera (`WEBMON_` es el prefijo del complemento que se agrega automáticamente a todas las configuraciones):
```json
{
    "params" : [
        {
            "name"  : "urls",
            "type"  : "setting",
            "value" : "WEBMON_urls_to_check"
        }]
}
```
* Luego usa esta configuración como parámetro de entrada para su comando en la configuración `CMD`. Observe `urls={urls}` en el siguiente json:

```json
 {
            "function": "CMD",
            "type": "text",
            "default_value":"python3 /home/pi/pialert/front/plugins/website_monitor/script.py urls={urls}",
            "options": [],
            "localized": ["name", "description"],
            "name" : [{
                "language_code":"en_us",
                "string" : "Command"
            }],
            "description": [{
                "language_code":"en_us",
                "string" : "Command to run"
            }]
        }
```

Durante la ejecución del script, la aplicación tomará el comando `"python3 /home/pi/pialert/front/plugins/website_monitor/script.py urls={urls}"`, tomará el comodín `{urls}` y lo reemplazará con el valor de la configuración `WEBMON_urls_to_check`. Esto es porque:
1) La aplicación verifica las entradas de "parámetros".
2) Encuentra `"nombre": "urls"`
3) Comprueba el tipo de parámetros de `urls` y encuentra`"type"  : "setting"`
4) Obtiene el nombre de la configuración de  `"value" : "WEBMON_urls_to_check"` 
   - IMPORTANTE: en `config.json` esta configuración se identifica con `"function":"urls_to_check"`, not `"function":"WEBMON_urls_to_check"`
   - También puedes usar una configuración global o una configuración de un complemento diferente 
5) The app gets the user defined value from the setting with the code name `WEBMON_urls_to_check`
   - digamos la configuración con el nombre en clave `WEBMON_urls_to_check` contiene 2 valores ingresados ​​por el usuario:
   - `WEBMON_urls_to_check=['https://google.com','https://duck.com']`
6) La aplicación toma el valor de `WEBMON_urls_to_check` y reemplaza el comodín `{urls}` en la configuración donde `"function":"CMD"`, por lo que pasas de:
   - `python3 /home/pi/pialert/front/plugins/website_monitor/script.py urls={urls}`
   - to
   - `python3 /home/pi/pialert/front/plugins/website_monitor/script.py urls=https://google.com,https://duck.com` 

A continuación se muestran algunas notas adicionales generales al definir "parámetros":

- `"name":"name_value"` - se utiliza como reemplazo de comodín en el valor de configuración `CMD` mediante el uso de llaves `{name_value}`. El comodín se reemplaza por el resultado de la configuración combinada `"valor": "param_value"` y `"type":"type_value"` a continuación.
- `"type":"<sql|setting>"` - se utiliza para especificar el tipo de parámetros, actualmente solo se admiten 2 (`sql`,`setting`).
  - `"type":"sql"` - ejecutará la consulta SQL especificada en la propiedad `valor`. La consulta SQL debe devolver solo una columna. La columna está aplanada y separada por comas (`,`), por ejemplo: `SELECT dev_MAC from DEVICES` -> `Internet,74:ac:74:ac:74:ac,44:44:74:ac:74:ac `. Luego se usa para reemplazar los comodines en la configuración "CMD".  
  - `"type":"setting"` - El nombre del código de configuración. Una combinación del valor de `unique_prefix` + `_` + valor de `function`, o de lo contrario, el nombre del código que puede encontrar en la página Configuración bajo el nombre para mostrar de configuración, p. `PIHOLE_RUN`.
- `"value" : "param_value"` - Debe contener un nombre de código de configuración o una consulta SQL sin comodines.


> 🔎Ejemplo:
> 
> ```json
> {
>     "params" : [{
>             "name"  : "macs",
>             "type"  : "sql",
>             "value" : "SELECT dev_MAC from DEVICES"
>         },
>         {
>             "name"  : "urls",
>             "type"  : "setting",
>             "value" : "WEBMON_urls_to_check"
>         },
>         {
>             "name"  : "internet_ip",
>             "type"  : "setting",
>             "value" : "WEBMON_SQL_internet_ip"
>         }]
> }
> ```


#### ⚙ Configuración de la estructura del objeto

> [!NOTE] 
> El flujo de configuración y cuándo se aplican las configuraciones específicas del complemento se describen en la sección [Settings system](/docs/SETTINGS_SYSTEM.md).

Los atributos requeridos son:

- `"function": "<see Supported settings function values>"` - ¿Qué función maneja la configuración o un nombre de código único y simple?
- `"type": "<text|integer|boolean|password|readonly|integer.select|text.select|text.multiselect|list|integer.checkbox|text.template>"` - El control de formulario utilizado para la configuración que se muestra en la página Configuración y qué valores se aceptan.
- `"localized"` - una lista de propiedades en el nivel JSON actual que deben localizarse
- `"name"` y `"description"` - Se muestra en la página de Configuración. Una serie de cadenas localizadas. (consulte Cadenas localizadas a continuación).
- (optional) `"events"` - `<test|run>` - para generar un botón de ejecución al lado del campo de entrada de la configuración (no probado completamente)
- (optional) `"override_value"` - se utiliza para determinar una anulación definida por el usuario para la configuración. Útil para complementos basados en plantillas, donde puede optar por dejar el valor actual o anularlo con el valor definido en la configuración. (trabajo en progreso)
- (optional) `"events": ["run", "test"]` - utilizado para activar el complemento. Generalmente se usa en la configuración "EJECUTAR". No probado completamente en todos los escenarios. Mostrará un botón de reproducción al lado de la configuración y luego, después de hacer clic, se generará un evento para el backend en la tabla de la base de datos "Parámetros" para procesar el evento del front-end en la siguiente ejecución.
    
##### Valores de `función` de configuraciones admitidas

Puede tener cualquier nombre personalizado `"function": "my_custom_name"`; sin embargo, los que se enumeran a continuación tienen una funcionalidad específica adjunta. Si usa un nombre personalizado, la configuración se usa principalmente como parámetro de entrada para la sección `params`.

- `RUN` - (requerido) Especifica cuándo se ejecuta el servicio.
    - Opciones soportadas: 
      - "disabled" - no ejecutar
      - "once" - ejecutar al iniciar la aplicación o en la configuración guardada
      - "schedule" - Si se incluye, se debe especificar una configuración `RUN_SCHD` para determinar cuál es el cronograma, 
      - "always_after_scan" - Se ejecuta siempre después de finalizar un escaneo
      - "on_new_device" - Se ejecuta cuando se detecta un nuevo dispositivo
      - "before_config_save" - Se ejecuta antes de que la configuración se marque como guardada. Útil si su complemento necesita modificar el archivo `pialert.conf`.
- `RUN_SCHD` - (requerido si incluye la función `RUN` anterior) La programación tipo cron se utiliza si la configuración `RUN` está establecida en `schedule`
- `CMD` - (requerido) Qué comando se debe ejecutar.
- `API_SQL` - (opcional) Genera una `table_` + code_name  + `.json` archivo según [API docs](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/API.md).
- `RUN_TIMEOUT` - (opcional) Tiempo máximo de ejecución del script. Si no se especifica, se utiliza un valor predeterminado de 10 segundos para evitar que se cuelgue.
- `WATCH` - (opcional) Qué columnas de la base de datos se vigilan en busca de cambios para este complemento en particular. Si no se especifica no se envían notificaciones. 
- `REPORT_ON` - (opcional) Envíe una notificación solo sobre estos estados. Las opciones admitidas son:
  - `new` significa que se descubrió un nuevo objeto único (combinación única de PrimaryId y SecondaryId).
  - `watched-changed` - significa que las columnas seleccionadas `Watched_ValueN` cambiaron
  - `watched-not-changed`  - informes incluso en eventos donde el `Watched_ValueN` seleccionado no cambió
  - `missing-in-last-scan` - si falta el objeto en comparación con escaneos anteriores


> 🔎 Ejemplo:
> 
> ```json
> {
>     "function": "RUN",            
>     "type": "text.select",            
>     "default_value":"disabled",
>     "options": ["disabled", "once", "schedule", "always_after_scan", "on_new_device"],
>     "localized": ["name", "description"],
>     "name" :[{
>         "language_code":"en_us",
>         "string" : "When to run"
>     }],
>     "description": [{
>         "language_code":"en_us",
>         "string" : "Enable a regular scan of your services. If you select <code>schedule</code> the scheduling settings from below are applied. If you select <code>once</code> the scan is run only once on start of the application (container) for the time specified in <a href=\"#WEBMON_RUN_TIMEOUT\"><code>WEBMON_RUN_TIMEOUT</code> setting</a>."
>     }]
> }
> ```

##### 🌍Cadenas localizadas

- `"language_code":"<en_us|es_es|de_de>"`  - nombre de código de la cadena de idioma. Actualmente sólo se admiten estos tres. Al menos se debe definir la variante `"language_code":"en_us"`. 
- `"string"`  - La cadena que se mostrará en el idioma especificado.

> 🔎 Ejemplo:
> 
> ```json
> 
>     {
>         "language_code":"en_us",
>         "string" : "When to run"
>     }
> 
> ```

##### Configuración de la UI en Database_column_definitions

La interfaz de usuario ajustará cómo se muestran las columnas en función de la definición del objeto `database_column_definitions`. Estos son los controles de formulario admitidos y la funcionalidad relacionada:

- Solo las columnas con `"show": true` y también con al menos una traducción al inglés se mostrarán en la interfaz de usuario.
- Tipos soportados: `label`, `text`, `threshold`, `replace`, `device_ip`, `device_mac`, `url`. Consulte los detalles a continuación sobre cómo se comportan las columnas según el tipo.
   - `label` hace que solo se muestre una columna
   - `text` hace que una columna sea editable y se muestra un icono de guardar junto a ella.
   - Consulte a continuación para obtener información sobre "umbral", "reemplazar"
- La propiedad `opciones` se utiliza junto con estos tipos:
  - `threshold` - La matriz `opciones` contiene objetos desde el `máximo` más bajo hasta el más alto con el `hexColor` correspondiente usado para el color de fondo del valor si es menor que el `máximo` especificado, pero mayor que el anterior en la matriz `opciones`
  - `replace` - La matriz `opciones` contiene objetos con una propiedad `equals`, que se compara con el "valor" y si los valores son los mismos, la cadena en "reemplazo" se muestra en la interfaz de usuario en lugar del "valor" real
- `device_mac` - El valor se considera una dirección Mac y se genera un enlace que apunta al dispositivo con la dirección Mac proporcionada.
- `device_ip` - El valor se considera una dirección IP y se genera un enlace que apunta al dispositivo con la IP dada. La IP se compara con las últimas direcciones IP detectadas y se traduce a una dirección Mac que luego se usa para el enlace en sí.
- `url` - El valor se considera una URL por lo que se genera un enlace.
- `textbox_save` - Se genera un cuadro de texto editable y guardable que guarda los valores en la base de datos. Diseñado principalmente para la columna de base de datos "UserData" en la tabla "Plugins_Objects".


```json
{
            "column": "Watched_Value1",
            "css_classes": "col-sm-2",
            "show": true,
            "type": "threshold",            
            "default_value":"",
            "options": [
                {
                    "maximum": 199,
                    "hexColor": "#792D86"                
                },
                {
                    "maximum": 299,
                    "hexColor": "#5B862D"
                },
                {
                    "maximum": 399,
                    "hexColor": "#7D862D"
                },
                {
                    "maximum": 499,
                    "hexColor": "#BF6440"
                },
                {
                    "maximum": 599,
                    "hexColor": "#D33115"
                }
            ],
            "localized": ["name"],
            "name":[{
                "language_code":"en_us",
                "string" : "Status code"
                }]
        },        
        {
            "column": "Status",
            "show": true,
            "type": "replace",            
            "default_value":"",
            "options": [
                {
                    "equals": "watched-not-changed",
                    "replacement": "<i class='fa-solid fa-square-check'></i>"
                },
                {
                    "equals": "watched-changed",
                    "replacement": "<i class='fa-solid fa-triangle-exclamation'></i>"
                },
                {
                    "equals": "new",
                    "replacement": "<i class='fa-solid fa-circle-plus'></i>"
                }
            ],
            "localized": ["name"],
            "name":[{
                "language_code":"en_us",
                "string" : "Status"
                }]
        }
```



[screen1]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins.png                    "Screen 1"
[screen2]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins_settings.png           "Screen 2"
[screen3]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins_json_settings.png      "Screen 3"
[screen4]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins_json_ui.png            "Screen 4"
[screen5]: https://raw.githubusercontent.com/jokob-sk/Pi.Alert/main/docs/img/plugins_device_details.png     "Screen 5"
