<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  parameters.php - Front module. Server side. Manage Parameters
//------------------------------------------------------------------------------
//  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
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
  
  // Open DB
  OpenDB();

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
  global $db;

  $parameter = $_REQUEST['parameter'];
  $sql = 'SELECT par_Value FROM Parameters
          WHERE par_ID="'. quotes($_REQUEST['parameter']) .'"';
  $result = $db->query($sql);
  $row = $result -> fetchArray (SQLITE3_NUM);
  $value = $row[0];

  echo (json_encode ($value));
}


//------------------------------------------------------------------------------
//  Set Parameter Value
//------------------------------------------------------------------------------
function setParameter() {
  global $db;
 
  // Update value
  $sql = 'UPDATE Parameters SET par_Value="'. quotes ($_REQUEST['value']) .'"
          WHERE par_ID="'. quotes($_REQUEST['parameter']) .'"';
  $result = $db->query($sql);

  if (! $result == TRUE) {
    echo "Error updating parameter\n\n$sql \n\n". $db->lastErrorMsg();
    return;
  }

  $changes = $db->changes();
  if ($changes == 0) {
    // Insert new value
    $sql = 'INSERT INTO Parameters (par_ID, par_Value)
            VALUES ("'. quotes($_REQUEST['parameter']) .'",
                    "'. quotes($_REQUEST['value'])     .'")';
    $result = $db->query($sql);

    if (! $result == TRUE) {
      echo "Error creating parameter\n\n$sql \n\n". $db->lastErrorMsg();
      return;
    }
  }

  echo 'OK';
}

?>
