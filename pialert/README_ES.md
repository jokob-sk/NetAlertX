# Módulos Pi.Alert

El código pilaert.py original ahora se mueve a esta nueva carpeta y se divide en diferentes módulos.

| Módulo | Descripción |
|--------|-----------|
|```__main__.py```| El programa PRINCIPAL de Pi.Alert|
|```__init__.py```| Un archivo init vacío|
|```README.md```| Versión en inglés del readme|
|```README_ES.md```| Versión en castellano del readme|
|**publishers**| Una carpeta que contiene todos los módulos utilizados para publicar los resultados|
|**scanners**| Una carpeta que contiene todos los módulos utilizados para buscar dispositivos |
|```api.py```| Actualización de los puntos finales de la API con los datos pertinentes. (Debería trasladarse a los editores)|
|```const.py```| Un lugar para definir las constantes para Pi.Alert como la ruta de registro o la ruta de configuración.|
|```conf.py```| conf.py contiene las variables de configuración y las pone a disposición de todos los módulos. También es la <b>solución</b> para variables globales que deben resolverse en algún momento.|
|```database.py```| Este módulo se conecta a la BD, se asegura de que la BD está actualizada y define algunas consultas e interfaces estándar |
|```device.py```| El módulo de dispositivos se ocupa de los dispositivos y guarda los resultados de la exploración en los dispositivos |
|```helper.py```| Helper como su nombre indica contiene múltiples pequeñas funciones y métodos utilizados en muchos de los otros módulos y ayuda a mantener las cosas limpias |
|```initialise.py```| Initiatlise prepara el entorno y deja todo listo para funcionar |
|```logger.py```| Logger está ahí para mantener todos los registros organizados y con el mismo aspecto |
|```networscan.py```| El escaneado de red organiza el escaneado real de la red, llamando a los escáneres individuales y gestionando los resultados |
|```plugin.py```| Aquí es donde los plugins se integran en el backend de Pi.Alert |
|```reporting.py```| La generación de informes genera los informes de correo electrónico, html y json que deben enviar los editores |
|```scheduler.py```| Todo sobre la planificación |


