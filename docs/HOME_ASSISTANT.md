# Home Assistant integration

NetAlertX includes MQTT support, allowing detected devices to appear as devices in Home Assistant. It also publishes various statistics, such as the number of online devices.

> [!TIP]
> You can also install NetAlertX as a Home Assistant Add-on via the [![Home Assistant](https://img.shields.io/badge/Repo-blue?logo=home-assistant\&style=for-the-badge\&color=0aa8d2\&logoColor=fff\&label=Add)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Falexbelgium%2Fhassio-addons) from the [alexbelgium/hassio-addons](https://github.com/alexbelgium/hassio-addons/) repository. This is only available for supervised Home Assistant installations. If you're running Home Assistant Container or Home Assistant Core, you can instead run NetAlertX in a separate Docker container. 

> [!WARNING]
>
> * Device discovery in Home Assistant takes approximately 10 seconds **per device**.
> * Devices removed from NetAlertX are not automatically removed from Home Assistant. Use [MQTT Explorer](https://mqtt-explorer.com/) to delete them from the MQTT broker if required.
> * For performance reasons, device definitions are not always fully synchronized. To force a complete synchronization, delete the MQTT Plugin Objects as described in the [MQTT plugin](https://docs.netalertx.com/plugins/_publisher_mqtt#forcing-an-update) documentation.

## Mosquitto MQTT setup

1. Enable the Mosquitto MQTT integration in Home Assistant by following the [official documentation](https://www.home-assistant.io/integrations/mqtt/).
2. Create an MQTT username and password on your broker.
3. Record the following information for configuring NetAlertX:

   * MQTT host URL (usually your Home Assistant IP address)
   * MQTT broker port
   * Username
   * Password

4. Open **NetAlertX** → **Settings** → **MQTT**.

   * Enable MQTT.
   * Enter the broker details from the previous step.
   * Configure the remaining settings as needed.
   * Set `MQTT_RUN` to either `schedule` or `on_notification`, depending on your requirements.

![Configuration Example][configuration]

### Screenshots

| ![Screen 1][sensors] | ![Screen 2][history]  |
| -------------------- | --------------------- |
| ![Screen 3][list]    | ![Screen 4][overview] |

[configuration]: ./img/HOME_ASSISTANT/HomeAssistant-Configuration.png "configuration"
[sensors]: ./img/HOME_ASSISTANT/HomeAssistant-Device-as-Sensors.png "sensors"
[history]: ./img/HOME_ASSISTANT/HomeAssistant-Device-Presence-History.png "history"
[list]: ./img/HOME_ASSISTANT/HomeAssistant-Devices-List.png "list"
[overview]: ./img/HOME_ASSISTANT/HomeAssistant-Overview-Card.png "overview"

## Troubleshooting

### Missing devices

If some devices do not appear in Home Assistant, first verify that NetAlertX can detect them by running:

```bash
sudo arp-scan --interface=eth0 192.168.1.0/24
```

Replace the interface and subnet with values appropriate for your environment (see the [Subnets](./SUBNETS.md) documentation).

Run this command **inside the NetAlertX container**, not inside the Home Assistant container.

### Accessing the NetAlertX container

You can access the NetAlertX container via Portainer on your host or via SSH. The container name will be something like `addon_db21ed7f_netalertx` (you can copy the `db21ed7f_netalertx` part from the browser URL when accessing the NetAlertX web interface).

1. Log into your Home Assistant host via SSH.

```bash
local@local:~ $ ssh pi@192.168.1.9
```

2. Find the NetAlertX container name.

```bash
pi@raspberrypi:~ $ sudo docker container ls | grep netalertx
06c540d97f67   ghcr.io/alexbelgium/netalertx-armv7:25.3.1                   "/init"               6 days ago      Up 6 days (healthy)    addon_db21ed7f_netalertx
```

3. Open a shell inside the NetAlertX container.

```bash
pi@raspberrypi:~ $ sudo docker exec -it addon_db21ed7f_netalertx /bin/sh
/ #
```

4. Run a test `arp-scan`.

```bash
/ # sudo arp-scan --ignoredups --retry=6 192.168.1.0/24 --interface=eth0
Interface: eth0, type: EN10MB, MAC: dc:a6:32:73:8a:b1, IPv4: 192.168.1.9
Starting arp-scan 1.10.0 with 256 hosts (https://github.com/royhills/arp-scan)
192.168.1.1     74:ac:b9:54:09:fb       Ubiquiti Networks Inc.
192.168.1.21    74:ac:b9:ad:c3:30       Ubiquiti Networks Inc.
192.168.1.58    1c:69:7a:a2:34:7b       EliteGroup Computer Systems Co., LTD
192.168.1.57    f4:92:bf:a3:f3:56       Ubiquiti Networks Inc.
...
```

If your output does not contain devices similar to those shown above, verify that your subnet configuration is correct (see the [Subnets](./SUBNETS.md) documentation), that you are scanning the correct network interface, and that the network segment is reachable. If the devices are located on a different or remote network, refer to the [Remote Networks](./REMOTE_NETWORKS.md) documentation.
