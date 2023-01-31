<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  parameters.php - Front module. Server side. Manage Parameters
//------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------


//------------------------------------------------------------------------------
  // External files
  require dirname(__FILE__).'/init.php';
 

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
  // Set maximum execution time to 15 seconds
  ini_set ('max_execution_time','15');

  $skipCache = FALSE;
  $expireMinutes = 5;
  $defaultValue = '';
  

  if (isset ($_REQUEST['skipcache'])) {
    $skipCache = TRUE;    
  }

  if (isset ($_REQUEST['defaultValue'])) {
    $defaultValue = $_REQUEST['defaultValue'];    
  }

  if (isset ($_REQUEST['expireMinutes'])) {
    $expireMinutes = $_REQUEST['expireMinutes'];    
  }

  // Action functions
  if (isset ($_REQUEST['action']) && !empty ($_REQUEST['action'])) {
    $action = $_REQUEST['action'];
    switch ($action) {
      case 'get':  getParameter($skipCache, $defaultValue, $expireMinutes); break;
      case 'set':  setParameter($expireMinutes);                          break;
      default:     logServerConsole ('Action: '. $action);  break;
    }
  }


//------------------------------------------------------------------------------
//  Get Parameter Value
//------------------------------------------------------------------------------
function getParameter($skipCache, $defaultValue, $expireMinutes) {

  $parameter = $_REQUEST['parameter'];
  $value = "";

  // get the value from the cache if available
  $cachedValue = getCache($parameter);
  if($cachedValue != "")
  {
    $value  = $cachedValue;
  }

  // query the database if no cache entry found or requesting live data (skipping cache)
  if($skipCache || $value == "" )
  {
    global $db;
    
    $sql = 'SELECT par_Value FROM Parameters
            WHERE par_ID="'. quotes($parameter) .'"';
    
    $result = $db->query($sql);
    $row = $result -> fetchArray (SQLITE3_NUM);  

    if($row != NULL && count($row) == 1)
    {
      $value = $row[0];
    } else{
      $value = $defaultValue;

      // Nothing found in the DB, Insert new value
      insertNew($parameter, $value);
    }

    // update cache  
    setCache($parameter, $value, $expireMinutes);
  }
  // return value
  echo (json_encode ($value));  
}


//------------------------------------------------------------------------------
//  Set Parameter Value
//------------------------------------------------------------------------------
function setParameter($expireMinutes) {

  $parameter = $_REQUEST['parameter'];
  $value = $_REQUEST['value'];  
    
  global $db;
 
  // Update value
  $sql = 'UPDATE Parameters SET par_Value="'. quotes ($value) .'"
          WHERE par_ID="'. quotes($parameter) .'"';
  $result = $db->query($sql);

  if (! $result == TRUE) {
    echo "Error updating parameter\n\n$sql \n\n". $db->lastErrorMsg();
    return;
  }

  $changes = $db->changes();
  if ($changes == 0) {
    // Insert new value
    insertNew($parameter, $value);
  }

  // update cache  
  setCache($parameter, $value, $expireMinutes);

  echo 'OK';
}

function insertNew($parameter, $value)
{
  global $db;

  // Insert new value
  $sql = 'INSERT INTO Parameters (par_ID, par_Value)
          VALUES ("'. quotes($parameter) .'",
                  "'. quotes($value)     .'")';
  $result = $db->query($sql);

  if (! $result == TRUE) {
    echo "Error creating parameter\n\n$sql \n\n". $db->lastErrorMsg();
    return;
  }
}


?>
