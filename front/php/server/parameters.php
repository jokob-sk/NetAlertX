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
  require 'db.php';
  require 'util.php';
 

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
  // Set maximum execution time to 15 seconds
  ini_set ('max_execution_time','15');

  // Action functions
  if (isset ($_REQUEST['action']) && !empty ($_REQUEST['action'])) {
    $action = $_REQUEST['action'];
    switch ($action) {
      case 'get':  getParameter();                          break;
      case 'set':  setParameter();                          break;
      default:     logServerConsole ('Action: '. $action);  break;
    }
  }


//------------------------------------------------------------------------------
//  Get Parameter Value
//------------------------------------------------------------------------------
function getParameter() {

  $parameter = $_REQUEST['parameter'];
  $value = "";

  // get the value from the cookie if available
  if(getCache($parameter) != "")
  {
    $value  = getCache($parameter);
  }

  // query the database if no cache entry found or requesting live data for the Back_App_State in the header
  if($parameter == "Back_App_State" || $value == "" )
  {
    // Open DB
    OpenDB();

    global $db;
    
    $sql = 'SELECT par_Value FROM Parameters
            WHERE par_ID="'. quotes($parameter) .'"';
    
    $result = $db->query($sql);
    $row = $result -> fetchArray (SQLITE3_NUM);  
    $value = $row[0];

    // Close DB
    $db->close();

    // update cookie cache  
    setCache($parameter, $value);
  }
  // return value
  echo (json_encode ($value));  
}


//------------------------------------------------------------------------------
//  Set Parameter Value
//------------------------------------------------------------------------------
function setParameter() {

  $parameter = $_REQUEST['parameter'];
  $value = $_REQUEST['value'];

  // Open DB
  OpenDB();
    
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
    $sql = 'INSERT INTO Parameters (par_ID, par_Value)
            VALUES ("'. quotes($parameter) .'",
                    "'. quotes($value)     .'")';
    $result = $db->query($sql);

    if (! $result == TRUE) {
      echo "Error creating parameter\n\n$sql \n\n". $db->lastErrorMsg();
      return;
    }
  }

  // Close DB
  $db->close();  

  // update cookie cache  
  setCache($parameter, $value);

  echo 'OK';
}

?>
