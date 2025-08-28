<?php
//------------------------------------------------------------------------------
//  NetAlertX
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  events.php - Front module. Server side. Manage Events
//------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------
//------------------------------------------------------------------------------

// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /sessions /events
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺

// External files
require dirname(__FILE__).'/init.php';

//------------------------------------------------------------------------------
// check if authenticated
require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
  // Set maximum execution time to 1 minute
  ini_set ('max_execution_time','60');

  // Action functions
  if (isset ($_REQUEST['action']) && !empty ($_REQUEST['action'])) {
    $action = $_REQUEST['action'];
    switch ($action) {
      case 'getEventsTotals':    getEventsTotals();                       break;
      case 'getEvents':          getEvents();                             break;                      
      case 'getDeviceSessions':  getDeviceSessions();                     break;
      case 'getDevicePresence':  getDevicePresence();                     break;
      case 'getEventsCalendar':  getEventsCalendar();                     break;
      default:                   logServerConsole ('Action: '. $action);  break;
    }
  }


//------------------------------------------------------------------------------
//  Query total numbers of Events
//------------------------------------------------------------------------------
function getEventsTotals() {
  global $db;

  // Request Parameters
  $periodDate = $_REQUEST['period'];

  $periodDateSQL = "";
  $days = "";

  switch ($periodDate) {
    case '7 days':
      $days = "7";
      break;
    case '1 month':
      $days = "30";
      break;
    case '1 year':
      $days = "365";
      break;
    case '100 years':
      $days = "3650"; //10 years
      break;
    default:
    $days = "1";    
  }  

  $periodDateSQL = "-".$days." day"; 

  $resultJSON = "";

  // check cache if JSON available in a cookie
  if(getCache("getEventsTotals".$days) != "")
  {
    $resultJSON = getCache("getEventsTotals".$days);
  } else
  {
    // one query to get all numbers, which is quicker than multiple queries
    $sql = "select 
              (SELECT Count(*) FROM Events  WHERE eve_DateTime >=  date('now', '".$periodDateSQL."')) as all_events, 
              (SELECT Count(*) FROM Sessions as sessions WHERE (  ses_DateTimeConnection >= date('now', '".$periodDateSQL."') OR ses_DateTimeDisconnection >= date('now', '".$periodDateSQL."') OR ses_StillConnected = 1 ))  as sessions,
              (SELECT Count(*) FROM Sessions WHERE ((ses_DateTimeConnection IS NULL    AND ses_DateTimeDisconnection >= date('now', '".$periodDateSQL."' )) OR (ses_DateTimeDisconnection IS NULL AND ses_StillConnected = 0 AND ses_DateTimeConnection >= date('now', '".$periodDateSQL."' )))) as missing,
              (SELECT Count(*) FROM Events  WHERE eve_DateTime >= date('now', '".$periodDateSQL."') AND eve_EventType LIKE 'VOIDED%' ) as voided, 
              (SELECT Count(*) FROM Events  WHERE eve_DateTime >= date('now', '".$periodDateSQL."') AND eve_EventType LIKE 'New Device' ) as new,
              (SELECT Count(*) FROM Events  WHERE eve_DateTime >= date('now', '".$periodDateSQL."') AND eve_EventType LIKE 'Device Down' ) as down";

    $result = $db->query($sql);
    $row = $result -> fetchArray (SQLITE3_NUM);
    $resultJSON = json_encode (array ($row[0], $row[1], $row[2], $row[3], $row[4], $row[5]));

    // save JSON result to cache
    setCache("getEventsTotals".$days, $resultJSON );
  }
  
  // Return json  
  echo ($resultJSON);
}


