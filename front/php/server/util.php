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

$FUNCTION = $_REQUEST['function'];


if ($FUNCTION  == 'savesettings') {
  saveSettings();
} elseif ($PIA_SCAN_MODE == 'test') {
    // other function
}

//------------------------------------------------------------------------------
// Formatting data functions
//------------------------------------------------------------------------------
function createArray($input){
  $pattern = '/(^\s*\[)|(\]\s*$)/';
  $replacement = '';
  $noBrackets = preg_replace($pattern, $replacement, $input); 
  
  return $options = explode(",", $noBrackets);
}

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
function checkPermissions($files)
{
  foreach ($files as $file)
  {
    // check access to database
    if(file_exists($file) != 1)
    {
      displayMessage("File ".$file." not found or inaccessible. Grant read & write permissions to the file to the correct user.");
    }
  }
 
}


function displayMessage($message)
{
  echo '<script>alert("'.$message.'")</script>';
}


function saveSettings()
{
  $config_file = "../../../config/pialert.conf";
  // save in the file
  $new_location = $config_file.'_'.strtotime("now").'.backup';

  if(file_exists( $config_file) == 1)
  {
    // create a backup copy    
    if (!copy($config_file, $new_location))
    {      
      echo "Failed to copy file ".$config_file." to ".$new_location." <br/> Check your permissions to allow read/write access to the /config folder.";
    }
    {
      echo "Backup of pialert.conf created: <code>".$new_location."</code>";
    }
  } else {
    echo 'File "'.$config_file.'" not found or missing read permissions.';
  }

  // save in the DB
}

function getString ($codeName, $default, $pia_lang) {

  $result = $pia_lang[$codeName];

  if ($result )
  {
    return $result;
  }   

  return $default;
}

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
