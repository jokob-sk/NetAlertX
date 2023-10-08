## Icons overview

Icons are used to visually distinguish devices in the app in most of the device listing tables and the [network tree](/docs/NETWORK_TREE.md). Currently only free [Font Awesome](https://fontawesome.com/search?o=r&m=free) icons (up-to v 6.4.0) are supported.

![Raspberry Pi with a brand icon](/docs/img/ICONS/devices-icons.png)

## ⚙ How to use custom device Icons

You can assign icons individually on each device in the Details tab.

![preview](/docs/img/ICONS/device_icons_preview.gif)

![Raspberry Pi device details](/docs/img/ICONS/device-icon.png)

- You can click into the `Icon` field or click the Pencil (2) icon in the above screenshot to enter any text. Only [free Font Awesome](https://fontawesome.com/search?o=r&m=free) icons in the following format will work:

  1. For any value that is only prefixed with `fa-`, you can enter the value directly, such as `server`, `tv`, `ethernet`. 
  2. If you want to add another classname, e.g. `fa-brands`, you can enter `brands fa-[fontawesome-icon-name]`, so for `apple` that is using the syntax`fa-brands fa-apple`, you would enter `brands fa-apple`.

- If you want to mass-apply an icon to all devices of the same device type (Field marked (4) in the above screenshot), you can click the copy button (Marked (1) in the above screenshot). A confirmation prompt is displayed. If you proceed, icons of all devices set to the same device type as the current device, will be overwritten with the current device's icon.

- The dropdown (3) contains all icons already used in the app for device icons. You need to navigate away or refresh the page once you add a new icon. 

## 🌟 Pro Font Awesome icons

If you own the premium package of Font Awesome icons you can mount it in your Docker container the following way:

```yaml
/font-awesome:/home/pi/pialert/front/lib/AdminLTE/bower_components/font-awesome:ro
```

You can use the full range of Font Awesome icons afterwards. 
