<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  db.php - Front module. Server side. DB common file
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
// DB File Path
$DBFILE = '../../../db/pialert.db';

//------------------------------------------------------------------------------
// Connect DB
//------------------------------------------------------------------------------
function SQLite3_connect ($trytoreconnect) {
  global $DBFILE;
  try
  {
    // connect to database
    // return new SQLite3($DBFILE, SQLITE3_OPEN_READONLY);
    return new SQLite3($DBFILE, SQLITE3_OPEN_READWRITE);
  }
  catch (Exception $exception)
  {
    // sqlite3 throws an exception when it is unable to connect
    // try to reconnect one time after 3 seconds
    
    if($trytoreconnect)
    {
      echo '<script>alert("Error connecting to database, will try in 3s")</script>';
      sleep(3);      
      return SQLite3_connect(false);
    }
  }
}


//------------------------------------------------------------------------------
// Open DB
//------------------------------------------------------------------------------

function OpenDB (...$DBPath) {
  global $DBFILE;
  global $db;

  // use custom path if supplied
  foreach ($DBPath as $path) {  
    $DBFILE = $path;  
  }  
  
  if(strlen($DBFILE) == 0)
  {
    echo '<script>alert("Database not available")</script>';
    die ('<div style="padding-left:150px">Database not available</div>');
  }

  $db = SQLite3_connect(true);
  
  if(!$db)
  {
    echo '<script>alert("Error connecting to the database")</script>';
    die ('<div style="padding-left:150px">Error connecting to the database</div>');
  }

  $db->exec('PRAGMA journal_mode = wal;');
}
   
?>