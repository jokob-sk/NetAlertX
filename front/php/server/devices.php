<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  devices.php - Front module. Server side. Manage Devices
//------------------------------------------------------------------------------
//  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
//------------------------------------------------------------------------------

foreach (glob("../../../db/setting_language*") as $filename) {
    $pia_lang_selected = str_replace('setting_language_','',basename($filename));
}
if (strlen($pia_lang_selected) == 0) {$pia_lang_selected = 'en_us';}

//------------------------------------------------------------------------------
  // External files
  require 'db.php';
  require 'util.php';
  require '../templates/language/'.$pia_lang_selected.'.php';

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
  // Set maximum execution time to 15 seconds
  ini_set ('max_execution_time','30');
  
  // Open DB
  OpenDB();

  // Action functions
  if (isset ($_REQUEST['action']) && !empty ($_REQUEST['action'])) {
    $action = $_REQUEST['action'];
    switch ($action) {
      case 'getDeviceData':           getDeviceData();                         break;
      case 'setDeviceData':           setDeviceData();                         break;
      case 'deleteDevice':            deleteDevice();                          break;
      case 'deleteAllWithEmptyMACs':  deleteAllWithEmptyMACs();                break;
      case 'createBackupDB':          createBackupDB();                        break;
      case 'restoreBackupDB':         restoreBackupDB();                       break;
      case 'deleteAllDevices':        deleteAllDevices();                      break;
      case 'runScan15min':            runScan15min();                          break;
      case 'runScan1min':             runScan1min();                           break;
      case 'deleteUnknownDevices':    deleteUnknownDevices();                  break;
      case 'deleteEvents':            deleteEvents();                          break;
      case 'PiaBackupDBtoArchive':    PiaBackupDBtoArchive();                  break;
      case 'PiaRestoreDBfromArchive': PiaRestoreDBfromArchive();               break;
      case 'PiaEnableDarkmode':       PiaEnableDarkmode();                     break;
      case 'PiaToggleArpScan':        PiaToggleArpScan();                      break;

      case 'getDevicesTotals':        getDevicesTotals();                      break;
      case 'getDevicesList':          getDevicesList();                        break;
      case 'getDevicesListCalendar':  getDevicesListCalendar();                break;

      case 'getOwners':               getOwners();                             break;
      case 'getDeviceTypes':          getDeviceTypes();                        break;
      case 'getGroups':               getGroups();                             break;
      case 'getLocations':            getLocations();                          break;

      default:                        logServerConsole ('Action: '. $action);  break;
    }
  }


