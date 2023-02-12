## Subnets configuration

The arp-scan time itself depends on the number of IP addresses to check. 
The number of IPs to check depends on the [network mask](https://www.calculator.net/ip-subnet-calculator.html) you set on the `SCAN_SUBNETS` setting. 

For example, a `/24` mask results in 256 IPs to check, where as a `/16` mask checks around 65,536. Every IP takes a couple seconds. This means that with an incorrect configuration the arp-scan will take hours to complete instead of seconds.

- Specify the network mask. For example, the filter `192.168.1.0/24` covers IP ranges 192.168.1.0 to 192.168.1.255
- Run `iwconfig` in your container to find your interface name(s) (e.g.: `eth0`, `eth1`). 
- Append e.g.: ` -vlan=107` to the interface field (e.g.: `eth0 -vlan=107`) for multiple vlans. More details in this [issue](https://github.com/jokob-sk/Pi.Alert/issues/170)