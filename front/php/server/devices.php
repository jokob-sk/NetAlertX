<?php
//------------------------------------------------------------------------------
//  NetAlertX
//  Open Source Network Guard / WIFI & LAN intrusion detector
//
//  devices.php - Front module. Server side. Manage Devices
//------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------

// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺

  // External files
  require dirname(__FILE__).'/init.php';

  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

  //------------------------------------------------------------------------------
  //  Action selector
  //------------------------------------------------------------------------------
  // Set maximum execution time to 15 seconds

  ini_set ('max_execution_time','30');

  // Action functions
  if (isset ($_REQUEST['action']) && !empty ($_REQUEST['action'])) {
    $action = $_REQUEST['action'];
    switch ($action) {
                                                                                      // check server/api_server/api_server_start.py for equivalents
      case 'getServerDeviceData':     getServerDeviceData();                   break; // equivalent: get_device_data
      case 'deleteDevice':            deleteDevice();                          break; // equivalent: delete_device(mac)
      case 'deleteAllWithEmptyMACs':  deleteAllWithEmptyMACs();                break; // equivalent: delete_all_with_empty_macs

      case 'deleteAllDevices':        deleteAllDevices();                      break; // equivalent: delete_devices(macs)
      case 'deleteUnknownDevices':    deleteUnknownDevices();                  break; // equivalent: delete_unknown_devices
      case 'deleteEvents':            deleteEvents();                          break; // equivalent: delete_events
      case 'deleteEvents30':          deleteEvents30();                        break; // equivalent: delete_events_30
      case 'deleteActHistory':        deleteActHistory();                      break; // equivalent: delete_online_history
      case 'deleteDeviceEvents':      deleteDeviceEvents();                    break; // equivalent: delete_device_events(mac)

      case 'ExportCSV':               ExportCSV();                             break; // equivalent: export_devices
      case 'ImportCSV':               ImportCSV();                             break; // equivalent: import_csv

      case 'getDevicesTotals':        getDevicesTotals();                      break; // equivalent: devices_totals
      case 'getDevicesListCalendar':  getDevicesListCalendar();                break; // equivalent: devices_by_status

      case 'updateNetworkLeaf':       updateNetworkLeaf();                     break; // equivalent: update_device_column(mac, column_name, column_value)

      default:                        logServerConsole ('Action: '. $action);  break; // equivalent:
    }
  }



