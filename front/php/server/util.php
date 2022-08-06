<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  util.php - Front module. Server side. Common generic functions
//------------------------------------------------------------------------------
//  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
//------------------------------------------------------------------------------

// ## TimeZone processing
$config_file = "../../../config/pialert.conf";
$config_file_lines = file($config_file);
$config_file_lines_timezone = array_values(preg_grep('/^TIMEZONE\s.*/', $config_file_lines));
$timezone_line = explode("'", $config_file_lines_timezone[0]);
$Pia_TimeZone = $timezone_line[1];
date_default_timezone_set($Pia_TimeZone);

//------------------------------------------------------------------------------
// Formatting data functions
//------------------------------------------------------------------------------
function formatDate ($date1) {
  return date_format (new DateTime ($date1) , 'Y-m-d   H:i');
}

function formatDateDiff ($date1, $date2) {
  return date_diff (new DateTime ($date1), new DateTime ($date2 ) )-> format ('%ad   %H:%I');
}

function formatDateISO ($date1) {
  return date_format (new DateTime ($date1),'c');
}

function formatEventDate ($date1, $eventType) {
  if (!empty ($date1) ) {
    $ret = formatDate ($date1);
  } elseif ($eventType == '<missing event>') {
    $ret = '<missing event>';
  } else {
    $ret = '<Still Connected>';
  }

  return $ret;
}

function formatIPlong ($IP) {
  return sprintf('%u', ip2long($IP) );
}


//------------------------------------------------------------------------------
// Others functions
//------------------------------------------------------------------------------
function getDateFromPeriod () {
  $period = $_REQUEST['period'];    
  return '"'. date ('Y-m-d', strtotime ('+1 day -'. $period) ) .'"';
}

function quotes ($text) {
  return str_replace ('"','""',$text);
}
    
function logServerConsole ($text) {
  $x = array();
  $y = $x['__________'. $text .'__________'];
}

function getNetworkTypes(){

  $array = array(
    "AP", "Gateway", "Powerline", "Switch", "WLAN", "PLC", "Router","USB LAN Adapter", "USB WIFI Adapter"
  );

  return $array;
}

function getDevicesColumns(){

  $columns = ["dev_MAC", 
              "dev_Name",
              "dev_Owner",
              "dev_DeviceType",
              "dev_Vendor",
              "dev_Favorite",
              "dev_Group",
              "dev_Comments", 
              "dev_FirstConnection",
              "dev_LastConnection",
              "dev_LastIP",
              "dev_StaticIP",
              "dev_ScanCycle",
              "dev_LogEvents",
              "dev_AlertEvents",
              "dev_AlertDeviceDown",
              "dev_SkipRepeated",
              "dev_LastNotification",
              "dev_PresentLastScan",
              "dev_NewDevice",
              "dev_Location",
              "dev_Archived",
              "dev_Network_Node_port",
              "dev_Network_Node_MAC_ADDR"]; 
              
  return $columns;
}

//------------------------------------------------------------------------------
//  Simple cookie cache
//------------------------------------------------------------------------------
function getCache($key) {
  if( isset($_COOKIE[$key]))
  {
    return $_COOKIE[$key];
  }else
  {
    return "";
  }
}

function setCache($key, $value) {
  setcookie($key,  $value, time()+300, "/","", 0); // 5min cache
}



?>
