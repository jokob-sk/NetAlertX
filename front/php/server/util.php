<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  util.php - Front module. Server side. Common generic functions
//------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------

require dirname(__FILE__).'/../templates/timezone.php';
require dirname(__FILE__).'/../templates/skinUI.php';

$FUNCTION = [];
$SETTINGS = [];

// init request params
if(array_key_exists('function', $_REQUEST) != FALSE)
{  
  $FUNCTION = $_REQUEST['function']; 
}

if(array_key_exists('settings', $_REQUEST) != FALSE)
{
  $SETTINGS = $_REQUEST['settings'];
}

// call functions based on requested params
if ($FUNCTION  == 'savesettings') 
{
  saveSettings();
} 
elseif ($FUNCTION  == 'cleanLog')
{
  cleanLog($SETTINGS);
}

//------------------------------------------------------------------------------
// Formatting data functions
//------------------------------------------------------------------------------
// Creates a PHP array from a string representing a python array (input format ['...','...'])
// Only supports:
//      - one level arrays, not nested ones
//      - single quotes 
function createArray($input){

  // empty array
  if($input == '[]')
  {
    return [];
  }

  // regex patterns
  $patternBrackets = '/(^\s*\[)|(\]\s*$)/';
  $patternQuotes = '/(^\s*\')|(\'\s*$)/';
  $replacement = '';

  // remove brackets
  $noBrackets = preg_replace($patternBrackets, $replacement, $input); 
  
  $options = array(); 

  // create array
  $optionsTmp = explode(",", $noBrackets);

  // handle only one item in array
  if(count($optionsTmp) == 0)
  {
    return [preg_replace($patternQuotes, $replacement, $noBrackets)];
  }

  // remove quotes
  foreach ($optionsTmp as $item)
  {
    array_push($options, preg_replace($patternQuotes, $replacement, $item) );
  }
  
  return $options;
}

// -------------------------------------------------------------------------------------------
// For debugging - Print arrays
function printArray ($array) {
  echo '[';
  foreach ($array as $val)
  {
    if(is_array($val))
    {
      echo '<br/>';
      printArray($val);
    } else
    {
      echo $val.', ';
    }
  }  
  echo ']<br/>';
}

// -------------------------------------------------------------------------------------------
function formatDate ($date1) {
  return date_format (new DateTime ($date1) , 'Y-m-d   H:i');
}

// -------------------------------------------------------------------------------------------
function formatDateDiff ($date1, $date2) {
  return date_diff (new DateTime ($date1), new DateTime ($date2 ) )-> format ('%ad   %H:%I');
}

// -------------------------------------------------------------------------------------------
function formatDateISO ($date1) {
  return date_format (new DateTime ($date1),'c');
}

// -------------------------------------------------------------------------------------------
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

// -------------------------------------------------------------------------------------------
function formatIPlong ($IP) {
  return sprintf('%u', ip2long($IP) );
}


//------------------------------------------------------------------------------
// Other functions
//------------------------------------------------------------------------------
function checkPermissions($files)
{
  foreach ($files as $file)
  {
    // check access to database
    if(file_exists($file) != 1)
    {
      $message = "File '".$file."' not found or inaccessible. Correct file permissions, create one yourself or generate a new one in 'Settings' by clicking the 'Save' button.";
      displayMessage($message, TRUE);      
    }
  } 
}

// ----------------------------------------------------------------------------------------

