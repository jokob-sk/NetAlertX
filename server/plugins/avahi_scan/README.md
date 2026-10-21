## Overview

Plugin for device name discovery via the [avahi](https://wiki.alpinelinux.org/wiki/MDNS) network utility, using mDNS. Runs against IPs already discovered by a device scanner - it doesn't discover devices itself, only tries to attach a name to ones that don't have one yet. Generally the most reliable naming source for local devices that advertise themselves over mDNS (most consumer IoT, Apple/Chromecast-style devices).

### Usage

- Check the Settings page for details.

### Notes

- See the [Name resolution guide](https://docs.netalertx.com/NAME_RESOLUTION) for how this fits alongside the other naming plugins (`NBTSCAN`, `NSLOOKUP`, `DIGSCAN`).
