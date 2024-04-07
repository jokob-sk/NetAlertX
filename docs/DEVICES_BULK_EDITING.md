# 🖊 Multi-editing via the UI

> [!NOTE] 
> Make sure you have your backups saved and restorable before doing any mass edits. Check [Backup strategies](/docs/BACKUPS.md). 

You can select devices in the _Devices_ view by selecting devices to edit and then clicking the _Multi-edit_ button or via the _Maintenance_ > _Multi-Edit_ section.

![Maintenance > Multi-edit](/docs/img/DEVICES_BULK_EDITING/MULTI-EDIT.gif)


# 📝Bulk-edit devices via CSV Export/Import

> [!NOTE] 
> As always, backup everything, just in case.

1. In _Maintenance_ > _Backup / Restore_ click the _CSV Export_ button.  
2. A `devices.csv` is generated in the `/config` folder
3. Edit the `devices.csv` file however you like. 

![Maintenance > CSV Export](/docs/img/DEVICES_BULK_EDITING/MAINTENANCE_CSV_EXPORT.png)

> [!NOTE] 
> The file containing a list of Devices including the Network relationships between Network Nodes and connected devices. You can also trigger this by acessing this URL: `<your netalertx url>/php/server/devices.php?action=ExportCSV` or via the `CSV Backup` plugin. (💡 You can schedule this)

![Settings > CSV Backup](/docs/img/DEVICES_BULK_EDITING/CSV_BACKUP_SETTINGS.png)

> [!NOTE] 
> Keep Linux line endings (suggested editors: Nano, Notepad++)

![Nodepad++ line endings](/docs/img/DEVICES_BULK_EDITING/NOTEPAD++.png)




