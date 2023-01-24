## How to setup your Network page

Make sure you have a root device with the MAC `Internet` (No other MAC addresses are currently support as root)

To setup a device named `rapberrypi` as a `Switch` in our network. 

### 1) Device details page

- Go to the `Devices` (1) page:

![Device details](/docs/img/NETWORK_TREE/Device_Details_Network_Type.png)

- In the (2) `Details` tab navigate to the the `Type` (3) dropdown and select the type `Switch` (4).

> Note: Only the following device types will show up as selectable Network nodes ( = devices you can connect other devices to):
> AP, Firewall, Gateway, PLC, Powerline, Router, Switch, USB LAN Adapter, USB WIFI Adapter and WLAN.

- Assign a device to your root device from the `Node` (5) dropdown whitch has the MAC `Internet` (6) (Your name may differ, but the MAC needs to be set to `Internet` - this is done by default). 

- Save your changes (7)

### 1) Network page

- Navigate to your `Network` (1) page:

![Network page](/docs/img/NETWORK_TREE/Network_Page.png)

- Notice the newly added `raspberrypi` (2) tab which now represents a network node, also showing up in the tree (3).
- As we asssigned the `raspberrypi` in the previous 1) Device details page section to the `Internet` parent network node in step (6), the link is also showing up in the tree diagram (4)
- We can now assign the device `(AppleTV)` (5) to this `raspberrypi` node, representing a network Switch in this example

### 1) Network page with 2 levels

- After clicking the `Assign` button in the previous section, the `(AppleTV)` (1) device is now connected to our `raspberrypi` (2).

![Network page with 2 levels](/docs/img/NETWORK_TREE/Network_Page_2_Levels.png)

- You can see the `raspberrypi` represents the Network node type `Switch` (3)
- The `(AppleTV)` to `raspberrypi` connection is also displayed in the table of `Connected devices` (4).
- You can also see that our `raspberrypi` node is connected to it's Parent network device node with the MAC `Internet` (5). This connection again shows up in the tree (6) as well.