//------------------------------------------------------------------------------
//  Query Device Data
//------------------------------------------------------------------------------
function getServerDeviceData() {
  global $db;

  // Request Parameters
  $periodDate = getDateFromPeriod();
  $mac = $_REQUEST['mac'];

  // Check for "new" MAC case
  if ($mac === "new") {
    $now = date('Y-m-d   H:i');
    $deviceData = [
      "devMac" => "",
      "devName" => "",
      "devOwner" => "",
      "devType" => "",
      "devVendor" => "",
      "devFavorite" => 0,
      "devGroup" => "",
      "devComments" => "",
      "devFirstConnection" => $now,
      "devLastConnection" => $now,
      "devLastIP" => "",
      "devStaticIP" => 0,
      "devScan" => 0,
      "devLogEvents" => 0,
      "devAlertEvents" => 0,
      "devAlertDown" => 0,
      "devParentRelType" => "default",
      "devReqNicsOnline" => 0,
      "devSkipRepeated" => 0,
      "devLastNotification" => "",
      "devPresentLastScan" => 0,
      "devIsNew" => 1,
      "devLocation" => "",
      "devIsArchived" => 0,
      "devParentMAC" => "",
      "devParentPort" => "",
      "devIcon" => "",
      "devGUID" => "",
      "devSite" => "",
      "devSSID" => "",
      "devSyncHubNode" => "",
      "devSourcePlugin" => "",
      "devCustomProps" => "",
      "devStatus" => "Unknown",
      "devIsRandomMAC" => false,
      "devSessions" => 0,
      "devEvents" => 0,
      "devDownAlerts" => 0,
      "devPresenceHours" => 0,
      "devFQDN"  => ""
    ];
    echo json_encode($deviceData);
    return;
  }


  // Get current date (used in presence calc)
  $currentdate = date("Y-m-d H:i:s");

  // Fetch Device Info + Children + Events Stats
  $sql =<<<SQL
    SELECT
      d.rowid,
      d.*,
      CASE
        WHEN d.devAlertDown != 0 AND d.devPresentLastScan = 0 THEN "Down"
        WHEN d.devPresentLastScan = 1 THEN "On-line"
        ELSE "Off-line"
      END AS devStatus,

      -- Event counters
      (SELECT COUNT(*) FROM Sessions
      WHERE ses_MAC = d.devMac AND (
        ses_DateTimeConnection >= $periodDate OR
        ses_DateTimeDisconnection >= $periodDate OR
        ses_StillConnected = 1
      )
      ) AS devSessions,

      (SELECT COUNT(*) FROM Events
      WHERE eve_MAC = d.devMac AND
            eve_DateTime >= $periodDate AND
            eve_EventType NOT IN ("Connected", "Disconnected")
      ) AS devEvents,

      (SELECT COUNT(*) FROM Events
      WHERE eve_MAC = d.devMac AND
            eve_DateTime >= $periodDate AND
            eve_EventType = "Device Down"
      ) AS devDownAlerts,

      (SELECT CAST(( MAX (0, SUM (julianday (IFNULL (ses_DateTimeDisconnection,'$currentdate'))
                      - julianday (CASE WHEN ses_DateTimeConnection < $periodDate
                                        THEN $periodDate
                                        ELSE ses_DateTimeConnection END)) *24 )) AS INT)
      FROM Sessions
      WHERE ses_MAC = d.devMac AND
            ses_DateTimeConnection IS NOT NULL AND
            (ses_DateTimeDisconnection IS NOT NULL OR ses_StillConnected = 1) AND
            (
              ses_DateTimeConnection >= $periodDate OR
              ses_DateTimeDisconnection >= $periodDate OR
              ses_StillConnected = 1
            )
      ) AS devPresenceHours

    FROM Devices d
    WHERE d.devMac = "$mac" OR CAST(d.rowid AS TEXT) = "$mac"
  SQL;

  $row = $db->query($sql)->fetchArray(SQLITE3_ASSOC);
  $deviceData = $row;
  $mac = $deviceData['devMac'];

  $deviceData['devFirstConnection'] = formatDate($deviceData['devFirstConnection']);
  $deviceData['devLastConnection']  = formatDate($deviceData['devLastConnection']);
  $deviceData['devIsRandomMAC']     = isRandomMAC($mac);

  // Fetch children once and split in PHP
  $sql = 'SELECT rowid, * FROM Devices WHERE devParentMAC = "' . $mac . '" ORDER BY devPresentLastScan DESC';
  $result = $db->query($sql);
  $children = [];
  $childrenNics = [];

  while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
      $children[] = $row;
      if ($row['devParentRelType'] === 'nic') {
          $childrenNics[] = $row;
      }
  }

  $deviceData['devChildrenDynamic']     = $children;
  $deviceData['devChildrenNicsDynamic'] = $childrenNics;

  // Return JSON
  echo json_encode($deviceData);

}

