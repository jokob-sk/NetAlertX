<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  parameters.php - Front module. Server side. Manage Parameters
//------------------------------------------------------------------------------
#  Puche 2022+ jokob             jokob@duck.com                GNU GPLv3
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
  $dbtable = '';
  $columns = '';
  $values  = '';
  

  if (isset ($_REQUEST['skipcache'])) {
    $skipCache = TRUE;    
  }

  if (isset ($_REQUEST['defaultValue'])) {
    $defaultValue = $_REQUEST['defaultValue'];    
  }

  if (isset ($_REQUEST['expireMinutes'])) {
    $expireMinutes = $_REQUEST['expireMinutes'];    
  }

  if (isset ($_REQUEST['key'])) {
    $key = $_REQUEST['key'];    
  }

  if (isset ($_REQUEST['id'])) {
    $id = $_REQUEST['id'];    
  }

  if (isset ($_REQUEST['values'])) {
    $values = $_REQUEST['values'];    
  }

  if (isset ($_REQUEST['columns'])) {
    $columns = $_REQUEST['columns'];    
  }

  if (isset ($_REQUEST['dbtable'])) {
    $dbtable = $_REQUEST['dbtable'];    
  }
  // TODO: Security, read, delete, edge cases
  // Action functions
  if (isset ($_REQUEST['action']) && !empty ($_REQUEST['action'])) {
    $action = $_REQUEST['action'];
    switch ($action) {
      case 'create':    create($skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values ); break;
      // case 'read'  :    read($skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values);    break;
      case 'update':    update($key, $id, $skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values);  break;
      // case 'delete':    delete($skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values);  break;
      default:     logServerConsole ('Action: '. $action);  break;
    }
  }


//------------------------------------------------------------------------------
//  update
//------------------------------------------------------------------------------
function update($key, $id, $skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values) {

  global $db;  

  if(strpos($columns, ',') !== false) 
  {
    $columnsArr = explode(",", $columns);
  }else
  {
    $columnsArr = array($columns);
  }

  if(strpos($values, ',') !== false)
  {
    $valuesArr = explode(",", $values);
  } else
  {
    $valuesArr = array($values);
  }

  $columnValues = '';

  $index = 0;
  foreach($columnsArr as $column)
  {
    $columnValues =  $columnValues .' "' .$column.'" = "'.$valuesArr[$index] . '",' ;
    $index = $index + 1;
  }
  
  $columnValues = substr($columnValues, 0, -1);  
 
  // Update value
  $sql = 'UPDATE '.$dbtable.' SET '. $columnValues .'
          WHERE "'. $key .'"="'. $id.'"';
  $result = $db->query($sql);

  if (! $result == TRUE) {
    echo "Error updating parameter\n\n$sql \n\n". $db->lastErrorMsg();
    return;
  }

  $changes = $db->changes();
  if ($changes == 0) {
    // Insert new value
    create($skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values);
  }

  // update cache  
  $uniqueHash = hash('ripemd160', $dbtable . $columns);
  setCache($uniqueHash, $values, $expireMinutes);

  echo 'OK';  
}


//------------------------------------------------------------------------------
//  create
//------------------------------------------------------------------------------
function create($skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values)
{
  global $db;

  // Insert new value
  $sql = 'INSERT INTO '.$dbtable.' ('.$columns.')
          VALUES ("'. quotes($parameter) .'",
                  "'. $values     .'")';
  $result = $db->query($sql);

  if (! $result == TRUE) {
    echo "Error creating etry\n\n$sql \n\n". $db->lastErrorMsg();
    return;
  }
}


?>
