<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  devices.php - Front module. Server side. Manage Devices
//------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------

  // External files
  require dirname(__FILE__).'/init.php';

  //------------------------------------------------------------------------------
  //  Action selector
  //------------------------------------------------------------------------------
  // Set maximum execution time to 15 seconds

  ini_set ('max_execution_time','30');

  // Action functions
  if (isset ($_REQUEST['action']) && !empty ($_REQUEST['action'])) {
    $action = $_REQUEST['action'];
    switch ($action) {
      case 'getDeviceData':           getDeviceData();                         break;
      case 'setDeviceData':           setDeviceData();                         break;
      case 'getNetworkNodes':         getNetworkNodes();                       break;
      case 'deleteDevice':            deleteDevice();                          break;
      case 'deleteAllWithEmptyMACs':  deleteAllWithEmptyMACs();                break;      
      case 'createBackupDB':          createBackupDB();                        break;
      
      case 'deleteAllDevices':        deleteAllDevices();                      break;
      case 'runScan15min':            runScan15min();                          break;
      case 'runScan1min':             runScan1min();                           break;
      case 'deleteUnknownDevices':    deleteUnknownDevices();                  break;
      case 'deleteEvents':            deleteEvents();                          break;
      case 'deleteEvents30':          deleteEvents30();                        break;
      case 'deleteActHistory':        deleteActHistory();                      break;
      case 'deleteDeviceEvents':      deleteDeviceEvents();                    break;
      case 'PiaBackupDBtoArchive':    PiaBackupDBtoArchive();                  break;
      case 'PiaRestoreDBfromArchive': PiaRestoreDBfromArchive();               break;
      case 'PiaPurgeDBBackups':       PiaPurgeDBBackups();                     break;             
      case 'ExportCSV':               ExportCSV();                             break;    
      case 'ImportCSV':               ImportCSV();                             break;     

      case 'getDevicesTotals':        getDevicesTotals();                      break;
      case 'getDevicesList':          getDevicesList();                        break;
      case 'getDevicesListCalendar':  getDevicesListCalendar();                break;

      case 'getOwners':               getOwners();                             break;
      case 'getDeviceTypes':          getDeviceTypes();                        break;
      case 'getGroups':               getGroups();                             break;
      case 'getLocations':            getLocations();                          break;
      case 'getPholus':               getPholus();                             break;
      case 'getNmap':                 getNmap();                               break;
      case 'saveNmapPort':            saveNmapPort();                          break;
      case 'updateNetworkLeaf':       updateNetworkLeaf();                     break;
      case 'overwriteIconType':       overwriteIconType();                     break;
      case 'getIcons':                getIcons();                              break;

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

  $deviceData['dev_Network_Node_MAC_ADDR'] = $row['dev_Network_Node_MAC_ADDR'];
  $deviceData['dev_Network_Node_port'] = $row['dev_Network_Node_port'];
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

  // Get current date using php, sql datetime does not return time respective to timezone.
  $currentdate = date("Y-m-d H:i:s");
  // Presence hours
  $sql = 'SELECT CAST(( MAX (0, SUM (julianday (IFNULL (ses_DateTimeDisconnection,"'. $currentdate .'" ))
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

  // sql
  $sql = 'UPDATE Devices SET
                 dev_Name                   = "'. quotes($_REQUEST['name'])         .'",
                 dev_Owner                  = "'. quotes($_REQUEST['owner'])        .'",
                 dev_DeviceType             = "'. quotes($_REQUEST['type'])         .'",
                 dev_Vendor                 = "'. quotes($_REQUEST['vendor'])       .'",
                 dev_Icon                   = "'. quotes($_REQUEST['icon'])         .'",
                 dev_Favorite               = "'. quotes($_REQUEST['favorite'])     .'",
                 dev_Group                  = "'. quotes($_REQUEST['group'])        .'",
                 dev_Location               = "'. quotes($_REQUEST['location'])     .'",
                 dev_Comments               = "'. quotes($_REQUEST['comments'])     .'",
                 dev_Network_Node_MAC_ADDR  = "'. quotes($_REQUEST['networknode']).'",
                 dev_Network_Node_port      = "'. quotes($_REQUEST['networknodeport']).'",
                 dev_StaticIP               = "'. quotes($_REQUEST['staticIP'])     .'",
                 dev_ScanCycle              = "'. quotes($_REQUEST['scancycle'])    .'",
                 dev_AlertEvents            = "'. quotes($_REQUEST['alertevents'])  .'",
                 dev_AlertDeviceDown        = "'. quotes($_REQUEST['alertdown'])    .'",
                 dev_SkipRepeated           = "'. quotes($_REQUEST['skiprepeated']) .'",
                 dev_NewDevice              = "'. quotes($_REQUEST['newdevice'])    .'",
                 dev_Archived               = "'. quotes($_REQUEST['archived'])     .'"
          WHERE dev_MAC="' . $_REQUEST['mac'] .'"';
  // update Data
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_UpdDev');
  } else {
    echo lang('BackDevices_DBTools_UpdDevError')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}


//------------------------------------------------------------------------------
//  Delete Device
//------------------------------------------------------------------------------
function deleteDevice() {
  global $db;

  // sql
  $sql = 'DELETE FROM Devices WHERE dev_MAC="' . $_REQUEST['mac'] .'"';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_DelDev_a');
  } else {
    echo lang('BackDevices_DBTools_DelDevError_a')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete all devices with empty MAC addresses
//------------------------------------------------------------------------------
function deleteAllWithEmptyMACs() {
  global $db;  

  // sql
  $sql = 'DELETE FROM Devices WHERE dev_MAC=""';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_DelDev_b');
  } else {
    echo lang('BackDevices_DBTools_DelDevError_b')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete all devices with empty MAC addresses
//------------------------------------------------------------------------------
function deleteUnknownDevices() {
  global $db;  

  // sql
  $sql = 'DELETE FROM Devices WHERE dev_Name="(unknown)"';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_DelDev_b');
  } else {
    echo lang('BackDevices_DBTools_DelDevError_b')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete Device Events
//------------------------------------------------------------------------------
function deleteDeviceEvents() {
  global $db;

  // sql
  $sql = 'DELETE FROM Events WHERE eve_MAC="' . $_REQUEST['mac'] .'"';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_DelEvents');
  } else {
    echo lang('BackDevices_DBTools_DelEventsError')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete all devices 
//------------------------------------------------------------------------------
function deleteAllDevices() {
  global $db;

  // sql
  $sql = 'DELETE FROM Devices';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_DelDev_b');
  } else {
    echo lang('BackDevices_DBTools_DelDevError_b')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete all Events 
//------------------------------------------------------------------------------
function deleteEvents() {
  global $db;
  // sql
  $sql = 'DELETE FROM Events';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_DelEvents');
  } else {
    echo lang('BackDevices_DBTools_DelEventsError')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete all Events older than 30 days
//------------------------------------------------------------------------------
function deleteEvents30() {
  global $db;

  // sql
  $sql = "DELETE FROM Events WHERE eve_DateTime <= date('now', '-30 day')";
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_DelEvents');
  } else {
    echo lang('BackDevices_DBTools_DelEventsError')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Delete History
//------------------------------------------------------------------------------
function deleteActHistory() {
  global $db;

  // sql
  $sql = 'DELETE FROM Online_History';
  // execute sql
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo lang('BackDevices_DBTools_DelActHistory');
  } else {
    echo lang('BackDevices_DBTools_DelActHistoryError')."\n\n$sql \n\n". $db->lastErrorMsg();
  }
}

//------------------------------------------------------------------------------
//  Backup DB to Archiv
//------------------------------------------------------------------------------
function PiaBackupDBtoArchive() {
  // prepare fast Backup
  $file = '../../../db/pialert.db';
  $newfile = '../../../db/pialert.db.latestbackup';
  
  // copy files as a fast Backup
  if (!copy($file, $newfile)) {
      echo lang('BackDevices_Backup_CopError');
  } else {
    // Create archive with actual date
    $Pia_Archive_Name = 'pialertdb_'.date("Ymd_His").'.zip';
    $Pia_Archive_Path = '../../../db/';
    exec('zip -j '.$Pia_Archive_Path.$Pia_Archive_Name.' ../../../db/pialert.db', $output);
    // chheck if archive exists
    if (file_exists($Pia_Archive_Path.$Pia_Archive_Name) && filesize($Pia_Archive_Path.$Pia_Archive_Name) > 0) {
      echo lang('BackDevices_Backup_okay').': ('.$Pia_Archive_Name.')';
      unlink($newfile);
      echo("<meta http-equiv='refresh' content='1'>");
    } else {
      echo lang('BackDevices_Backup_Failed').' (pialert.db.latestbackup)';
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

  // copy files as a fast Backup
  if (!copy($file, $oldfile)) {
      echo lang('BackDevices_Restore_CopError');
  } else {
    // extract latest archive and overwrite the actual pialert.db
    $Pia_Archive_Path = '../../../db/';
    exec('/bin/ls -Art '.$Pia_Archive_Path.'*.zip | /bin/tail -n 1 | /usr/bin/xargs -n1 /bin/unzip -o -d ../../../db/', $output);
    // check if the pialert.db exists
    if (file_exists($file)) {
       echo lang('BackDevices_Restore_okay');
       unlink($oldfile);
       echo("<meta http-equiv='refresh' content='1'>");
     } else {
       echo lang('BackDevices_Restore_Failed');
     }
  }

}

//------------------------------------------------------------------------------
//  Purge Backups
//------------------------------------------------------------------------------
function PiaPurgeDBBackups() {  

  $Pia_Archive_Path = '../../../db';
  $Pia_Backupfiles = array();
  $files = array_diff(scandir($Pia_Archive_Path, SCANDIR_SORT_DESCENDING), array('.', '..', 'pialert.db', 'pialertdb-reset.zip'));

  foreach ($files as &$item) 
    {
      $item = $Pia_Archive_Path.'/'.$item;
      if (stristr($item, 'setting_') == '') {array_push($Pia_Backupfiles, $item);}
    }

  if (sizeof($Pia_Backupfiles) > 3) 
    {
      rsort($Pia_Backupfiles);
      unset($Pia_Backupfiles[0], $Pia_Backupfiles[1], $Pia_Backupfiles[2]);
      $Pia_Backupfiles_Purge = array_values($Pia_Backupfiles);
      for ($i = 0; $i < sizeof($Pia_Backupfiles_Purge); $i++) 
        {
          unlink($Pia_Backupfiles_Purge[$i]);
        }
  }
  echo lang('BackDevices_DBTools_Purge');
  echo("<meta http-equiv='refresh' content='1'>");
    
}

//------------------------------------------------------------------------------
//  Export CSV of devices
//------------------------------------------------------------------------------
function ExportCSV() {

  header("Content-Type: application/octet-stream");
  header("Content-Transfer-Encoding: Binary");
  header("Content-disposition: attachment; filename=\"devices.csv\"");

  global $db;
  $func_result = $db->query("SELECT * FROM Devices");        

  // prepare CSV header row
  // header array with column names 
  $columns = getDevicesColumns();

  // wrap the headers with " (quotes) 
  $resultCSV = '"'.implode('","', $columns).'"';  

  //and append a new line
  $resultCSV = $resultCSV."\n";

  // retrieve the devices from the DB
  while ($row = $func_result -> fetchArray (SQLITE3_ASSOC)) {   

    // loop through columns and add values to the string 
    $index = 0;
    foreach ($columns as $columnName) {

      // add quotes around the value to prevent issues with commas in fields
      $resultCSV = $resultCSV.'"'.$row[$columnName].'"';

      // detect last loop - skip as no comma needed
      if ($index != count($columns) - 1  )
      {
        $resultCSV = $resultCSV.',';
      }
      $index++;
    } 

    //$resultCSV = $resultCSV.implode(",", [$row["dev_MAC"], $row["dev_Name"]]);
    $resultCSV = $resultCSV."\n";
  }

  //write the built CSV string
  echo $resultCSV;    
}

//------------------------------------------------------------------------------
//  Import CSV of devices
//------------------------------------------------------------------------------
function ImportCSV() {


  $file = '../../../config/devices.csv';

  if (file_exists($file)) {

    global $db;    

    $error = "";

    // sql
    $sql = 'DELETE FROM Devices';

    // execute sql
    $result = $db->query($sql);    

    $data = file_get_contents($file); 
    $data = explode("\n", $data); 

    $columns = getDevicesColumns();

    
    // Parse data from CSV file line by line (max 10000 lines)    
    foreach($data as $row)
    {
      // Check if not empty and skipping first line      
      $rowArray = explode(',',$row);

      if(count($rowArray) > 20)
      {
        $cleanMac = str_replace("\"","",$rowArray[0]);
        
        if(filter_var($cleanMac , FILTER_VALIDATE_MAC) == True || $cleanMac == "Internet")
        {
          $sql = "INSERT INTO Devices (".implode(',', $columns).") VALUES (" . $row.")";         
          $result = $db->query($sql);
          
          // check result
          if ($result != TRUE) {
            $error = $db->lastErrorMsg();
            // break the while loop on error
            break;
          } 
        }
      }
      
    }
   
    if($error == "")
    {
      // import succesful
      echo lang('BackDevices_DBTools_ImportCSV');

    }
    else{
      // an error occurred while writing to the DB, display the last error message 
      echo lang('BackDevices_DBTools_ImportCSVError')."\n\n$sql \n\n".$result;
    }
    
   } else {
    echo lang('BackDevices_DBTools_ImportCSVMissing');    
   }

}

//------------------------------------------------------------------------------
//  Query total numbers of Devices by status
//------------------------------------------------------------------------------
function getDevicesTotals() {

  $resultJSON = "";

  if(getCache("getDevicesTotals") != "")
  {
    $resultJSON = getCache("getDevicesTotals");
  } else
  {
    global $db;

    // combined query
    $result = $db->query(
          'SELECT 
          (SELECT COUNT(*) FROM Devices '. getDeviceCondition ('all').') as devices, 
          (SELECT COUNT(*) FROM Devices '. getDeviceCondition ('connected').') as connected, 
          (SELECT COUNT(*) FROM Devices '. getDeviceCondition ('favorites').') as favorites, 
          (SELECT COUNT(*) FROM Devices '. getDeviceCondition ('new').') as new, 
          (SELECT COUNT(*) FROM Devices '. getDeviceCondition ('down').') as down, 
          (SELECT COUNT(*) FROM Devices '. getDeviceCondition ('archived').') as archived
    ');

    $row = $result -> fetchArray (SQLITE3_NUM); 
    $resultJSON = json_encode (array ($row[0], $row[1], $row[2], $row[3], $row[4], $row[5]));

    // save to cache
    setCache("getDevicesTotals", $resultJSON );
  }  

  echo ($resultJSON);
}


//------------------------------------------------------------------------------
//  Query the List of devices in a determined Status
//------------------------------------------------------------------------------
// function getDevicesListForNetworkTree() {
//   global $db;

//   $sql = 'SELECT *, CASE
//               WHEN t1.dev_AlertDeviceDown=1 AND t1.dev_PresentLastScan=0 THEN "Down"
//               WHEN t1.dev_NewDevice=1 THEN "New"
//               WHEN t1.dev_PresentLastScan=1 THEN "On-line"
//               ELSE "Off-line"  END AS dev_Status
//               FROM (Devices ) t1
//           LEFT JOIN
//                       (
//                             SELECT *,
//                                   count() as connected_devices 
//                             FROM Devices b 
//                             WHERE b.dev_Network_Node_MAC_ADDR NOT NULL group by b.dev_Network_Node_MAC_ADDR
//                       ) t2
//                       ON (t1.dev_MAC = t2.dev_MAC); ';

//   $result = $db->query($sql);

//   // arrays of rows
//   $tableData = array();
//   while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {

//   $defaultOrder = array ($row['dev_Name'],
//                     $row['dev_Owner'],
//                     handleNull($row['dev_DeviceType']),
//                     handleNull($row['dev_Icon'], "laptop"),
//                     $row['dev_Favorite'],
//                     $row['dev_Group'],
//                     formatDate ($row['dev_FirstConnection']),
//                     formatDate ($row['dev_LastConnection']),
//                     $row['dev_LastIP'],
//                     ( in_array($row['dev_MAC'][1], array("2","6","A","E","a","e")) ? 1 : 0),
//                     $row['dev_Status'],
//                     $row['dev_MAC'], // MAC (hidden)
//                     formatIPlong ($row['dev_LastIP']), // IP orderable
//                     $row['rowid'], // Rowid (hidden)      
//                     handleNull($row['dev_Network_Node_MAC_ADDR']), // 
//                     handleNull($row['connected_devices']) // 
//                     );

//   $newOrder = array();

//   // reorder columns based on user settings
//   for($index = 0; $index  < count($columnOrderMapping); $index++)
//   {
//   array_push($newOrder, $defaultOrder[$columnOrderMapping[$index][2]]);      
//   }

//   $tableData['data'][] = $newOrder;
//   }

//   // Control no rows
//   if (empty($tableData['data'])) {
//   $tableData['data'] = '';
//   }

//   // Return json
//   echo (json_encode ($tableData));

// }

//------------------------------------------------------------------------------
//  Query the List of devices in a determined Status
//------------------------------------------------------------------------------
function getDevicesList() {
  global $db;

  $forceDefaultOrder = FALSE;

  if (isset ($_REQUEST['forceDefaultOrder']) )
  {
    $forceDefaultOrder = TRUE;
  }

  // This object is used to map from the old order ( second parameter, first number) to the 3rd parameter (Second number (here initialized to -1))
  $columnOrderMapping = array(
    array("dev_Name", 0, 0),               
    array("dev_Owner", 1, 1),              
    array("dev_DeviceType", 2, 2),         
    array("dev_Icon", 3, 3),               
    array("dev_Favorite", 4, 4),           
    array("dev_Group", 5, 5),              
    array("dev_FirstConnection", 6, 6),    
    array("dev_LastConnection", 7, 7),     
    array("dev_LastIP", 8, 8),             
    array("dev_MAC", 9, 9),                
    array("dev_Status", 10, 10),            
    array("dev_MAC_full", 11, 11),          
    array("dev_LastIP_orderable", 12, 12),  
    array("rowid", 13, 13),            
    array("dev_Network_Node_MAC_ADDR", 14, 14),
    array("connected_devices", 15, 15),
    array("dev_Location", 16, 16),
    array("dev_Vendor", 17, 17)           
  );

  if($forceDefaultOrder == FALSE) 
  {
    // get device columns order
    $sql = 'SELECT par_Value FROM Parameters  where par_ID = "Front_Devices_Columns_Order"';
    $result = $db->query($sql);
    $row = $result -> fetchArray (SQLITE3_NUM);  

    if($row != NULL && count($row) == 1)
    {
      // ordered columns setting from the maintenance page
      $orderedColumns = createArray($row[0]);

      // init ordered columns    
      for($i = 0; $i < count($orderedColumns); $i++) {           
        $columnOrderMapping[$i][2] = $orderedColumns[$i];      
      }
    }
  }

  // SQL
  $condition = getDeviceCondition ($_REQUEST['status']);

  $sql = 'SELECT * FROM (
              SELECT rowid, *, CASE
                      WHEN t1.dev_AlertDeviceDown=1 AND t1.dev_PresentLastScan=0 THEN "Down"
                      WHEN t1.dev_NewDevice=1 THEN "New"
                      WHEN t1.dev_PresentLastScan=1 THEN "On-line"
                      ELSE "Off-line"  END AS dev_Status
                      FROM Devices t1 '.$condition.') t3  
                    LEFT JOIN
                              (
                                    SELECT dev_Network_Node_MAC_ADDR as dev_Network_Node_MAC_ADDR_t2, dev_MAC as dev_MAC_t2,
                                          count() as connected_devices 
                                    FROM Devices b 
                                    WHERE b.dev_Network_Node_MAC_ADDR NOT NULL group by b.dev_Network_Node_MAC_ADDR
                              ) t2
                              ON (t3.dev_MAC = t2.dev_Network_Node_MAC_ADDR_t2);';

  $result = $db->query($sql);
  
  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {

    $defaultOrder = array ($row['dev_Name'],
                            $row['dev_Owner'],
                            handleNull($row['dev_DeviceType']),
                            handleNull($row['dev_Icon'], "laptop"),
                            $row['dev_Favorite'],
                            $row['dev_Group'],
                            formatDate ($row['dev_FirstConnection']),
                            formatDate ($row['dev_LastConnection']),
                            $row['dev_LastIP'],
                            ( in_array($row['dev_MAC'][1], array("2","6","A","E","a","e")) ? 1 : 0),
                            $row['dev_Status'],
                            $row['dev_MAC'], // MAC (hidden)
                            formatIPlong ($row['dev_LastIP']), // IP orderable
                            $row['rowid'], // Rowid (hidden)      
                            handleNull($row['dev_Network_Node_MAC_ADDR']),
                            handleNull($row['connected_devices']),
                            handleNull($row['dev_Location']), 
                            handleNull($row['dev_Vendor'])                            
                          );

    $newOrder = array();

    // reorder columns based on user settings
    for($index = 0; $index  < count($columnOrderMapping); $index++)
    {
      array_push($newOrder, $defaultOrder[$columnOrderMapping[$index][2]]);      
    }

    $tableData['data'][] = $newOrder;
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
//  Query Device Data
//------------------------------------------------------------------------------
function getNetworkNodes() {
  global $db;

  // Device Data
  $sql = 'SELECT * FROM Devices WHERE dev_DeviceType in (  "AP", "Gateway", "Firewall", "Powerline", "Switch", "WLAN", "PLC", "Router","USB LAN Adapter", "USB WIFI Adapter")';

  $result = $db->query($sql);

  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {   
    // Push row data
    $tableData[] = array('id'    => $row['dev_MAC'], 
                         'name'  => $row['dev_Name'] );                        
  }
  
  // Control no rows
  if (empty($tableData)) {
    $tableData = [];
  }
  
    // Return json
  echo (json_encode ($tableData));
}

//------------------------------------------------------------------------------
function getIcons() {
  global $db;

  // Device Data
  $sql = 'select dev_Icon from Devices group by dev_Icon';

  $result = $db->query($sql);

  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {  
    $icon = handleNull($row['dev_Icon'], "laptop"); 
    // Push row data
    $tableData[] = array('id'    => $icon, 
                         'name'  => '<i class="fa fa-'.$icon.'"></i> - '.$icon );                          
  }
  
  // Control no rows
  if (empty($tableData)) {
    $tableData = [];
  }
  
    // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query the List of types
//------------------------------------------------------------------------------
function getDeviceTypes() {
  global $db;

  $networkTypes = getNetworkTypes();

  // SQL
  $sql = 'SELECT DISTINCT 9 as dev_Order, dev_DeviceType
          FROM Devices
          WHERE dev_DeviceType NOT IN ("",
                 "Smartphone", "Tablet",
                 "Laptop", "Mini PC", "PC", "Printer", "Server", "Singleboard Computer (SBC)", "NAS",
                 "Domotic", "IP Camera", "Game Console", "SmartTV", "TV Decoder", "Virtual Assistance",
                 "Clock", "House Appliance", "Phone", "Radio",
                 "AP", "Gateway", "Firewall", "Powerline", "Switch", "WLAN", "PLC", "Router","USB LAN Adapter", "USB WIFI Adapter" )

          UNION SELECT 1 as dev_Order, "Smartphone"
          UNION SELECT 1 as dev_Order, "Tablet"

          UNION SELECT 2 as dev_Order, "Laptop"
          UNION SELECT 2 as dev_Order, "Mini PC"
          UNION SELECT 2 as dev_Order, "PC"
          UNION SELECT 2 as dev_Order, "Printer"
          UNION SELECT 2 as dev_Order, "Server"
          UNION SELECT 2 as dev_Order, "Singleboard Computer (SBC)"
          UNION SELECT 2 as dev_Order, "NAS"

          UNION SELECT 3 as dev_Order, "Domotic"
          UNION SELECT 3 as dev_Order, "IP Camera"
          UNION SELECT 3 as dev_Order, "Game Console"
          UNION SELECT 3 as dev_Order, "SmartTV"
          UNION SELECT 3 as dev_Order, "TV Decoder"
          UNION SELECT 3 as dev_Order, "Virtual Assistance"

          UNION SELECT 4 as dev_Order, "Clock"
          UNION SELECT 4 as dev_Order, "House Appliance"
          UNION SELECT 4 as dev_Order, "Phone"
          UNION SELECT 4 as dev_Order, "Radio"

          -- network devices
          UNION SELECT 5 as dev_Order, "AP"
          UNION SELECT 5 as dev_Order, "Gateway"
          UNION SELECT 5 as dev_Order, "Firewall"
          UNION SELECT 5 as dev_Order, "Powerline"
          UNION SELECT 5 as dev_Order, "Switch"
          UNION SELECT 5 as dev_Order, "WLAN"
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
//  Query the List of Pholus entries
//------------------------------------------------------------------------------
function getPholus() {
  global $db;

  // SQL
  $mac = $_REQUEST['mac']; 

  if ($mac == "Internet") // Not performing data lookup for router (improvement idea for later maybe)
  {
    echo "false";
    return;
  }

  if (false === filter_var($mac , FILTER_VALIDATE_MAC)) {
    throw new Exception('Invalid mac address');
  }
  else{
    $sql = 'SELECT * from Pholus_Scan where MAC ="'.$mac.'" and Record_Type not in ("Question")';

    // array 
    $tableData = array();

    // execute query
    $result = $db->query($sql);
    while ($row = $result -> fetchArray (SQLITE3_ASSOC)){   
      // Push row data      
      $tableData[] = array( 'Index'         => $row['Index'],
                            'Info'          => $row['Info'],
                            'Time'          => $row['Time'],
                            'MAC'           => $row['MAC'],
                            'IP_v4_or_v6'   => $row['IP_v4_or_v6'],
                            'Record_Type'   => $row['Record_Type'],
                            'Value'         => $row['Value'],
                            'Extra'         => $row['Extra']);
    }

    if(count($tableData) == 0)
    {
      echo "false";
    } else{
      // Return json
      echo (json_encode ($tableData));
    }
  }
}

//------------------------------------------------------------------------------
//  Query the List of Nmap entries
//------------------------------------------------------------------------------
function getNmap() {
  global $db;

  // SQL
  $mac = $_REQUEST['mac']; 

  if ($mac == "Internet") // Not performing data lookup for router (improvement idea for later maybe)
  {
    echo "false";
    return;
  }

  if (false === filter_var($mac , FILTER_VALIDATE_MAC)) {
    throw new Exception('Invalid mac address');
  }
  else{
    // $sql = 'SELECT * from Nmap_Scan where MAC ="'.$mac.'" ';
    $sql = 'select * from (select * from Nmap_Scan  INNER JOIN Devices on Nmap_Scan.MAC = Devices.dev_MAC) where MAC = "'.$mac.'" ';

    // array 
    $tableData = array();

    // execute query
    $result = $db->query($sql);
    while ($row = $result -> fetchArray (SQLITE3_ASSOC)){   
      // Push row data      
      $tableData[] = array( 'Index'         => $row['Index'],
                            'MAC'           => $row['MAC'],
                            'Port'          => $row['Port'],
                            'Time'          => $row['Time'],
                            'State'         => $row['State'],
                            'Service'       => $row['Service'],                            
                            'IP'            => $row['dev_LastIP'],                            
                            'Extra'         => $row['Extra']);
    }

    if(count($tableData) == 0)
    {
      echo "false";
    } else{
      // Return json
      echo (json_encode ($tableData));
    }
  }
}

// -------------------------------------------------------------------------------------------

function saveNmapPort()
{

  $portIndex = $_REQUEST['id'];
  $value = $_REQUEST['value'];
 
  if(is_integer((int)$portIndex))
  {
    global $db;
     // sql
    $sql = 'UPDATE Nmap_Scan SET "Extra" = "'. $value .'" WHERE "Index"=' . $portIndex ;
    // update Data
    $result = $db->query($sql);

    // check result
    if ($result == TRUE) {
      echo 'OK';
    } else {
      echo 'KO';
    }
  }
 
}

// ----------------------------------------------------------------------------------------
function updateNetworkLeaf()
{
  $nodeMac = $_REQUEST['value'];
  $leafMac = $_REQUEST['id'];

  if ((false === filter_var($nodeMac , FILTER_VALIDATE_MAC) && $nodeMac != "Internet" && $nodeMac != "") || false === filter_var($leafMac , FILTER_VALIDATE_MAC) ) {
    throw new Exception('Invalid mac address');
  }
  else
  {
    global $db;
    // sql
    $sql = 'UPDATE Devices SET "dev_Network_Node_MAC_ADDR" = "'. $nodeMac .'" WHERE "dev_MAC"="' . $leafMac.'"' ;
    // update Data
    $result = $db->query($sql);

    // check result
    if ($result == TRUE) {
      echo 'OK';
    } else {
      echo 'KO';
    }
  }

}

// ----------------------------------------------------------------------------------------
function overwriteIconType()
{
  $mac = $_REQUEST['mac'];
  $icon = $_REQUEST['icon'];

  if ((false === filter_var($mac , FILTER_VALIDATE_MAC) && $mac != "Internet" && $mac != "")  ) {
    throw new Exception('Invalid mac address');
  }
  else
  {
    global $db;
    // sql    
    $sql = 'UPDATE Devices SET "dev_Icon" = "'. $icon .'" where dev_DeviceType in (select dev_DeviceType from Devices where dev_MAC = "' . $mac.'")' ;
    // update Data
    $result = $db->query($sql);

    // check result
    if ($result == TRUE) {
      echo 'OK';
    } else {
      echo lang('BackDevices_Device_UpdDevError');
    }
  }

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