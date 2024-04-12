## Icons overview

Icons are used to visually distinguish devices in the app in most of the device listing tables and the [network tree](/docs/NETWORK_TREE.md). 

![Raspberry Pi with a brand icon](/docs/img/ICONS/devices-icons.png)

### Icons Support

Two types of icons are suported:

- Free [Font Awesome](https://fontawesome.com/search?o=r&m=free) icons (up-to v 6.4.0)
- SVG icons 

You can assign icons individually on each device in the Details tab.

## Adding new icons

1. You can get an SVG or a Font awesome HTML code

Copying the SVG (for example from [iconify.design](https://icon-sets.iconify.design/)): 

![iconify svg](/docs/img/ICONS/iconify_design_copy_svg.png)

Copying the HTML code from [Font Awesome](https://fontawesome.com/search?o=r&m=free).

![Font awesome](/docs/img/ICONS/font_awesome_copy_html.png)

2. Navigate to the device you want to use the icon on and click the "+" icon:

![preview](/docs/img/ICONS/device_add_icon.png)

3. Paste in the copied HTML or SVG code.

4. Click "OK"

5. "Save" the device

> [!NOTE] 
> If you want to mass-apply an icon to all devices of the same device type (Field: Type), you can click the mass-copy button (next to the "+" button). A confirmation prompt is displayed. If you proceed, icons of all devices set to the same device type as the current device, will be overwritten with the current device's icon.

- The blue dropdown contains all icons already used in the app for device icons. You need to navigate away or refresh the page once you add a new icon. 

## 🌟 Pro Font Awesome icons

If you own the premium package of Font Awesome icons you can mount it in your Docker container the following way:

```yaml
/font-awesome:/app/front/lib/AdminLTE/bower_components/font-awesome:ro
```

You can use the full range of Font Awesome icons afterwards. 