//------------------------------------------------------------------------------
//  Query the List of events
//------------------------------------------------------------------------------
function getEvents() {
  global $db;

  // Request Parameters
  $type       = $_REQUEST ['type'];
  $periodDate = getDateFromPeriod();

  // SQL 
  $SQL1 = 'SELECT eve_DateTime AS eve_DateTimeOrder, devName, devOwner, eve_DateTime, eve_EventType, NULL, NULL, NULL, NULL, eve_IP, NULL, eve_AdditionalInfo, NULL, devMac, eve_PendingAlertEmail
           FROM Events_Devices 
           WHERE eve_DateTime >= '. $periodDate;
 
  $SQL2 = 'SELECT IFNULL (ses_DateTimeConnection, ses_DateTimeDisconnection) ses_DateTimeOrder,
                  devName, devOwner, Null, Null, ses_DateTimeConnection, ses_DateTimeDisconnection, NULL, NULL, ses_IP, NULL,  ses_AdditionalInfo, ses_StillConnected, devMac
           FROM Sessions_Devices ';

  // SQL Variations for status
  switch ($type) {
    case 'all':     $SQL = $SQL1;                                         break;
    case 'sessions':
      $SQL = $SQL2 . ' WHERE (  ses_DateTimeConnection >= '. $periodDate .' OR ses_DateTimeDisconnection >= '. $periodDate .' OR ses_StillConnected = 1 ) ';
      break;
    case 'missing':
      $SQL = $SQL2 . ' WHERE    (ses_DateTimeConnection    IS NULL AND ses_DateTimeDisconnection >= '. $periodDate .' )
                             OR (ses_DateTimeDisconnection IS NULL AND ses_StillConnected = 0 AND ses_DateTimeConnection >= '. $periodDate .' )';
      break;
    case 'voided':  $SQL = $SQL1 .' AND eve_EventType LIKE "VOIDED%" ';   break;
    case 'new':     $SQL = $SQL1 .' AND eve_EventType = "New Device" ';   break;
    case 'down':    $SQL = $SQL1 .' AND eve_EventType = "Device Down" ';  break;
    default:        $SQL = $SQL1 .' AND 1==0 ';                           break;
  }

  // Query
  $result = $db->query($SQL);

  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_NUM)) {
    if ($type == 'sessions' || $type == 'missing' ) {
      // Duration
      if (!empty ($row[5]) && !empty($row[6]) ) {
        $row[7] = formatDateDiff ($row[5], $row[6]);
        $row[8] = abs(strtotime($row[6]) - strtotime($row[5]));
      } elseif ($row[12] == 1) {
        $row[7] = formatDateDiff ($row[5], '');
        $row[8] = abs(strtotime("now") - strtotime($row[5]));
      } else {
        $row[7] = '...';
        $row[8] = 0;
      }

      // Connection
      if (!empty ($row[5]) ) {
        $row[5] = formatDate ($row[5]);
      } else {
        $row[5] = '<missing event>';
      }

      // Disconnection
      if (!empty ($row[6]) ) {
        $row[6] = formatDate ($row[6]);
      } elseif ($row[12] == 0) {
        $row[6] = '<missing event>';
      } else {
        $row[6] = '...';
      }

    } else {
      // Event Date
      $row[3] = formatDate ($row[3]);
    }

    // IP Order
    $row[10] = formatIPlong ($row[9]);
    $tableData['data'][] = $row;
  }

  // Control no rows
  if (empty($tableData['data'])) {
    $tableData['data'] = '';
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query Device Sessions
//------------------------------------------------------------------------------
function getDeviceSessions() {
  global $db;

  // Request Parameters
  $mac        = $_REQUEST['mac'];
  $periodDate = getDateFromPeriod();

  // SQL 
  $SQL = 'SELECT IFNULL (ses_DateTimeConnection, ses_DateTimeDisconnection) ses_DateTimeOrder,
                         ses_EventTypeConnection, ses_DateTimeConnection,
                         ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_StillConnected,
                         ses_IP, ses_AdditionalInfo 
          FROM Sessions
          WHERE ses_MAC="' . $mac .'"
            AND (  ses_DateTimeConnection >= '. $periodDate .'
                OR ses_DateTimeDisconnection >= '. $periodDate .'
                OR ses_StillConnected = 1 ) ';
  $result = $db->query($SQL);
  
  // arrays of rows
  $tableData = array();
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    // Connection DateTime
    if ($row['ses_EventTypeConnection'] == '<missing event>') {
      $ini = $row['ses_EventTypeConnection'];
    } else {
      $ini = formatDate ($row['ses_DateTimeConnection']);
    }
    
    // Disconnection DateTime
    if ($row['ses_StillConnected'] == true) {
      $end = '...'; 
    } elseif ($row['ses_EventTypeDisconnection'] == '<missing event>') {
      $end = $row['ses_EventTypeDisconnection'];      
    } else {
      $end = formatDate ($row['ses_DateTimeDisconnection']);
    }

    // Duration
    if ($row['ses_EventTypeConnection'] == '<missing event>' || $row['ses_EventTypeConnection'] == NULL || $row['ses_EventTypeDisconnection'] == '<missing event>' || $row['ses_EventTypeDisconnection'] == NULL) {
      $dur = '...';
    } elseif ($row['ses_StillConnected'] == true) {
      $dur = formatDateDiff ($row['ses_DateTimeConnection'], '');  //***********
    } else {
      $dur = formatDateDiff ($row['ses_DateTimeConnection'], $row['ses_DateTimeDisconnection']);
    }
    
    // Additional Info
    $info = $row['ses_AdditionalInfo'];
    if ($row['ses_EventTypeConnection'] == 'New Device' ) {
      $info = $row['ses_EventTypeConnection'] .':   '. $info;
    }

    // Push row data
    $tableData['data'][] = array($row['ses_DateTimeOrder'], $ini, $end, $dur, $row['ses_IP'], $info);
  }

  // Control no rows
  if (empty($tableData['data'])) {
    $tableData['data'] = '';
  }

  // Return json
  echo (json_encode ($tableData));
}


