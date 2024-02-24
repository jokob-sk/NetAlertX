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

  if (isset ($_REQUEST['columnName'])) {
    $columnName = $_REQUEST['columnName'];    
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
      case 'update':    update($columnName, $id, $skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values);  break;
      case 'delete':    delete($columnName, $id, $dbtable);  break;
      default:     logServerConsole ('Action: '. $action);  break;
    }
  }


//------------------------------------------------------------------------------
//  update
//------------------------------------------------------------------------------
function update($columnName, $id, $skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values) {

  global $db;  

  // Handle one or multiple columns
  if(strpos($columns, ',') !== false) {
      $columnsArr = explode(",", $columns);
  } else {
      $columnsArr = array($columns);
  }

  // Handle one or multiple values
  if(strpos($values, ',') !== false) {
      $valuesArr = explode(",", $values);
  } else {
      $valuesArr = array($values);
  }

  // Handle one or multiple IDs
  if(strpos($id, ',') !== false) {
      $idsArr = explode(",", $id);
      $idsPlaceholder = rtrim(str_repeat('?,', count($idsArr)), ',');
  } else {
      $idsArr = array($id);
      $idsPlaceholder = '?';
  }

  // Build column-value pairs string
  $columnValues = '';
  foreach($columnsArr as $column) {
      $columnValues .= '"' . $column . '" = ?,';
  }
  // Remove trailing comma
  $columnValues = rtrim($columnValues, ',');

  // Construct the SQL query
  $sql = 'UPDATE ' . $dbtable . ' SET ' . $columnValues . ' WHERE ' . $columnName . ' IN (' . $idsPlaceholder . ')';
  
  // Prepare the statement
  $stmt = $db->prepare($sql);

  // Check for errors
  if(!$stmt) {
      echo "Error preparing statement: " . $db->lastErrorMsg();
      return;
  }

  // Bind the parameters
  $paramTypes = str_repeat('s', count($columnsArr));
  foreach($valuesArr as $i => $value) {
      $stmt->bindValue($i + 1, $value);
  }
  foreach($idsArr as $i => $idValue) {
      $stmt->bindValue(count($valuesArr) + $i + 1, $idValue);
  }

  // Execute the statement
  $result = $stmt->execute();

  $changes = $db->changes();
  if ($changes == 0) {
    // Insert new value
    create($skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values);
  }

  // update cache  
  $uniqueHash = hash('ripemd160', $dbtable . $columns);
  setCache($uniqueHash, $values, $expireMinutes);

  echo 'OK' ;  
}


//------------------------------------------------------------------------------
//  create
//------------------------------------------------------------------------------
function create($skipCache, $defaultValue, $expireMinutes, $dbtable, $columns, $values)
{
  global $db;

  echo "NOT IMPLEMENTED!\n\n";
  return;

  // // Insert new value
  // $sql = 'INSERT INTO '.$dbtable.' ('.$columns.')
  //         VALUES ("'. quotes($parameter) .'",
  //                 "'. $values     .'")';
  // $result = $db->query($sql);

  // if (! $result == TRUE) {
  //   echo "Error creating entry\n\n$sql \n\n". $db->lastErrorMsg();
  //   return;
  // }
}

//------------------------------------------------------------------------------
//  delete
//------------------------------------------------------------------------------
function delete($columnName, $id, $dbtable)
{
  global $db;

  // handle one or multiple ids
  if(strpos($id, ',') !== false) 
  {
    $idsArr = explode(",", $id);
  }else
  {
    $idsArr = array($id);
  }

  $idsStr = "";
  
  foreach ($idsArr as $item) 
  {
    $idsStr = $idsStr . '"' .$item.'"';
  }

  // Insert new value
  $sql = 'DELETE FROM '.$dbtable.' WHERE "'.$columnName.'" IN ('. $idsStr .')';
  $result = $db->query($sql);

  if (! $result == TRUE) {
    echo "Error deleting entry\n\n$sql \n\n". $db->lastErrorMsg();
    return;
  } else
  {
    echo lang('Gen_DataUpdatedUITakesTime');
    return;
  }
}


?>