//------------------------------------------------------------------------------
//  Query Device Data
//------------------------------------------------------------------------------
function getDeviceData() {
  global $db;

  // Request Parameters
  $periodDate = getDateFromPeriod();
  $mac = $_REQUEST['mac'];

  // Device Data
  $sql = 'SELECT rowid, *,
            CASE WHEN dev_AlertDeviceDown=1 AND dev_PresentLastScan=0 THEN "Down"
                 WHEN dev_PresentLastScan=1 THEN "On-line"
                 ELSE "Off-line" END as dev_Status
          FROM Devices
          WHERE dev_MAC="'. $mac .'" or cast(rowid as text)="'. $mac. '"';
  $result = $db->query($sql);
  $row = $result -> fetchArray (SQLITE3_ASSOC);
  $deviceData = $row;
  $mac = $deviceData['dev_MAC'];

  $deviceData['dev_FirstConnection'] = formatDate ($row['dev_FirstConnection']); // Date formated
  $deviceData['dev_LastConnection'] =  formatDate ($row['dev_LastConnection']);  // Date formated

  $deviceData['dev_RandomMAC'] = ( in_array($mac[1], array("2","6","A","E","a","e")) ? 1 : 0);

  // Count Totals
  $condition = ' WHERE eve_MAC="'. $mac .'" AND eve_DateTime >= '. $periodDate;

  // Connections
  $sql = 'SELECT COUNT(*) FROM Sessions
          WHERE ses_MAC="'. $mac .'"
          AND (   ses_DateTimeConnection    >= '. $periodDate .'
               OR ses_DateTimeDisconnection >= '. $periodDate .'
               OR ses_StillConnected = 1 )';
  $result = $db->query($sql);
  $row = $result -> fetchArray (SQLITE3_NUM);
  $deviceData['dev_Sessions'] = $row[0];
  
  // Events
  $sql = 'SELECT COUNT(*) FROM Events '. $condition .' AND eve_EventType <> "Connected" AND eve_EventType <> "Disconnected" ';
  $result = $db->query($sql);
  $row = $result -> fetchArray (SQLITE3_NUM);
  $deviceData['dev_Events'] = $row[0];

  // Down Alerts
  $sql = 'SELECT COUNT(*) FROM Events '. $condition .' AND eve_EventType = "Device Down"';
  $result = $db->query($sql);
  $row = $result -> fetchArray (SQLITE3_NUM);
  $deviceData['dev_DownAlerts'] = $row[0];

  // Presence hours
  $sql = 'SELECT CAST(( MAX (0, SUM (julianday (IFNULL (ses_DateTimeDisconnection, DATETIME("now","localtime")))
                                     - julianday (CASE WHEN ses_DateTimeConnection < '. $periodDate .' THEN '. $periodDate .'
                                                       ELSE ses_DateTimeConnection END)) *24 )) AS INT)
          FROM Sessions
          WHERE ses_MAC="'. $mac .'"
            AND ses_DateTimeConnection IS NOT NULL
            AND (ses_DateTimeDisconnection IS NOT NULL OR ses_StillConnected = 1 )
            AND (   ses_DateTimeConnection    >= '. $periodDate .'
                 OR ses_DateTimeDisconnection >= '. $periodDate .'
                 OR ses_StillConnected = 1 )';
  $result = $db->query($sql);
  $row = $result -> fetchArray (SQLITE3_NUM);
  $deviceData['dev_PresenceHours'] = round ($row[0]);

  // Return json
  echo (json_encode ($deviceData));
}


