<?php

  // External files
  require 'db.php';
  require 'util.php';
 
//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
  // Set maximum execution time to 1 minute
  ini_set ('max_execution_time','60');
  
  // Open DB
  OpenDB();

  // Action functions
  if (isset ($_REQUEST['action']) && !empty ($_REQUEST['action'])) {
    $action = $_REQUEST['action'];
    switch ($action) {
      case 'totals':           queryTotals();       break;
      case 'list':             queryList();         break;
      case 'queryDeviceData':  queryDeviceData();   break;
      case 'updateData':       updateDeviceData();  break;
      case 'calendar':         queryCalendarList(); break;
      case 'queryOwners':      queryOwners();       break;
      case 'queryDeviceTypes': queryDeviceTypes();  break;
      case 'queryGroups':      queryGroups();       break;
      default:                 logServerConsole ('Action: '. $action); break;
    }
  }


//------------------------------------------------------------------------------
//  Query total numbers of Devices by status
//------------------------------------------------------------------------------
function queryTotals() {
  global $db;

  // All
  $result = $db->query('SELECT COUNT(*) FROM Devices ');
  $row = $result -> fetchArray (SQLITE3_NUM);
  $devices = $row[0];
  
  // Connected
  $result = $db->query('SELECT COUNT(*) FROM Devices ' . getDeviceCondition ('connected') );
  $row = $result -> fetchArray (SQLITE3_NUM);
  $connected = $row[0];
  
  // New
  $result = $db->query('SELECT COUNT(*) FROM Devices ' . getDeviceCondition ('new') );
  $row = $result -> fetchArray (SQLITE3_NUM);
  $newDevices = $row[0];
  
  // Down Alerts
  $result = $db->query('SELECT COUNT(*) FROM Devices ' . getDeviceCondition ('down'));
  $row = $result -> fetchArray (SQLITE3_NUM);
  $devicesDownAlert = $row[0];

  echo (json_encode (array ($devices, $connected, $newDevices, $devicesDownAlert)));
}


