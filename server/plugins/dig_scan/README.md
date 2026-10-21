## Overview

Plugin for device name discovery via reverse DNS (PTR) lookups, using the [dig](https://linux.die.net/man/1/dig) utility (`dig +short -x <ip>`). Runs against IPs already discovered by a device scanner - it doesn't discover devices itself, only tries to attach a name to ones that don't have one yet. Functionally similar to `NSLOOKUP` (both do a reverse DNS lookup, just via a different tool) - enabling both is redundant, pick whichever behaves better against your DNS server.

### Usage

- Check the Settings page for details.

### Notes

- Only useful if your network's DNS server actually has PTR records for local devices (e.g. via your router's DHCP-to-DNS integration); many home networks don't, in which case this plugin will find little to nothing.
- See the [Name resolution guide](https://docs.netalertx.com/NAME_RESOLUTION) for how this fits alongside the other naming plugins (`AVAHISCAN`, `NBTSCAN`, `NSLOOKUP`).
