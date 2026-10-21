# Scanning Remote or Inaccessible Networks

> [!TIP]
> If a device responds to `ping` but does not appear in NetAlertX, the most common cause is that the device is located on a different Layer-2 segment, behind a Wi-Fi extender, VPN, VLAN, or router. In these cases, `arp-scan` may not be able to discover it even though IP connectivity exists.

By design, local network scanners such as `arp-scan` use ARP (Address Resolution Protocol) to map IP addresses to MAC addresses on the local network. Since ARP operates at Layer 2 (Data Link Layer), it **typically works only within a single broadcast domain**, usually limited to a single router or network segment.

> [!NOTE]
> `ping` and `arp-scan` use different protocols so even if you can ping devices it doesn't mean the `ARPSCAN` plugin can detect them.

To scan multiple **locally accessible network segments**, add them as subnets according to the [subnets](./SUBNETS.md) documentation. If `ARPSCAN` is not suitable for your setup, read on.

## Complex Use Cases

The following network setups can prevent the `ARPSCAN` plugin from discovering some devices. Review the relevant section below to understand the limitations and available workarounds.

### Wi-Fi Extenders

Wi-Fi extenders often **block or proxy Layer-2 broadcast traffic**, which can prevent network scanning tools like `arp-scan` from detecting devices behind the extender. This can happen **even when the extender uses the same SSID and the same IP subnet** as the main network.

> [!IMPORTANT]
> Please note that being able to `ping` a device does **not** mean it is discoverable via `arp-scan`.
>
> * `arp-scan` relies on **Layer 2 (ARP broadcast)**
> * ICMP (`ping`) operates at **Layer 3 (routed traffic)**

Devices behind extenders may respond to ping but remain undiscoverable via `arp-scan`.

#### Workaround: Wi-Fi Extenders

If the extender uses a separate subnet, scan that subnet directly. See the [subnets](./SUBNETS.md) documentation for details. Otherwise, use DHCP-based discovery plugins or router integration instead of relying only on the `ARPSCAN` plugin. See the **Other Workarounds** section below for more details.

### VPNs

The `arp-scan` utility operates at Layer 2 (Data Link Layer) and works only within a local area network (LAN). VPNs, which operate at Layer 3 (Network Layer), route traffic between networks, preventing ARP requests from discovering devices outside the local network.

VPNs use virtual interfaces (e.g., `tun0`, `tap0`) to encapsulate traffic, bypassing ARP-based discovery. Additionally, many VPNs use NAT, which masks individual devices behind a shared IP address.

#### Workaround: VPNs 

In some cases, configuring the VPN in bridge mode instead of routed mode can allow ARP traffic to pass. Whether this is possible depends on the VPN technology and your security requirements.

### VLANs

VLANs create separate Layer-2 broadcast domains. Devices on a different VLAN may be reachable via routing and respond to `ping`, but they typically cannot be discovered by `arp-scan`.

#### Workaround: VLANs

Configure the VLAN subnet in the [subnets](./SUBNETS.md) settings if the network is locally accessible, or use one of the alternative discovery methods described below.

## Other Workarounds

The following workarounds should work for most complex network setups.

### Workaround: Supplementing Plugins

Using supplementing plugins that employ alternate discovery methods is one of the easiest ways to extend your scan coverage. Protocols used by the `SNMPDSC` or `DHCPLSS` plugins are widely supported on different routers and can be effective as workarounds. Check the [plugins list](./PLUGINS_OVERVIEW.md) to find a plugin that works with your router and network setup.

### Workaround: Multiple NetAlertX Instances if you have servers in all networks

If you have servers in different networks, you can set up separate NetAlertX instances on those subnets and synchronize the results into one instance using the [`SYNC` plugin](https://docs.netalertx.com/plugins/sync).

> [!TIP]
> The [`SYNC_BEHAVIOR`](https://docs.netalertx.com/plugins/sync#hub-device-write-behavior-sync_behavior) setting controls how the hub handles newly discovered devices from nodes - whether it inherits node config, overwrites on every sync, or applies its own `NEWDEV` defaults.

### Workaround: Manual Entry for devices you can `ping`

If you don't need to discover new devices in unreachable networks, and only need to report on their status (`online`, `offline`, `down`), you can manually enter devices, with their actual IP address, and check their status using the [`ICMP` plugin](https://github.com/netalertx/NetAlertX/blob/main/server/plugins/icmp_scan/), which uses the `ping` command internally.

> [!TIP]
> For more information on how to add devices manually (or dummy devices), refer to the [Device Management](./DEVICE_MANAGEMENT.md) documentation.

Dummy devices can also be used to segment your network topology, or to represent an unmanaged device. These devices usually can't be scanned, but you can still make them appear online by using the `Force Status` field on the device to force a specific status.

### Workaround: NMAP and Fake MAC Addresses for devices with a static IP

Scanning remote networks with NMAP is possible (via the `NMAPDEV` plugin), but since it cannot retrieve the MAC address, you need to enable the `NMAPDEV_FAKE_MAC` setting. This will generate a fake MAC address based on the IP address, allowing you to track devices. 

Because the generated MAC address is derived from the IP address, changing the IP can cause the device to appear as a new device or create duplicate records. If this setting is disabled, devices with a missing MAC addresses will be skipped.

Check the [NMAPDEV plugin](https://docs.netalertx.com/plugins/nmap_dev_scan) for details.
