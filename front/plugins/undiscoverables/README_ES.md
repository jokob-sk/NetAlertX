## Descripción general

Un plugin que permite importar dispositivos no detectables desde la página de configuración.
El caso de uso principal es agregar equipos de red tontos, como concentradores y conmutadores no administrados, a la vista de red.
Puede haber otros casos de uso, hágamelo saber.

### Uso

- Vaya a configuración y busque Dispositivos no descubiertos en la lista de complementos.
- Habilite el complemento cambiando el parámetro RUN de deshabilitado a "once" o "always_after_scan".
- Añade el nombre de tu dispositivo a la lista. (elimine primero la entrada de muestra)
- GUARDAR
- Espere a que finalice el siguiente escaneo

#### Ejemplos:
Ajustes:
![configuración](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/52883307-19a5-4602-b13a-9825461f6cc4)

Resultado en dispositivos:
![dispositivos](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/9f7659e7-75a8-4ae9-9f5f-781bdbcbc949)

Permitir que dispositivos no detectables como concentradores, conmutadores o AP se agreguen a la vista de red.
![red](https://github.com/Data-Monkey/Pi.Alert/assets/7224371/b5ccc3b3-f5fd-4f5b-b0f0-e4e637c6da33)

### Limitaciones conocidas
  - Los dispositivos no detectables siempre se muestran sin conexión. Esto es de esperar, ya que Pi.Alert no puede descubrirlos.
  - Todas las IP están configuradas en 0.0.0.0, por lo que es posible que aparezca el icono "MAC aleatoria".