function displayMessage($message, $logAlert = FALSE, $logConsole = TRUE, $logFile = TRUE, $logEcho = FALSE)
{
  global $logFolderPath, $log_file, $timestamp;

  // sanitize
  $message = str_replace(array("\n", "\r", PHP_EOL), '', $message);

  echo "<script>function escape(html, encode) {
    return html.replace(!encode ? /&(?!#?\w+;)/g : /&/g, '&amp;')  
      .replace(/\t/g, '')    
  }</script>";

  // Javascript Alert pop-up
  if($logAlert)
  {
    echo '<script>alert(escape("'.$message.'"));</script>';
  }

  // F12 Browser console
  if($logConsole)
  {
    echo '<script>console.log(escape("'.str_replace('"',"'",$message).'"));</script>';
  }

  //File
  if($logFile)
  {
    if(file_exists($logFolderPath.$log_file) != 1) // file doesn't exist, create one
    {
      $log = fopen($logFolderPath.$log_file, "w") or die("Unable to open file!");
    }else // file exists, append
    {
      $log = fopen($logFolderPath.$log_file, "a") or die("Unable to open file!");
    }

    fwrite($log, "[".$timestamp. "] " . str_replace('<br>',"\n   ",str_replace('<br/>',"\n   ",$message)).PHP_EOL."" );
    fclose($log);
  }

  //echo
  if($logEcho)
  {
    echo $message;
  }

}

// ----------------------------------------------------------------------------------------
function cleanLog($logFile)
{  
  global $logFolderPath, $timestamp;

  $path = "";

  $allowedFiles = ['pialert.log', 'pialert_front.log', 'IP_changes.log', 'stdout.log', 'stderr.log', "pialert_pholus.log", "pialert_pholus_lastrun.log"];
  
  if(in_array($logFile, $allowedFiles))
  {
    $path = $logFolderPath.$logFile;
  }

  if($path != "")
  {
    // purge content
    $file = fopen($path, "w") or die("Unable to open file!");
    fwrite($file, "[".$timestamp. "] Log file manually purged" .PHP_EOL."");
    fclose($file);
    displayMessage('File <code>'.$logFile.'</code> purged.', FALSE, TRUE, TRUE, TRUE);      
  } else
  {
    displayMessage('File <code>'.$logFile.'</code> is not allowed to be purged.', FALSE, TRUE, TRUE, TRUE);      
  } 
}



// ----------------------------------------------------------------------------------------
function saveSettings()
{
  global $SETTINGS, $FUNCTION, $config_file, $fullConfPath, $configFolderPath, $timestamp;   

  // save in the file
  $new_name = $config_file.'_'.$timestamp.'.backup';
  $new_location = $configFolderPath.$new_name;

  if(file_exists( $fullConfPath) != 1)
  {    
    displayMessage('File "'.$fullConfPath.'" not found or missing read permissions. Creating a new <code>'.$config_file.'</code> file.', FALSE, TRUE, TRUE, TRUE);      
  }
  // create a backup copy    
  elseif (!copy($fullConfPath, $new_location))
  {      
    displayMessage("Failed to copy file ".$fullConfPath." to ".$new_location." <br/> Check your permissions to allow read/write access to the /config folder.", FALSE, TRUE, TRUE, TRUE);      
  }
  
       
  // generate a clean pialert.conf file
  $groups = [];

  $txt = "";

  $txt = $txt."#-----------------AUTOGENERATED FILE-----------------#\n";
  $txt = $txt."#                                                    #\n";
  $txt = $txt."#         Generated:  ".$timestamp."            #\n";
  $txt = $txt."#                                                    #\n";
  $txt = $txt."#   Config file for the LAN intruder detection app:  #\n";
  $txt = $txt."#      https://github.com/jokob-sk/Pi.Alert          #\n";
  $txt = $txt."#                                                    #\n";
  $txt = $txt."#-----------------AUTOGENERATED FILE-----------------#\n";

  // collect all groups
  foreach ($SETTINGS as $setting) { 
    if( in_array($setting[0] , $groups) == false) {
      array_push($groups ,$setting[0]);
    }
  }

  // go thru the groups and prepare settings to write to file
  foreach($groups as $group)
  {
    $txt = $txt."\n\n# ".$group;
    $txt = $txt."\n#---------------------------\n" ;
    foreach($SETTINGS as $setting)
    {
      if($group == $setting[0])
      {            
        if($setting[2] == 'text' or $setting[2] == 'password' or $setting[2] == 'readonly' or $setting[2] == 'selecttext')
        {
          $val = encode_single_quotes($setting[3]);
          $txt = $txt.$setting[1]."='".$val."'\n" ; 
        } elseif($setting[2] == 'integer' or $setting[2] == 'selectinteger')
        {
          $txt = $txt.$setting[1]."=".$setting[3]."\n" ; 
        } elseif($setting[2] == 'boolean')
        {
          $val = "False";
          if($setting[3] == 'true')
          {
            $val = "True";
          }
          $txt = $txt.$setting[1]."=".$val."\n" ; 
        }elseif($setting[2] == 'multiselect' or $setting[2] == 'subnets' or $setting[2] == 'list')
        {
          $temp = '[';         
          
          if (count($setting) > 3 && is_array( $setting[3]) == True){
            foreach($setting[3] as $val)
            {
              $temp = $temp."'". encode_single_quotes($val)."',";
            }

            $temp = substr_replace($temp, "", -1); // remove last comma ','
          }

          $temp = $temp.']';  // close brackets 
          $txt = $txt.$setting[1]."=".$temp."\n" ; 
        }            
      }
    }
  }

  $txt = $txt."\n\n";
  $txt = $txt."#-------------------IMPORTANT INFO-------------------#\n";
  $txt = $txt."#   This file is ingested by a python script, so if  #\n";      
  $txt = $txt."#        modified it needs to use python syntax      #\n";      
  $txt = $txt."#-------------------IMPORTANT INFO-------------------#\n";

  // open new file and write the new configuration      
  $newConfig = fopen($fullConfPath, "w") or die("Unable to open file!");
  fwrite($newConfig, $txt);
  fclose($newConfig);

  displayMessage("<br/>Settings saved to the <code>".$config_file."</code> file.  
    <br/><br/>Backup of the previous ".$config_file." created here: <br/><br/><code>".$new_name."</code><br/><br/>
    <b>Note:</b> Wait at least <b>5s</b> for the changes to reflect in the UI. (longer if for example a <a href='#state'>Scan is running</a>)", 
    FALSE, TRUE, TRUE, TRUE);    

}

// -------------------------------------------------------------------------------------------
function getString ($codeName, $default) {

  $result = lang($codeName);

  if ($result )
  {
    return $result;
  }   

  return $default;
}

// -------------------------------------------------------------------------------------------


function encode_single_quotes ($val) {

  $result = str_replace ('\'','{s-quote}',$val);

  return $result;
}

// -------------------------------------------------------------------------------------------

function getDateFromPeriod () {
  $period = $_REQUEST['period'];    
  return '"'. date ('Y-m-d', strtotime ('+1 day -'. $period) ) .'"';
}

// -------------------------------------------------------------------------------------------
function quotes ($text) {
  return str_replace ('"','""',$text);
}
    
// -------------------------------------------------------------------------------------------
function logServerConsole ($text) {
  $x = array();
  $y = $x['__________'. $text .'__________'];
}
    
// -------------------------------------------------------------------------------------------
function handleNull ($text, $default = "") {
  if($text == NULL || $text == 'NULL')
  {
    return $default;
  } else
  {
    return $text;
  }
  
}

// -------------------------------------------------------------------------------------------

function getNetworkTypes(){

  $array = array(
    "AP", "Gateway", "Firewall", "Powerline", "Switch", "WLAN", "PLC", "Router","USB LAN Adapter", "USB WIFI Adapter"
  );

  return $array;
}

// -------------------------------------------------------------------------------------------
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
              "dev_Network_Node_MAC_ADDR",
              "dev_Icon"]; 
              
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
// -------------------------------------------------------------------------------------------
function setCache($key, $value, $expireMinutes = 5) {
  setcookie($key,  $value, time()+$expireMinutes*60, "/","", 0); 
}


?>