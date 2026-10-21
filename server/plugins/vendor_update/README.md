## Overview

Keeps the local MAC-vendor lookup database current by downloading the [IEEE OUI registry](http://standards-oui.ieee.org/oui/oui.txt), then re-resolves the vendor for any device whose vendor is still unknown. This is what fills in the `devVendor` field for devices your scanners couldn't already identify.

### Usage

- Check the Settings page for details. A daily or weekly `schedule` is plenty - the OUI registry doesn't change often enough to warrant running this on every scan.
