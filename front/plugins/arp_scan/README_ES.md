## Descripción general

Arp-scan es una herramienta de línea de comandos que utiliza el protocolo ARP para descubrir y tomar huellas digitales de hosts IP en la red local. Una alternativa al escaneo ARP es habilitar la configuración de integración de PiHole `PIHOLE_RUN`. El tiempo de arp-scan (y otros tiempos del complemento de escaneo de red que utilizan la configuración `SCAN_SUBNETS`) depende de la cantidad de direcciones IP a verificar, así que configúrelo cuidadosamente con la interfaz y la máscara de red adecuadas. Consulte la [documentación de subredes](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/SUBNETS.md) para obtener ayuda sobre cómo configurar VLAN, qué VLAN son compatibles o cómo averiguarlo. la máscara de red y su interfaz.

### Uso

- Vaya a la configuración y establezca la configuración `SCAN_SUBNETS` según la [documentación de subredes](https://github.com/jokob-sk/Pi.Alert/blob/main/docs/SUBNETS.md).
- Habilite el complemento cambiando el parámetro RUN de deshabilitado a su tiempo de ejecución preferido (generalmente: `schedule`).
  - Especifique el horario en la configuración `ARPSCAN_RUN_SCHD`
- Ajuste el tiempo de espera si es necesario en la configuración `ARPSCAN_RUN_TIMEOUT`
- Revisar las configuraciones restantes
- Guardar
- Espere a que finalice el siguiente escaneo.
