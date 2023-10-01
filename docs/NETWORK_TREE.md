## How to setup your Network page

Make sure you have a root device with the MAC `Internet` (No other MAC addresses are currently supported as the root node).

> 💡 Tip: You can add dummy devices via the [Undiscoverables plugin](https://github.com/jokob-sk/Pi.Alert/blob/main/front/plugins/undiscoverables/README.md)

> 💡 Tip: Export your configuration of the Network and Devices once in a while via the Export CSV feature under **Maintenance** -> **Backup/Restore** -> **CSV Export**.   

## ⚡Quick setup:

* Go to Devices > Device Details. 
* Find the device(s) you want to use as network devices (network nodes). 
* Set the Type of such a device to one of the following: AP, Firewall, Gateway, PLC, Powerline, Router, Switch, USB LAN Adapter, USB WIFI Adapter and WLAN.
* Save and go to Network where the devices you've marked as network devices (by selecting the Type as mentioned above) will show up as tabs.
* You can now assign the Unassigend devices to the correct network node.
* If port is empty or 0 a wifi icon is rendered, otherwise a ethernet port icon


> [!NOTE] 
>
> [Bulk-edit devices](/docs/DEVICES_BULK_EDITING.md) by using the `CSV Export` functionality in the `Maintenance` section. You can use this to fix `Internet` node assignment issues. 

## 🔍Detailed example:

In this example you will setup a device named `rapberrypi` as a `Switch` in our network. 

### 1. Device details page

- Go to the `Devices` (1) page:

![Device details](/docs/img/NETWORK_TREE/Device_Details_Network_Type.png)

- In the (2) `Details` tab navigate to the the `Type` (3) dropdown and select the type `Switch` (4).

> Note: Only the following device types will show up as selectable Network nodes ( = devices you can connect other devices to):
> AP, Firewall, Gateway, Hypervisor, PLC, Powerline, Router, Switch, USB LAN Adapter, USB WIFI Adapter and WLAN. Custom types can be added via the `NETWORK_DEVICE_TYPES` setting.

- Assign a device to your root device from the `Node` (5) dropdown which has the MAC `Internet` (6) (Your name may differ, but the MAC needs to be set to `Internet` - this is done by default). 

- Save your changes (7)

### 2. Network page

- Navigate to your `Network` (1) page:

![Network page](/docs/img/NETWORK_TREE/Network_Page.png)

- Notice the newly added `raspberrypi` (2) tab which now represents a network node, also showing up in the tree (3).
- As we asssigned the `raspberrypi` in the previous 1) Device details page section to the `Internet` parent network node in step (6), the link is also showing up in the tree diagram (4)
- We can now assign the device `(AppleTV)` (5) to this `raspberrypi` node, representing a network Switch in this example

### 3. Network page with 2 levels

- After clicking the `Assign` button in the previous section, the `(AppleTV)` (1) device is now connected to our `raspberrypi` (2).

![Network page with 2 levels](/docs/img/NETWORK_TREE/Network_Page_2_Levels.png)

- You can see the `raspberrypi` represents the Network node type `Switch` (3)
- The `(AppleTV)` to `raspberrypi` connection is also displayed in the table of `Connected devices` (4).
- You can also see that our `raspberrypi` node is connected to it's Parent network device node with the MAC `Internet` (5). This connection again shows up in the tree (6) as well.




