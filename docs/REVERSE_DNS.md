## Setting up better name discovery with Reverse DNS

If you are running a DNS server, such as AdGuard, set up **Private reverse DNS servers** for a better name resolution on your network. Enabling this setting will enable PiAlert to execute dig and nslookup comamnds to automatically resolve device names based on their IP addresses.

> Example 1: Reverse DNS `disabled`
> 
> ```
> jokob@Synology-NAS:/$ nslookup 192.168.1.58
> ** server can't find 58.1.168.192.in-addr.arpa: NXDOMAIN
> 
> ```

> Example 2: Reverse DNS `enabled`
> 
> ```
> jokob@Synology-NAS:/$ nslookup 192.168.1.58
> 45.1.168.192.in-addr.arpa       name = jokob-NUC.localdomain.
> ```

### Enabling reverse DNS in AdGuard

1. Navigate to **Settings** ->  **DNS Settings**
2. Locate **Private reverse DNS servers**
3. Enter your router IP address, such as `192.168.1.1`
4. Make sure you have **Use private reverse DNS resolvers** ticked.
5. Click **Apply** to save your settings.

