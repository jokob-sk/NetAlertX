## Overview

Plugin for device name discovery via the [nbtscan](https://linuxcommandlibrary.com/man/nbtscan) network utility, using NetBIOS. Runs against IPs already discovered by a device scanner - it doesn't discover devices itself, only tries to attach a name to ones that don't have one yet. Mainly useful for older/Windows-family devices that respond to NetBIOS name queries; most modern devices won't.

### Usage

- Check the Settings page for details.

### Notes

- See the [Name resolution guide](https://docs.netalertx.com/NAME_RESOLUTION) for how this fits alongside the other naming plugins (`AVAHISCAN`, `NSLOOKUP`, `DIGSCAN`).
