<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  db.php - Front module. Server side. DB common file
//------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// DB File Path
$DBFILE = dirname(__FILE__).'/../../../db/pialert.db';

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


// # Open DB once and keep open
// # Opening / closing DB frequently actually casues more issues
OpenDB (); // main
