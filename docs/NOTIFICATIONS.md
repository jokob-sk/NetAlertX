# Notifications 📧

There are 3 ways how to influence notifications:

1. On the device itself
2. On the settings of the plugin
3. Globally
4. Ignoring devices


## Device settings 💻

![Device notification settings](/docs/img/NOTIFICATIONS/Device-notification-settings.png)

There are 4 settings on the device for influencing notifications. You can:

1. Completely disable the scanning of the device
2. **Alert all events**, connections, disconnections, IP changes (noisy, usually not recommended)
3. **Alert down** - alerts when a device goes down. This setting overrides disabled Alert All Events, so you will get a notification of a device going down even if you don't have Alert All Events ticked.
4. **Skip repeated notifications**, if for example you know there is a temporary issue and want to pause the same notification for this device for a given time.

## Plugin settings 🔌

![Plugin notification settings](/docs/img/NOTIFICATIONS/Plugin-notification-settings.png)

On almost all plugins there are 2 core settings, `<plugin>_WATCH` and `<plugin>_REPORT_ON`. 

1. `<plugin>_WATCH` specifies the columns which the app should watch. If watched columns change the device state is considered changed. This changed status is then used to decide to send out notifications based on the `<plugin>_REPORT_ON` setting. 
2. `<plugin>_REPORT_ON` let's you specify on which events the app should notify you. This is related to the `<plugin>_WATCH` setting. So if you select `watched-changed` and in `<plugin>_WATCH` you only select `Watched_Value1`, then a notification is triggered if `Watched_Value1` is changed from the previous value, but no notification is send if `Watched_Value2` changes. 

## Global settings ⚙

![Global notification settings](/docs/img/NOTIFICATIONS/Global-notification-settings.png)

In the Notification Processing section, you can specify blanket rules. These allso to specify exceptions to the Plugin and Device settings and will override those.

1. Notify on (`NTFPRCS_INCLUDED_SECTIONS`) allows you to specify which events trigegr notifications. Usual setups will have `new_devices`, `down_devices`, and possibly `events` set. Setting `plugin` might be too noisy for most setups.
2. Alert down after (`NTFPRCS_alert_down_time`) is useful if you want to wait for some time before the system sends out a down notification for a device. This is related to the on-device **Alert down** setting.
3. A filter to allow you to set device-specific exceptions to New devices being added to the app.
4. A filter to allow you to set device-specific exceptions to generated Events.

## Ignoring devices 🛑

![Ignoring new devices](/docs/img/NOTIFICATIONS/NEWDEV_ignores.png)

You can completely ignore detected devices globally. This could be becasue your instance detects docker containers, you want to ignore devices from a specific manufacturer via MAC rules or you want to ignore devices on a specific IP range. 

1. Ignored MACs (`NEWDEV_ignored_MACs`) - List of MACs to ignore.
2. Ignored IPs (`NEWDEV_ignored_MACs`) - List of IPs to ignore. 