//------------------------------------------------------------------------------
//  Query Device Presence Calendar
//------------------------------------------------------------------------------
function getDevicePresence() {         
  global $db;

  // Request Parameters
  $mac        = $_REQUEST['mac'];
  $startDate  = '"'. formatDateISO ($_REQUEST ['start']) .'"';
  $endDate    = '"'. formatDateISO ($_REQUEST ['end'])   .'"';

  // SQL
  $SQL = 'SELECT ses_EventTypeConnection, ses_DateTimeConnection,
                 ses_EventTypeDisconnection, ses_DateTimeDisconnection, ses_IP, ses_AdditionalInfo, ses_StillConnected,
            
                 CASE
                   WHEN ses_EventTypeConnection = "<missing event>" THEN
                        IFNULL ((SELECT MAX(ses_DateTimeDisconnection) FROM Sessions AS SES2 WHERE SES2.ses_MAC = SES1.ses_MAC AND SES2.ses_DateTimeDisconnection < SES1.ses_DateTimeDisconnection),  DATETIME(ses_DateTimeDisconnection, "-1 hour"))
                   ELSE ses_DateTimeConnection
                 END AS ses_DateTimeConnectionCorrected,

                 CASE
                   WHEN ses_EventTypeDisconnection = "<missing event>" OR ses_EventTypeDisconnection = NULL THEN
                        (SELECT MIN(ses_DateTimeConnection) FROM Sessions AS SES2 WHERE SES2.ses_MAC = SES1.ses_MAC AND SES2.ses_DateTimeConnection > SES1.ses_DateTimeConnection)
                   ELSE ses_DateTimeDisconnection
                 END AS ses_DateTimeDisconnectionCorrected

          FROM Sessions AS SES1 
          WHERE ses_MAC="' . $mac .'"
            AND (ses_DateTimeConnectionCorrected    <= date('. $endDate .')
            AND (ses_DateTimeDisconnectionCorrected >= date('. $startDate .') OR ses_StillConnected = 1 )) ';
  $result = $db->query($SQL);

  // arrays of rows
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    // Event color
    if ($row['ses_EventTypeConnection'] == '<missing event>' || $row['ses_EventTypeDisconnection'] == '<missing event>') {
      $color = '#f39c12';
    } elseif ($row['ses_StillConnected'] == 1 ) {
      $color = '#00a659';
    } else {
      $color = '#0073b7';
    }


    // tooltip
    $tooltip = 'Connection: '    . formatEventDate ($row['ses_DateTimeConnection'],    $row['ses_EventTypeConnection'])    . chr(13) .
               'Disconnection: ' . formatEventDate ($row['ses_DateTimeDisconnection'], $row['ses_EventTypeDisconnection']) . chr(13) .
               'IP: '            . $row['ses_IP'];

    // Save row data
    $tableData[] = array(
      'title'   => '',
      'start'   => formatDateISO ($row['ses_DateTimeConnectionCorrected']),
      'end'     => formatDateISO ($row['ses_DateTimeDisconnectionCorrected']),
      'color'   => $color,
      'tooltip' => $tooltip
    );
  }

  // Control no rows
  if (empty($tableData)) {
    $tableData = '';
  }

  // Return json
  echo (json_encode($tableData));
}


