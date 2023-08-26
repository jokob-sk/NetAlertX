## Descripción general

Un plugin para resolver nombres de dispositivos "(desconocidos)". Utiliza la herramienta de rastreo [Pholus](https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins/pholus_scan/pholus).

### Uso

- Vaya a configuración y busque Pholus-Scan (descubrimiento de nombre) en la lista de configuraciones.
- Habilite el complemento cambiando el parámetro `RUN` de deshabilitado a uno que prefiera (`schedule`, `always_after_scan`, `on_new_device`).
- Especifique `PHOLUS_RUN_TIMEOUT` (se dividirá por el número de subredes especificadas en la configuración del complemento Arp-Scan (escaneo de red) `SCAN_SUBNETS`)
- GUARDAR
- Espere a que finalice el siguiente escaneo.