//------------------------------------------------------------------------------
//  Query the List of devices in a determined Status
//------------------------------------------------------------------------------
function queryList() {
  global $db;

  // Request Parameters
  $periodDate = getDateFromPeriod();

  // SQL
  $condition = getDeviceCondition ($_REQUEST['status']);

  $result = $db->query('SELECT *,
                          CASE WHEN dev_AlertDeviceDown=1 AND dev_PresentLastScan=0 THEN "Down"
                               WHEN dev_FirstConnection >= ' . $periodDate . ' THEN "New"
                               WHEN dev_PresentLastScan=1 THEN "On-line"
                               ELSE "Off-line"
                          END AS dev_Status
                        FROM Devices ' . $condition);

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
                                  $row['dev_Status'],
                                  $row['dev_MAC'], // MAC (hidden)
                                  formatIPlong ($row['dev_LastIP']) // IP orderable
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
//  Query the List of Owners
//------------------------------------------------------------------------------
function queryOwners() {
  global $db;

  // SQL
  $result = $db->query('SELECT DISTINCT 1 as dev_Order, dev_Owner
                        FROM Devices
                        WHERE dev_Owner <> "(unknown)" AND dev_Owner <> ""
                          AND dev_Favorite = 1
                        UNION
                        SELECT DISTINCT 2 as dev_Order, dev_Owner
                        FROM Devices
                        WHERE dev_Owner <> "(unknown)" AND dev_Owner <> ""
                          AND dev_Favorite = 0
                          AND dev_Owner NOT IN (SELECT dev_Owner FROM Devices WHERE dev_Favorite = 1)
                        ORDER BY 1,2 ');

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
function queryDeviceTypes() {
  global $db;

  // SQL
  $result = $db->query('SELECT DISTINCT 9 as dev_Order, dev_DeviceType
                        FROM Devices
                        WHERE dev_DeviceType NOT IN ("",
                                                     "Smartphone", "Tablet",
                                                     "Laptop", "Mini PC", "PC", "Printer", "Server",
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

                        UNION SELECT 10 as dev_Order, "Other"

                        ORDER BY 1,2 ');

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
function queryGroups() {
  global $db;

  // SQL
  $result = $db->query('SELECT DISTINCT 1 as dev_Order, dev_Group
                        FROM Devices
                        WHERE dev_Group <> "(unknown)" AND dev_Group <> "Others" AND dev_Group <> ""
                        UNION SELECT 1 as dev_Order, "Always on"
                        UNION SELECT 1 as dev_Order, "Friends"
                        UNION SELECT 1 as dev_Order, "Personal"
                        UNION SELECT 2 as dev_Order, "Others"
                        ORDER BY 1,2 ');

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
//  Query the List of devices for calendar
//------------------------------------------------------------------------------
function queryCalendarList() {
  global $db;

  // Request Parameters
  $periodDate = getDateFromPeriod();

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
//  Query Device Data
//------------------------------------------------------------------------------
function queryDeviceData() {
  global $db;

  // Request Parameters
  $periodDate = getDateFromPeriod();
  $mac = $_REQUEST['mac'];

  // Device Data
  $result = $db->query('SELECT *,
                          CASE WHEN dev_AlertDeviceDown=1 AND dev_PresentLastScan=0 THEN "Down"
                               WHEN dev_PresentLastScan=1 THEN "On-line"
                               ELSE "Off-line" END as dev_Status
                        FROM Devices
                        WHERE dev_MAC="' . $mac .'"');

  $row = $result -> fetchArray (SQLITE3_ASSOC);
  $deviceData = $row;
  $deviceData['dev_FirstConnection'] = formatDate ($row['dev_FirstConnection']); // Date formated
  $deviceData['dev_LastConnection'] =  formatDate ($row['dev_LastConnection']);  // Date formated

  // Count Totals
  $condicion = ' WHERE eve_MAC="' . $mac .'" AND eve_DateTime >= ' . $periodDate;

  // Connections
  $result = $db->query('SELECT COUNT(*) FROM Sessions
                          WHERE ses_MAC="' . $mac .'"
                          AND (  ses_DateTimeConnection >= ' . $periodDate . '
                              OR ses_DateTimeDisconnection >= ' . $periodDate . '
                              OR ses_StillConnected = 1 ) ');
  $row = $result -> fetchArray (SQLITE3_NUM);
  $deviceData['dev_Sessions'] = $row[0];
  
  // Events
  $result = $db->query('SELECT COUNT(*) FROM Events ' . $condicion . ' AND eve_EventType <> "Connected" AND eve_EventType <> "Disconnected" ');
  $row = $result -> fetchArray (SQLITE3_NUM);
  $deviceData['dev_Events'] = $row[0];

  // Donw Alerts
  $result = $db->query('SELECT COUNT(*) FROM Events ' . $condicion . ' AND eve_EventType = "Device Down"');
  $row = $result -> fetchArray (SQLITE3_NUM);
  $deviceData['dev_DownAlerts'] = $row[0];

  // Presence hours
  $result = $db->query('SELECT SUM (julianday (IFNULL (ses_DateTimeDisconnection, DATETIME("now")))
                                  - julianday (CASE WHEN ses_DateTimeConnection < ' . $periodDate . ' THEN ' . $periodDate . '
                                               ELSE ses_DateTimeConnection END)) *24
                        FROM Sessions
                        WHERE ses_MAC="' . $mac .'"
                          AND ses_DateTimeConnection IS NOT NULL
                          AND (ses_DateTimeDisconnection IS NOT NULL OR ses_StillConnected = 1 )
                          AND (   ses_DateTimeConnection    >= ' . $periodDate . '
                               OR ses_DateTimeDisconnection >= ' . $periodDate . '
                               OR ses_StillConnected = 1 ) ');
  $row = $result -> fetchArray (SQLITE3_NUM);
  $deviceData['dev_PresenceHours'] = round ($row[0]);


  // Return json
  echo (json_encode ($deviceData));
}


//------------------------------------------------------------------------------
//  Status Where conditions
//------------------------------------------------------------------------------
function getDeviceCondition ($deviceStatus) {
  // Request Parameters
  $periodDate = getDateFromPeriod();

  switch ($deviceStatus) {
    case 'all':
        return  '';
    case 'connected':
        return 'WHERE dev_PresentLastScan=1';
    case 'new':
        return 'WHERE dev_FirstConnection >= ' . $periodDate;
    case 'down':
        return 'WHERE dev_AlertDeviceDown=1 AND dev_PresentLastScan=0';
    case 'favorites':
        return 'WHERE dev_Favorite=1';
    default:
        return 'WHERE 1=0';
  }
}


//------------------------------------------------------------------------------
//  Update Device Data
//------------------------------------------------------------------------------
function updateDeviceData() {
  global $db;

  // sql
  $sql = 'UPDATE Devices SET
                 dev_Name            = "'. $_REQUEST['name']           .'",
                 dev_Owner           = "'. $_REQUEST['owner']          .'",
                 dev_DeviceType      = "'. $_REQUEST['type']           .'",
                 dev_Vendor          = "'. $_REQUEST['vendor']         .'",
                 dev_Favorite        = "'. $_REQUEST['favorite']       .'",
                 dev_Group           = "'. $_REQUEST['group']          .'",
                 dev_Comments        = "'. $_REQUEST['comments']       .'",
                 dev_StaticIP        = "'. $_REQUEST['staticIP']       .'",
                 dev_ScanCycle       = "'. $_REQUEST['scancycle']      .'",
                 dev_AlertEvents     = "'. $_REQUEST['alertevents']    .'",
                 dev_AlertDeviceDown = "'. $_REQUEST['alertdown']      .'",
                 dev_SkipRepeated    = "'. $_REQUEST['skiprepeated']   .'"
          WHERE dev_MAC="' . $_REQUEST['mac'] .'"';
  // update Data
  $result = $db->query($sql);

  // check result
  if ($result == TRUE) {
    echo "Device updated successfully";
  } else {
    echo "Error updating device\n\n". $sql .'\n\n' . $db->lastErrorMsg();
  }

}


?>
