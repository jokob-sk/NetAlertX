<?php
//------------------------------------------------------------------------------
//  NetAlertX
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  db.php - Front module. Server side. DB common file
//------------------------------------------------------------------------------
#   2022 jokob             jokob@duck.com                GNU GPLv3
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// DB File Path
$DBFILE = dirname(__FILE__).'/../../../db/app.db';
$DBFILE_LOCKED_FILE = dirname(__FILE__).'/../../../logs/db_is_locked.log';

$db_locked = false;

//------------------------------------------------------------------------------
// Connect DB
//------------------------------------------------------------------------------
function SQLite3_connect ($trytoreconnect, $retryCount = 0) {
  global $DBFILE, $DBFILE_LOCKED_FILE;
  $maxRetries = 5; // Maximum number of retries
  $baseDelay = 1; // Base delay in seconds


  try {
    // Connect to database
    global $db_locked;
    $db_locked = false;

    // Write unlock status to the locked file
    file_put_contents($DBFILE_LOCKED_FILE, '0');

    return new SQLite3($DBFILE, SQLITE3_OPEN_READWRITE);
  } catch (Exception $exception) {
    // sqlite3 throws an exception when it is unable to connect
    global $db_locked;
    $db_locked = true;

    // Write lock status to the locked file
    file_put_contents($DBFILE_LOCKED_FILE, '1');

    // Connection failed, check if we should retry
    if ($trytoreconnect && $retryCount < $maxRetries) {
      // Calculate exponential backoff delay
      $delay = $baseDelay * pow(2, $retryCount);
      sleep($delay);

      // Retry the connection with an increased retry count
      return SQLite3_connect(true, $retryCount + 1);
    } else {
      // Maximum retries reached, hide loading spinner and show failure alert
      echo '<script>alert("Failed to connect to database after ' . $retryCount . ' retries.")</script>';
      return false; // Or handle the failure appropriately
    }
  }
}


//------------------------------------------------------------------------------
// ->query override to handle retries 
//------------------------------------------------------------------------------
class CustomDatabaseWrapper {
  private $sqlite;
  private $maxRetries;
  private $retryDelay;
  

  public function __construct($filename, $flags = SQLITE3_OPEN_READWRITE | SQLITE3_OPEN_CREATE, $maxRetries = 3, $retryDelay = 1000, $encryptionKey = null) {
      $this->sqlite = new SQLite3($filename, $flags, $encryptionKey);

      $this->maxRetries = $maxRetries;
      $this->retryDelay = $retryDelay;
  }

  public function query(string $query): SQLite3Result|bool {
      global $DBFILE_LOCKED_FILE;

      $attempts = 0;
      while ($attempts < $this->maxRetries) {
          $result = $this->sqlite->query($query);
          if ($result !== false) {
              // Write unlock status to the locked file
              file_put_contents($DBFILE_LOCKED_FILE, '0');
              return $result;
          }

          // Write lock status to the locked file
          file_put_contents($DBFILE_LOCKED_FILE, '1');

          $attempts++;
          usleep($this->retryDelay * 1000); // Retry delay in milliseconds
      }

      // If all retries failed, throw an exception or handle the error as needed
      echo '<script>alert("Error executing query (attempts: ' . $attempts . '"), query: '.$query.'</script>';
      throw new Exception("Query failed after {$this->maxRetries} attempts: " . $this->sqlite->lastErrorMsg());
  }

  // Delegate other SQLite3 methods to the $sqlite instance
  public function __call($name, $arguments) {
      return call_user_func_array([$this->sqlite, $name], $arguments);
  }
}


//------------------------------------------------------------------------------
// Open DB
//------------------------------------------------------------------------------

function OpenDB($DBPath = null) {
  global $DBFILE;
  global $db;

  // Use custom path if supplied
  if ($DBPath !== null) {
      $DBFILE = $DBPath;
  }

  if (strlen($DBFILE) == 0) {
      echo '<script>alert("Database not available")</script>';
      die('<div style="padding-left:150px">Database not available</div>');
  }

  try {
      $db = new CustomDatabaseWrapper($DBFILE);
  } catch (Exception $e) {
      echo '<script>alert("Error connecting to the database: ' . $e->getMessage() . '")</script>';
      die('<div style="padding-left:150px">Error connecting to the database</div>');
  }

  $db->exec('PRAGMA journal_mode = wal;');  
}



// # Open DB once and keep open
// # Opening / closing DB frequently actually casues more issues
OpenDB (); // main