//------------------------------------------------------------------------------
//  Update Device Data
//------------------------------------------------------------------------------
function setDeviceData() {
  global $db;
  global $pia_lang;

  // sql
  $sql = 'UPDATE Devices SET
                 dev_Name            = "'. quotes($_REQUEST['name'])         .'",
                 dev_Owner           = "'. quotes($_REQUEST['owner'])        .'",
                 dev_DeviceType      = "'. quotes($_REQUEST['type'])         .'",
                 dev_Vendor          = "'. quotes($_REQUEST['vendor'])       .'",
                 dev_Favorite        = "'. quotes($_REQUEST['favorite'])     .'",
                 dev_Group           = "'. quotes($_REQUEST['group'])        .'",
                 dev_Location        = "'. quotes($_REQUEST['location'])     .'",
                 dev_Comments        = "'. quotes($_REQUEST['comments'])     .'",
                 dev_StaticIP        = "'. quotes($_REQUEST['staticIP'])     .'",
                 dev_ScanCycle       = "'. quotes($_REQUEST['scancycle'])    .'",
                 dev_AlertEvents     = "'. quotes($_REQUEST['alertevents'])  .'",
                 dev_AlertDeviceDown = "'. quotes($_REQUEST['alertdown'])    .'",
                 dev_SkipRepeated    = "'. quotes($_REQUEST['skiprepeated']) .'",
                 dev_NewDevice       = "'. quotes($_REQUEST['newdevice'])    .'",
                 dev_Archived        = "'. quotes($_REQUEST['archived'])     .'"
          WHERE dev_MAC="' . $_REQUEST['mac'] .'"';
  // update Data
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo $pia_lang['BackDevices_DBTools_UpdDev'];
  } else {
    echo $pia_lang['BackDevices_DBTools_UpdDevError']."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}


//------------------------------------------------------------------------------
//  Delete Device
//------------------------------------------------------------------------------
function deleteDevice() {
  global $db;
  global $pia_lang;

  // sql
  $sql = 'DELETE FROM Devices WHERE dev_MAC="' . $_REQUEST['mac'] .'"';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo $pia_lang['BackDevices_DBTools_DelDev_a'];
  } else {
    echo $pia_lang['BackDevices_DBTools_DelDevError_a']."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete all devices with empty MAC addresses
//------------------------------------------------------------------------------
function deleteAllWithEmptyMACs() {
  global $db;
  global $pia_lang;

  // sql
  $sql = 'DELETE FROM Devices WHERE dev_MAC=""';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo $pia_lang['BackDevices_DBTools_DelDev_b'];
  } else {
    echo $pia_lang['BackDevices_DBTools_DelDevError_b']."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete all devices with empty MAC addresses
//------------------------------------------------------------------------------
function deleteUnknownDevices() {
  global $db;
  global $pia_lang;

  // sql
  $sql = 'DELETE FROM Devices WHERE dev_Name="(unknown)"';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo $pia_lang['BackDevices_DBTools_DelDev_b'];
  } else {
    echo $pia_lang['BackDevices_DBTools_DelDevError_b']."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}



//------------------------------------------------------------------------------
//  Delete all devices 
//------------------------------------------------------------------------------
function deleteAllDevices() {
  global $db;
  global $pia_lang;

  // sql
  $sql = 'DELETE FROM Devices';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo $pia_lang['BackDevices_DBTools_DelDev_b'];
  } else {
    echo $pia_lang['BackDevices_DBTools_DelDevError_b']."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete all Events 
//------------------------------------------------------------------------------
function deleteEvents() {
  global $db;
  global $pia_lang;

  // sql
  $sql = 'DELETE FROM Events';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo $pia_lang['BackDevices_DBTools_DelEvents'];
  } else {
    echo $pia_lang['BackDevices_DBTools_DelEventsError']."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Backup DB to Archiv
//------------------------------------------------------------------------------
function PiaBackupDBtoArchive() {
  // prepare fast Backup
  $file = '../../../db/pialert.db';
  $newfile = '../../../db/pialert.db.latestbackup';
  global $pia_lang;

  // copy files as a fast Backup
  if (!copy($file, $newfile)) {
      echo $pia_lang['BackDevices_Backup_CopError'];
  } else {
    // Create archive with actual date
    $Pia_Archive_Name = 'pialertdb_'.date("Ymd_His").'.zip';
    $Pia_Archive_Path = '../../../db/';
    exec('zip -j '.$Pia_Archive_Path.$Pia_Archive_Name.' ../../../db/pialert.db', $output);
    // chheck if archive exists
    if (file_exists($Pia_Archive_Path.$Pia_Archive_Name) && filesize($Pia_Archive_Path.$Pia_Archive_Name) > 0) {
      echo $pia_lang['BackDevices_Backup_okay'].': ('.$Pia_Archive_Name.')';
      unlink($newfile);
      echo("<meta http-equiv='refresh' content='1'>");
    } else {
      echo $pia_lang['BackDevices_Backup_Failed'].' (pialert.db.latestbackup)';
    }
  }

}

//------------------------------------------------------------------------------
//  Restore DB from Archiv
//------------------------------------------------------------------------------
function PiaRestoreDBfromArchive() {
  // prepare fast Backup
  $file = '../../../db/pialert.db';
  $oldfile = '../../../db/pialert.db.prerestore';
  global $pia_lang;

  // copy files as a fast Backup
  if (!copy($file, $oldfile)) {
      echo $pia_lang['BackDevices_Restore_CopError'];
  } else {
    // extract latest archive and overwrite the actual pialert.db
    $Pia_Archive_Path = '../../../db/';
    exec('/bin/ls -Art '.$Pia_Archive_Path.'*.zip | /bin/tail -n 1 | /usr/bin/xargs -n1 /bin/unzip -o -d ../../../db/', $output);
    // check if the pialert.db exists
    if (file_exists($file)) {
       echo $pia_lang['BackDevices_Restore_okay'];
       unlink($oldfile);
       echo("<meta http-equiv='refresh' content='1'>");
     } else {
       echo $pia_lang['BackDevices_Restore_Failed'];
     }
  }

}

//------------------------------------------------------------------------------
//  Toggle Dark/Light Themes
//------------------------------------------------------------------------------
function PiaEnableDarkmode() {
  $file = '../../../db/setting_darkmode';
  global $pia_lang;

  if (file_exists($file)) {
      echo $pia_lang['BackDevices_darkmode_disabled'];
      unlink($file);
      echo("<meta http-equiv='refresh' content='1'>");
     } else {
      echo $pia_lang['BackDevices_darkmode_enabled'];
      $darkmode = fopen($file, 'w');
      echo("<meta http-equiv='refresh' content='1'>");
     }
  }


//------------------------------------------------------------------------------
//  Toggle on/off Arp-Scans
//------------------------------------------------------------------------------
function PiaToggleArpScan() {
  $file = '../../../db/setting_stoparpscan';
  global $pia_lang;

  if (file_exists($file)) {
      echo $pia_lang['BackDevices_Arpscan_enabled'];
      unlink($file);
      echo("<meta http-equiv='refresh' content='1'>");
     } else {
      echo $pia_lang['BackDevices_Arpscan_disabled'];
      $startarpscan = fopen($file, 'w');
      echo("<meta http-equiv='refresh' content='1'>");
     }
  }

//------------------------------------------------------------------------------
//  Query total numbers of Devices by status
//------------------------------------------------------------------------------
function getDevicesTotals() {
  global $db;

  // All
  $result = $db->query('SELECT COUNT(*) FROM Devices '. getDeviceCondition ('all'));
  $row = $result -> fetchArray (SQLITE3_NUM);
  $devices = $row[0];
  
  // On-Line
  $result = $db->query('SELECT COUNT(*) FROM Devices '. getDeviceCondition ('connected') );
  $row = $result -> fetchArray (SQLITE3_NUM);
  $connected = $row[0];
  
  // Favorites
  $result = $db->query('SELECT COUNT(*) FROM Devices '. getDeviceCondition ('favorites') );
  $row = $result -> fetchArray (SQLITE3_NUM);
  $favorites = $row[0];
  
  // New
  $result = $db->query('SELECT COUNT(*) FROM Devices '. getDeviceCondition ('new') );
  $row = $result -> fetchArray (SQLITE3_NUM);
  $newDevices = $row[0];
  
  // Down Alerts
  $result = $db->query('SELECT COUNT(*) FROM Devices '. getDeviceCondition ('down'));
  $row = $result -> fetchArray (SQLITE3_NUM);
  $downAlert = $row[0];

  // Archived
  $result = $db->query('SELECT COUNT(*) FROM Devices '. getDeviceCondition ('archived'));
  $row = $result -> fetchArray (SQLITE3_NUM);
  $archived = $row[0];

  echo (json_encode (array ($devices, $connected, $favorites, $newDevices, $downAlert, $archived)));
}


//------------------------------------------------------------------------------
//  Query the List of devices in a determined Status
//------------------------------------------------------------------------------
function getDevicesList() {
  global $db;

  // SQL
  $condition = getDeviceCondition ($_REQUEST['status']);

  $sql = 'SELECT rowid, *, CASE
            WHEN dev_AlertDeviceDown=1 AND dev_PresentLastScan=0 THEN "Down"
            WHEN dev_NewDevice=1 THEN "New"
            WHEN dev_PresentLastScan=1 THEN "On-line"
            ELSE "Off-line"
          END AS dev_Status
          FROM Devices '. $condition;
  $result = $db->query($sql);

  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    $tableData['data'][] = array ($row['dev_Name'],
                                  $row['dev_Owner'],
                                  $row['dev_DeviceType'],
                                  $row['dev_Favorite'],
                                  $row['dev_Group'],
                                  formatDate ($row['dev_FirstConnection']),
                                  formatDate ($row['dev_LastConnection']),
                                  $row['dev_LastIP'],
                                  ( in_array($row['dev_MAC'][1], array("2","6","A","E","a","e")) ? 1 : 0),
                                  $row['dev_Status'],
                                  $row['dev_MAC'], // MAC (hidden)
                                  formatIPlong ($row['dev_LastIP']), // IP orderable
                                  $row['rowid'] // Rowid (hidden)
                                 );
  }

  // Control no rows
  if (empty($tableData['data'])) {
    $tableData['data'] = '';
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query the List of devices for calendar
//------------------------------------------------------------------------------
function getDevicesListCalendar() {
  global $db;

  // SQL
  $condition = getDeviceCondition ($_REQUEST['status']);
  $result = $db->query('SELECT * FROM Devices ' . $condition);

  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    if ($row['dev_Favorite'] == 1) {
      $row['dev_Name'] = '<span class="text-yellow">&#9733</span>&nbsp'. $row['dev_Name'];
    }

    $tableData[] = array ('id'       => $row['dev_MAC'],
                          'title'    => $row['dev_Name'],
                          'favorite' => $row['dev_Favorite']);
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query the List of Owners
//------------------------------------------------------------------------------
function getOwners() {
  global $db;

  // SQL
  $sql = 'SELECT DISTINCT 1 as dev_Order, dev_Owner
          FROM Devices
          WHERE dev_Owner <> "(unknown)" AND dev_Owner <> ""
            AND dev_Favorite = 1
        UNION
          SELECT DISTINCT 2 as dev_Order, dev_Owner
          FROM Devices
          WHERE dev_Owner <> "(unknown)" AND dev_Owner <> ""
            AND dev_Favorite = 0
            AND dev_Owner NOT IN
               (SELECT dev_Owner FROM Devices WHERE dev_Favorite = 1)
        ORDER BY 1,2 ';
  $result = $db->query($sql);

  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    $tableData[] = array ('order' => $row['dev_Order'],
                          'name'  => $row['dev_Owner']);
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query the List of types
//------------------------------------------------------------------------------
function getDeviceTypes() {
  global $db;

  // SQL
  $sql = 'SELECT DISTINCT 9 as dev_Order, dev_DeviceType
          FROM Devices
          WHERE dev_DeviceType NOT IN ("",
                 "Smartphone", "Tablet",
                 "Laptop", "Mini PC", "PC", "Printer", "Server", "Singleboard Computer (SBC)",
                 "Game Console", "SmartTV", "TV Decoder", "Virtual Assistance",
                 "Clock", "House Appliance", "Phone", "Radio",
                 "AP", "NAS", "PLC", "Router")

          UNION SELECT 1 as dev_Order, "Smartphone"
          UNION SELECT 1 as dev_Order, "Tablet"

          UNION SELECT 2 as dev_Order, "Laptop"
          UNION SELECT 2 as dev_Order, "Mini PC"
          UNION SELECT 2 as dev_Order, "PC"
          UNION SELECT 2 as dev_Order, "Printer"
          UNION SELECT 2 as dev_Order, "Server"
          UNION SELECT 2 as dev_Order, "Singleboard Computer (SBC)"

          UNION SELECT 3 as dev_Order, "Domotic"
          UNION SELECT 3 as dev_Order, "Game Console"
          UNION SELECT 3 as dev_Order, "SmartTV"
          UNION SELECT 3 as dev_Order, "TV Decoder"
          UNION SELECT 3 as dev_Order, "Virtual Assistance"

          UNION SELECT 4 as dev_Order, "Clock"
          UNION SELECT 4 as dev_Order, "House Appliance"
          UNION SELECT 4 as dev_Order, "Phone"
          UNION SELECT 4 as dev_Order, "Radio"

          UNION SELECT 5 as dev_Order, "AP"
          UNION SELECT 5 as dev_Order, "NAS"
          UNION SELECT 5 as dev_Order, "PLC"
          UNION SELECT 5 as dev_Order, "Router"
          UNION SELECT 5 as dev_Order, "USB LAN Adapter"
          UNION SELECT 5 as dev_Order, "USB WIFI Adapter"

          UNION SELECT 10 as dev_Order, "Other"

          ORDER BY 1,2';
  $result = $db->query($sql);

  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    $tableData[] = array ('order' => $row['dev_Order'],
                          'name'  => $row['dev_DeviceType']);
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query the List of groups
//------------------------------------------------------------------------------
function getGroups() {
  global $db;

  // SQL
  $sql = 'SELECT DISTINCT 1 as dev_Order, dev_Group
          FROM Devices
          WHERE dev_Group NOT IN ("(unknown)", "Others") AND dev_Group <> ""
          UNION SELECT 1 as dev_Order, "Always on"
          UNION SELECT 1 as dev_Order, "Friends"
          UNION SELECT 1 as dev_Order, "Personal"
          UNION SELECT 2 as dev_Order, "Others"
          ORDER BY 1,2 ';
  $result = $db->query($sql);

  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    $tableData[] = array ('order' => $row['dev_Order'],
                          'name'  => $row['dev_Group']);
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query the List of locations
//------------------------------------------------------------------------------
function getLocations() {
  global $db;

  // SQL
  $sql = 'SELECT DISTINCT 9 as dev_Order, dev_Location
          FROM Devices
          WHERE dev_Location <> ""
            AND dev_Location NOT IN (
                "Bathroom", "Bedroom", "Dining room", "Hallway",
                "Kitchen", "Laundry", "Living room", "Study", 
                "Attic", "Basement", "Garage", 
                "Back yard", "Garden", "Terrace",
                "Other")

          UNION SELECT 1 as dev_Order, "Bathroom"
          UNION SELECT 1 as dev_Order, "Bedroom"
          UNION SELECT 1 as dev_Order, "Dining room"
          UNION SELECT 1 as dev_Order, "Hall"  
          UNION SELECT 1 as dev_Order, "Kitchen"
          UNION SELECT 1 as dev_Order, "Laundry"
          UNION SELECT 1 as dev_Order, "Living room"
          UNION SELECT 1 as dev_Order, "Study" 

          UNION SELECT 2 as dev_Order, "Attic"
          UNION SELECT 2 as dev_Order, "Basement" 
          UNION SELECT 2 as dev_Order, "Garage" 

          UNION SELECT 3 as dev_Order, "Back yard"
          UNION SELECT 3 as dev_Order, "Garden" 
          UNION SELECT 3 as dev_Order, "Terrace"

          UNION SELECT 10 as dev_Order, "Other"
          ORDER BY 1,2 ';


 
  $result = $db->query($sql);

  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    $tableData[] = array ('order' => $row['dev_Order'],
                          'name'  => $row['dev_Location']);
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Status Where conditions
//------------------------------------------------------------------------------
function getDeviceCondition ($deviceStatus) {
  switch ($deviceStatus) {
    case 'all':        return 'WHERE dev_Archived=0';                                                      break;
    case 'connected':  return 'WHERE dev_Archived=0 AND dev_PresentLastScan=1';                            break;
    case 'favorites':  return 'WHERE dev_Archived=0 AND dev_Favorite=1';                                   break;
    case 'new':        return 'WHERE dev_Archived=0 AND dev_NewDevice=1';                                  break;
    case 'down':       return 'WHERE dev_Archived=0 AND dev_AlertDeviceDown=1 AND dev_PresentLastScan=0';  break;
    case 'archived':   return 'WHERE dev_Archived=1';                                                      break;
    default:           return 'WHERE 1=0';                                                                 break;
  }
}

?>
