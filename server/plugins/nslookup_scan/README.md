## Overview

Plugin for device name discovery via reverse DNS (PTR) lookups, using the [nslookup](https://linux.die.net/man/1/nslookup) utility. Runs against IPs already discovered by a device scanner - it doesn't discover devices itself, only tries to attach a name to ones that don't have one yet. Functionally similar to `DIGSCAN` (both do a reverse DNS lookup, just via a different tool) - enabling both is redundant, pick whichever behaves better against your DNS server.

### Usage

- Check the Settings page for details.

### Notes

- See the [Name resolution guide](https://docs.netalertx.com/NAME_RESOLUTION) for how this fits alongside the other naming plugins (`AVAHISCAN`, `NBTSCAN`, `DIGSCAN`).
