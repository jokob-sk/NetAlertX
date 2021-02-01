<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  db.php - Front module. Server side. DB common file
//------------------------------------------------------------------------------
//  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
//------------------------------------------------------------------------------


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
      sleep(3);
      return SQLite3_connect(false);
    }
  }
}


//------------------------------------------------------------------------------
// Open DB
//------------------------------------------------------------------------------
function OpenDB () {
  global $DBFILE;
  global $db;

  if(strlen($DBFILE) == 0)
  {
    die ('Database no available');
  }

  $db = SQLite3_connect(true);
  if(!$db)
  {
    die ('Error connecting to database');
  }
}
   
?>
