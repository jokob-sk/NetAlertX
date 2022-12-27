<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  db.php - Front module. Server side. DB common file
//------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------

// ## TimeZone processing
$configFolderPath = "/home/pi/pialert/config/";
$config_file = "pialert.conf";
$logFolderPath = "/home/pi/pialert/front/log/";
$log_file = "pialert_front.log";


$fullConfPath = $configFolderPath.$config_file;

$config_file_lines = file($fullConfPath);
$config_file_lines_timezone = array_values(preg_grep('/^TIMEZONE\s.*/', $config_file_lines));

$timeZone = "";

foreach ($config_file_lines as $line)
{    
  if( preg_match('/TIMEZONE(.*?)/', $line, $match) == 1 )
  {        
      if (preg_match('/\'(.*?)\'/', $line, $match) == 1) {          
        $timeZone = $match[1];
      }
  }
}

if($timeZone == "")
{
  $timeZone = "Europe/Berlin";
}

date_default_timezone_set($timeZone);

$date = new DateTime("now", new DateTimeZone($timeZone) );
$timestamp = $date->format('Y-m-d_H-i-s');

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