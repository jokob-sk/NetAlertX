# Subnets configuration for arp-scan

You need to specify the network interface and the network mask. You can also configure multiple subnets and specify VLANS (see exceptions below).

## Examples

* Examples for one and two subnets  (❗ Note the `['...', '...']` format):
   * One subnet: `SCAN_SUBNETS    = ['192.168.1.0/24 --interface=eth0']`
   * Two subnets:  `SCAN_SUBNETS    = ['192.168.1.0/24 --interface=eth0', '192.168.1.0/24 --interface=eth1 -vlan=107']` 

## Explanation

### Network mask

**Example value: `192.168.1.0/24`**

The arp-scan time itself depends on the number of IP addresses to check. 

> The number of IPs to check depends on the [network mask](https://www.calculator.net/ip-subnet-calculator.html) you set on the `SCAN_SUBNETS` setting. 
> For example, a `/24` mask results in 256 IPs to check, whereas a `/16` mask checks around 65,536. Every IP takes a couple of seconds. This means that with an incorrect configuration, the arp-scan will take hours to complete instead of seconds.

Specify the network filter (which **significantly** speeds up the scan process). For example, the filter `192.168.1.0/24` covers IP ranges 192.168.1.0 to 192.168.1.255.

### Network interface (adapter)

**Example value: `--interface=eth0`**

The adapter will probably be `eth0` or `eth1`. (Run `iwconfig` in the container to find your interface name(s)) 

> Run `iwconfig` in your container to find your interface name(s) (e.g.: `eth0`, `eth1`). 

### VLANs

**Example value: `-vlan=107`**

- Append e.g.: ` -vlan=107` to the interface field (e.g.: `eth0 -vlan=107`) for multiple vlans. More details in this [comment in this issue](https://github.com/jokob-sk/Pi.Alert/issues/170#issuecomment-1419902988)

#### VLAN 🔍Example:

![Vlan configuration example](/docs/img/SUBNETS/subnets_vlan.png)

#### Support for VLANS (& exceptions)

Please note the accessibility of the macvlans when they are configured on the same computer. My understanding this is a general networking behavior, but feel free to clarify via a PR/issue.

- Pi.Alert does not detect the macvlan container when it is running on the same computer.
- Pi.Alert recognizes the macvlan container when it is running on a different computer.

