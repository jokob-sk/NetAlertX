<?php
//------------------------------------------------------------------------------
//  NetAlertX
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  util.php - Front module. Server side. Common generic functions
//------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------

require dirname(__FILE__).'/../templates/globals.php';
require dirname(__FILE__).'/../templates/skinUI.php';

//------------------------------------------------------------------------------
// check if authenticated
require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

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

    // // make sure the file ownership is correct
    // chown($file, 'nginx');
    // chgrp($file, 'www-data');

    // check access to database
    if(file_exists($file) != 1)
    {
      $message = "File '".$file."' not found or inaccessible. Correct file permissions, create one yourself or generate a new one in 'Settings' by clicking the 'Save' button.";
      displayMessage($message, TRUE);      
    }
  } 
}

// ----------------------------------------------------------------------------------------
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /messaging/in-app/write
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
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

  // F12 Browser dev console
  if($logConsole)
  {
    echo '<script>console.log(escape("'.str_replace('"',"'",$message).'"));</script>';
  }

  //File
  if($logFile)
  {

    if (is_writable($logFolderPath.$log_file)) {
        

        if(file_exists($logFolderPath.$log_file) != 1) // file doesn't exist, create one
        {
          $log = fopen($logFolderPath.$log_file, "w") or die("Unable to open file!");
        }else // file exists, append
        {
          $log = fopen($logFolderPath.$log_file, "a") or die("Unable to open file - Permissions issue!");
        }
    
        fwrite($log, "[".$timestamp. "] " . str_replace('<br>',"\n   ",str_replace('<br/>',"\n   ",$message)).PHP_EOL."" );
        fclose($log);

    } else {
        echo 'The file is not writable: '.$logFolderPath.$log_file;
    }


  }

  //echo
  if($logEcho)
  {
    echo $message;
  }

}

// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /logs/add-to-execution-queue
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// ----------------------------------------------------------------------------------------
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
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /logs DELETE
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
function cleanLog($logFile)
{  
  global $logFolderPath, $timestamp;

  $path = "";

  $allowedFiles = ['app.log', 'app_front.log', 'IP_changes.log', 'stdout.log', 'stderr.log', 'app.php_errors.log', 'execution_queue.log', 'db_is_locked.log'];
  
  if(in_array($logFile, $allowedFiles))
  {
    $path = $logFolderPath.$logFile;
  }

  if($path != "")
  {
    // purge content
    $file = fopen($path, "w") or die("Unable to open file!");
    fwrite($file, "");
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
  
       
  // generate a clean .conf file
  $groups = [];

  $txt = "";

  $txt = $txt."#-----------------AUTOGENERATED FILE-----------------#\n";
  $txt = $txt."#                                                    #\n";
  $txt = $txt."#         Generated:  ".$timestamp."            #\n";
  $txt = $txt."#                                                    #\n";
  $txt = $txt."#   Config file for the LAN intruder detection app:  #\n";
  $txt = $txt."#      https://github.com/jokob-sk/NetAlertX         #\n";
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
      $setKey   = $setting[1];
      $dataType     = $setting[2]; 
      $settingValue = $setting[3];
  
      // // Parse the settingType JSON
      // $settingType = json_decode($settingTypeJson, true);
  
      // Sanity check
      if($setKey == "UI_LANG" && $settingValue == "") {
          echo "🔴 Error: important settings missing. Refresh the page with 🔃 on the top and try again.";
          return;
      }
  
      if ($group == $settingGroup) {          
  
          if ($dataType == 'string' ) {
              $val = encode_single_quotes($settingValue);
              $txt .= $setKey . "='" . $val . "'\n";
          } elseif ($dataType == 'integer') {
              $txt .= $setKey . "=" . $settingValue . "\n";
          } elseif ($dataType == 'none') {
              $txt .= $setKey . "=''\n";
          } elseif ($dataType == 'json') {
              $txt .= $setKey . "=" . $settingValue . "\n";
          } elseif ($dataType == 'boolean') {
              $val = ($settingValue === true || $settingValue === 1 || strtolower($settingValue) === 'true') ? "True" : "False";
              $txt .= $setKey . "=" . $val . "\n";
          } elseif ($dataType == 'array' ) {
              $temp = '';
              
              if(is_array($settingValue) == FALSE)
              {
                $settingValue =  json_decode($settingValue);
              }
              // skipping __metadata entries (?)
              if (count($setting) > 3 && is_array($settingValue) == true) {
                  foreach ($settingValue as $val) {
                      $temp .= "'" . encode_single_quotes($val) . "',";
                  }

                  $temp = substr_replace($temp, "", -1); // remove last comma ','
              }

              $temp = '['.$temp.']'; // wrap brackets
              $txt .= $setKey . "=" . $temp . "\n";
 
          } else  {
              $txt .= $setKey . "='⭕Not handled⭕'\n";
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

  // Backup the original file
  if (file_exists($fullConfPath)) {
    copy($fullConfPath, $fullConfPath . ".bak");
  }

  // Open the file for writing without changing permissions
  $file = fopen($fullConfPath, "w") or die("Unable to open file!");
  fwrite($file, $txt);
  fclose($file);

  // displayMessage(lang('settings_saved'), 
  //   FALSE, TRUE, TRUE, TRUE);    

  echo "OK";

}

// -------------------------------------------------------------------------------------------
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /graphql LangStrings endpoint
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
function getString ($setKey, $default) {

  $result = lang($setKey);

  if ($result )
  {
    return $result;
  }   

  return $default;
}
// -------------------------------------------------------------------------------------------
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /settings/<key>
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
function getSettingValue($setKey) {
  // Define the JSON endpoint URL  
  $url = dirname(__FILE__).'/../../../api/table_settings.json';  

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

  // Search for the setting by setKey
  foreach ($data['data'] as $setting) {
      if ($setting['setKey'] === $setKey) {
          return $setting['setValue'];
          // echo $setting['setValue'];
      }
  }

  // Return false if the setting was not found
  return 'Could not find setting '.$setKey;
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
// Encode special chars
function encodeSpecialChars($str) {
  return str_replace(
      ['&', '<', '>', '"', "'"],
      ['&amp;', '&lt;', '&gt;', '&quot;', '&#039;'],
      $str
  );
}

// -------------------------------------------------------------------------------------------
// Decode special chars
function decodeSpecialChars($str) {
  return str_replace(
      ['&amp;', '&lt;', '&gt;', '&quot;', '&#039;'],
      ['&', '<', '>', '"', "'"],
      $str
  );
}


// -------------------------------------------------------------------------------------------
// used in Export CSV
function getDevicesColumns(){

  $columns = ["devMac", 
              "devName",
              "devOwner",
              "devType",
              "devVendor",
              "devFavorite",
              "devGroup",
              "devComments", 
              "devFirstConnection",
              "devLastConnection",
              "devLastIP",
              "devStaticIP",
              "devScan",
              "devLogEvents",
              "devAlertEvents",
              "devAlertDown",
              "devSkipRepeated",
              "devLastNotification",
              "devPresentLastScan",
              "devIsNew",
              "devLocation",
              "devIsArchived",
              "devParentPort",
              "devParentMAC",
              "devIcon",
              "devGUID",
              "devSyncHubNode",
              "devSite",
              "devSSID",
              "devSourcePlugin",
              "devCustomProps",
              "devFQDN",
              "devParentRelType",
              "devReqNicsOnline"
            ]; 
              
  return $columns;
}


function generateGUID() {
  return sprintf(
      '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
      random_int(0, 0xffff), random_int(0, 0xffff),
      random_int(0, 0xffff),
      random_int(0, 0x0fff) | 0x4000, // Version 4 UUID
      random_int(0, 0x3fff) | 0x8000, // Variant 1
      random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff)
  );
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