//------------------------------------------------------------------------------
//  Delete Device
//------------------------------------------------------------------------------
function deleteDevice() {
  global $db;

  // sql
  $sql = 'DELETE FROM Devices WHERE devMac="' . $_REQUEST['mac'] .'"';
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
  $sql = 'DELETE FROM Devices WHERE devMac=""';
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
  $sql = 'DELETE FROM Devices WHERE devName="(unknown)" OR devName="(name not found)"';
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
//  Export CSV of devices
//------------------------------------------------------------------------------
function ExportCSV() {

  header("Content-Type: application/octet-stream");
  header("Content-Transfer-Encoding: Binary");
  header("Content-disposition: attachment; filename=\"devices.csv\"");

  global $db;
  $func_result = $db->query("SELECT * FROM Devices");

  // prepare CSV header row
  $columns = getDevicesColumns();

  // wrap the headers with " (quotes)
  $resultCSV = '"'.implode('","', $columns).'"'."\n";

  // retrieve the devices from the DB
  while ($row = $func_result->fetchArray(SQLITE3_ASSOC)) {

    // loop through columns and add values to the string
    $index = 0;
    foreach ($columns as $columnName) {
      // Escape special chars (e.g.quotes) inside fields by replacing them with html definitions
      $fieldValue = encodeSpecialChars($row[$columnName]);

      // add quotes around the value to prevent issues with commas in fields
      $resultCSV .= '"'.$fieldValue.'"';

      // detect last loop - skip as no comma needed
      if ($index != count($columns) - 1) {
        $resultCSV .= ',';
      }
      $index++;
    }

    // add a new line for the next row
    $resultCSV .= "\n";
  }

  //write the built CSV string
  echo $resultCSV;
}


//------------------------------------------------------------------------------
//  Import CSV of devices
//------------------------------------------------------------------------------
function ImportCSV() {

  global $db;
  $file = '../../../config/devices.csv';
  $data = "";
  $skipped = "";
  $error = "";

  // check if content passed in query string
  if(isset ($_POST['content']) && !empty ($_POST['content']))
  {
    // Decode the Base64 string
    // $data = base64_decode($_POST['content']);
    $data = base64_decode($_POST['content'], true);  // The second parameter ensures safe decoding

    // // Ensure the decoded data is treated as UTF-8 text
    // $data = mb_convert_encoding($data, 'UTF-8', 'UTF-8');

  } else if (file_exists($file)) { // try to get the data form the file

    // Read the CSV file
    $data = file_get_contents($file);
  } else {
    echo lang('BackDevices_DBTools_ImportCSVMissing');
  }

  if($data != "")
  {
    // data cleanup - new lines breaking the CSV
    $data = preg_replace_callback('/"([^"]*)"/', function($matches) {
      // Replace all \n within the quotes with a space
      return str_replace("\n", " ", $matches[0]); // Replace with a space
    }, $data);

    $lines = explode("\n", $data);

    // Get the column headers from the first line of the CSV
    $header = str_getcsv(array_shift($lines));
    $header = array_map('trim', $header);

    // Delete everything form the DB table
    $sql = 'DELETE FROM Devices';
    $result = $db->query($sql);

    // Build the SQL statement
    $sql = "INSERT INTO Devices (" . implode(', ', $header) . ") VALUES ";

    // Parse data from CSV file line by line (max 10000 lines)
    $index = 0;
    foreach($lines as $row) {
      $rowArray = str_getcsv($row);

      if (count($rowArray) === count($header)) {
        // Make sure the number of columns matches the header
        $rowArray = array_map(function ($value) {
          return "'" . SQLite3::escapeString(trim($value)) . "'";
        }, $rowArray);

        $sql .= "(" . implode(', ', $rowArray) . "), ";
      } else {
        $skipped .= ($index + 1) . ",";
      }

      $index++;
    }

    // Remove the trailing comma and space from SQL
    $sql = rtrim($sql, ', ');

    // Execute the SQL query
    $result = $db->query($sql);

    if($error === "") {
      // Import successful
      echo lang('BackDevices_DBTools_ImportCSV') . " (Skipped lines: " . $skipped . ") ";
    } else {
      // An error occurred while writing to the DB, display the last error message
      echo lang('BackDevices_DBTools_ImportCSVError') . "\n" . $error . "\n" . $sql . "\n\n" . $result;
    }
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
          (SELECT COUNT(*) FROM Devices '. getDeviceCondition ('my').') as devices,
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
//  Determine if Random MAC
//------------------------------------------------------------------------------

function isRandomMAC($mac) {
  $isRandom = false;

  // if detected as random, make sure it doesn't start with a prefix which teh suer doesn't want to mark as random
  $setting = getSettingValue("UI_NOT_RANDOM_MAC");
  $prefixes = createArray($setting);

  $isRandom = in_array($mac[1], array("2", "6", "A", "E", "a", "e"));

  // If detected as random, make sure it doesn't start with a prefix which the user doesn't want to mark as random
  if ($isRandom) {
      foreach ($prefixes as $prefix) {
          if (strpos($mac, $prefix) === 0) {
              $isRandom = false;
              break;
          }
      }
  }

  return $isRandom;
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
    if ($row['devFavorite'] == 1) {
      $row['devName'] = '<span class="text-yellow">&#9733</span>&nbsp'. $row['devName'];
    }

    $tableData[] = array ('id'       => $row['devMac'],
                          'title'    => $row['devName'],
                          'favorite' => $row['devFavorite']);
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query Device Data
//------------------------------------------------------------------------------

// ----------------------------------------------------------------------------------------
function updateNetworkLeaf()
{
  $nodeMac = $_REQUEST['value']; // parent
  $leafMac = $_REQUEST['id'];    // child

  if ((false === filter_var($nodeMac , FILTER_VALIDATE_MAC) && $nodeMac != "Internet" && $nodeMac != "") || false === filter_var($leafMac , FILTER_VALIDATE_MAC) ) {
    throw new Exception('Invalid mac address');
  }
  else
  {
    global $db;
    // sql
    $sql = 'UPDATE Devices SET "devParentMAC" = "'. $nodeMac .'" WHERE "devMac"="' . $leafMac.'"' ;
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


//------------------------------------------------------------------------------
//  Status Where conditions
//------------------------------------------------------------------------------
function getDeviceCondition ($deviceStatus) {
  switch ($deviceStatus) {
    case 'all':        return 'WHERE devIsArchived=0';                                                        break;
    case 'my':         return 'WHERE devIsArchived=0';                                                        break;
    case 'connected':  return 'WHERE devIsArchived=0 AND devPresentLastScan=1';                              break;
    case 'favorites':  return 'WHERE devIsArchived=0 AND devFavorite=1';                                     break;
    case 'new':        return 'WHERE devIsArchived=0 AND devIsNew=1';                                    break;
    case 'down':       return 'WHERE devIsArchived=0 AND devAlertDown !=0 AND devPresentLastScan=0';  break;
    case 'archived':   return 'WHERE devIsArchived=1';                                                        break;
    default:           return 'WHERE 1=0';                                                                   break;
  }
}


?>