//------------------------------------------------------------------------------
//  Query Presence Calendar for all Devices
//------------------------------------------------------------------------------
function getEventsCalendar() {         
  global $db;

  // Request Parameters
  $startDate  = '"'. $_REQUEST ['start'] .'"';
  $endDate    = '"'. $_REQUEST ['end'] .'"';

  // SQL 
  $SQL = 'SELECT SES1.ses_MAC, SES1.ses_EventTypeConnection, SES1.ses_DateTimeConnection,
          SES1.ses_EventTypeDisconnection, SES1.ses_DateTimeDisconnection, SES1.ses_IP,
          SES1.ses_AdditionalInfo, SES1.ses_StillConnected,
          
          CASE
            WHEN SES1.ses_EventTypeConnection = "<missing event>" THEN
              IFNULL (
                (SELECT MAX(SES2.ses_DateTimeDisconnection) 
                  FROM Sessions AS SES2 
                  WHERE SES2.ses_MAC = SES1.ses_MAC 
                    AND SES2.ses_DateTimeDisconnection < SES1.ses_DateTimeDisconnection
                    AND SES2.ses_DateTimeDisconnection BETWEEN Date('. $startDate .') AND Date('. $endDate .')
                ), 
                DATETIME(SES1.ses_DateTimeDisconnection, "-1 hour")
              )
            ELSE SES1.ses_DateTimeConnection
          END AS ses_DateTimeConnectionCorrected,

          CASE
            WHEN SES1.ses_EventTypeDisconnection = "<missing event>" THEN
              (SELECT MIN(SES2.ses_DateTimeConnection) 
                FROM Sessions AS SES2 
                WHERE SES2.ses_MAC = SES1.ses_MAC 
                  AND SES2.ses_DateTimeConnection > SES1.ses_DateTimeConnection
                  AND SES2.ses_DateTimeConnection BETWEEN Date('. $startDate .') AND Date('. $endDate .')
              )
            ELSE SES1.ses_DateTimeDisconnection
          END AS ses_DateTimeDisconnectionCorrected

        FROM Sessions AS SES1 
        WHERE (SES1.ses_DateTimeConnection BETWEEN Date('. $startDate .') AND Date('. $endDate .'))
        OR (SES1.ses_DateTimeDisconnection BETWEEN Date('. $startDate .') AND Date('. $endDate .'))
        OR SES1.ses_StillConnected = 1';

  $result = $db->query($SQL);

  // arrays of rows
  while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {
    // Event color
    if ($row['ses_EventTypeConnection'] == '<missing event>' || $row['ses_EventTypeDisconnection'] == '<missing event>') {
      $color = '#f39c12';
    } elseif ($row['ses_StillConnected'] == 1 ) {
      $color = '#00a659';
    } else {
      $color = '#0073b7';
    }

    // tooltip
    $tooltip = 'Connection: '    . formatEventDate ($row['ses_DateTimeConnection'],    $row['ses_EventTypeConnection'])    . chr(13) .
               'Disconnection: ' . formatEventDate ($row['ses_DateTimeDisconnection'], $row['ses_EventTypeDisconnection']) . chr(13) .
               'IP: '            . $row['ses_IP'];

    // Save row data
    $tableData[] = array(
      'resourceId' => $row['ses_MAC'],
      'title'      => '',
      'start'      => formatDateISO ($row['ses_DateTimeConnectionCorrected']),
      'end'        => formatDateISO ($row['ses_DateTimeDisconnectionCorrected']),
      'color'      => $color,
      'tooltip'    => $tooltip,
      'className'  => 'no-border'
    );
  }

  // Control no rows
  if (empty($tableData)) {
    $tableData = '';
  }

  // Return json
  echo (json_encode($tableData));
}

?>
