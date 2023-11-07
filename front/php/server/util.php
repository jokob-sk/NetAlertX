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
$ACTION   = "";

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
switch ($FUNCTION) {
  case 'savesettings':
      
      saveSettings();
      break;

  case 'cleanLog':      

      cleanLog($SETTINGS);
      break;

  case 'addToExecutionQueue':

      if(array_key_exists('action', $_REQUEST) != FALSE)
      {
        $ACTION = $_REQUEST['action'];
      }

      addToExecutionQueue($ACTION);
      break;

  default:
      // Handle any other cases or errors if needed
      break;
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

// Adds an action to perform into the execution_queue.log file
function addToExecutionQueue($action)
{
    global $logFolderPath, $timestamp;

    $logFile = 'execution_queue.log';
    $fullPath = $logFolderPath . $logFile;

    // Open the file or skip if it can't be opened
    if ($file = fopen($fullPath, 'a')) {
        fwrite($file, "[" . $timestamp . "]|" . $action . PHP_EOL);
        fclose($file);
        displayMessage('Action "'.$action.'" added to the execution queue.', false, true, true, true);
    } else {
        displayMessage('Log file not found or couldn\'t be created.', false, true, true, true);
    }
}


// ----------------------------------------------------------------------------------------
function cleanLog($logFile)
{  
  global $logFolderPath, $timestamp;

  $path = "";

  $allowedFiles = ['pialert.log', 'pialert_front.log', 'IP_changes.log', 'stdout.log', 'stderr.log', "pialert_pholus_lastrun.log", 'pialert.php_errors.log'];
  
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

  // save to the file
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

  $decodedSettings = json_decode($SETTINGS, true);

  foreach ($decodedSettings as $setting) { 
    if( in_array($setting[0] , $groups) == false) {
      array_push($groups ,$setting[0]);
    }
  }
  
  // go thru the groups and prepare settings to write to file
  foreach ($groups as $group) {
    $txt .= "\n\n# " . $group;
    $txt .= "\n#---------------------------\n";

    foreach ($decodedSettings as $setting) {
        $settingGroup = $setting[0];
        $settingKey = $setting[1];
        $settingType = $setting[2]; 
        $settingValue = $setting[3];

        if ($group == $settingGroup) {
            if ($settingType == 'text' || $settingType == 'password' || $settingType == 'readonly' || $settingType == 'text.select') {
                $val = encode_single_quotes($settingValue);
                $txt .= $settingKey . "='" . $val . "'\n";
            } elseif ($settingType == 'integer' || $settingType == 'integer.select') {
                $txt .= $settingKey . "=" . $settingValue . "\n";
            } elseif ($settingType == 'boolean' || $settingType == 'integer.checkbox') {

                if ($settingValue === true || $settingValue === 1 || strtolower($settingValue) === 'true') {
                    $val = "True";
                } else {
                    $val = "False";
                }

                $txt .= $settingKey . "=" . $val . "\n";
            } elseif ($settingType == 'text.multiselect' || $settingType == 'subnets' || $settingType == 'list') {
                $temp = '';
                
                if(is_array($settingValue) == FALSE)
                {
                  $settingValue =  json_decode($settingValue);
                }

                if (count($setting) > 3 && is_array($settingValue) == true) {
                    foreach ($settingValue as $val) {
                        $temp .= "'" . encode_single_quotes($val) . "',";
                    }

                    $temp = substr_replace($temp, "", -1); // remove last comma ','
                }

                $temp = '['.$temp.']'; // wrap brackets
                $txt .= $settingKey . "=" . $temp . "\n";
            } elseif ($settingType == 'json') {
                $txt .= $settingKey . "=" . $settingValue . "\n";
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
  // Create a temporary file
  $tempConfPath = $fullConfPath . ".tmp";

  // Write your changes to the temporary file
  $tempConfig = fopen($tempConfPath, "w") or die("Unable to open file!");
  fwrite($tempConfig, $txt);
  fclose($tempConfig);

  // Replace the original file with the temporary file
  rename($tempConfPath, $fullConfPath);

  displayMessage("<br/>Settings saved to the <code>pialert.conf</code> file.<br/><br/>A time-stamped backup of the previous file created. <br/><br/> Reloading...<br/>", 
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
function getSettingValue($codeName) {
  // Define the JSON endpoint URL  
  $url = dirname(__FILE__).'/../../../front/api/table_settings.json';  

  // Fetch the JSON data
  $json = file_get_contents($url);

  // Check if the JSON data was successfully fetched
  if ($json === false) {
      return 'Could not get json data';
  }

  // Decode the JSON data
  $data = json_decode($json, true);

  // Check if the JSON decoding was successful
  if (json_last_error() !== JSON_ERROR_NONE) {
    return 'Could not decode json data';
  }

  // Search for the setting by Code_Name
  foreach ($data['data'] as $setting) {
      if ($setting['Code_Name'] === $codeName) {
          return $setting['Value'];
          // echo $setting['Value'];
      }
  }

  // Return false if the setting was not found
  return 'Could not find setting '.$codeName;
}

// -------------------------------------------------------------------------------------------


function encode_single_quotes ($val) {

  $result = str_replace ('\'','{s-quote}',$val);

  return $result;
}

// -------------------------------------------------------------------------------------------

function getDateFromPeriod () {

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

  return " date('now', '".$periodDateSQL."') ";
 
  // $period = $_REQUEST['period'];    
  // return '"'. date ('Y-m-d', strtotime ('+2 day -'. $period) ) .'"';
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