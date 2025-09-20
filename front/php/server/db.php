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
// $DBFILE = dirname(__FILE__).'/../../../db/app.db';
// $DBFILE_LOCKED_FILE = dirname(__FILE__).'/../../../log/db_is_locked.log';
$scriptDir = realpath(dirname(__FILE__)); // Resolves symlinks to the actual physical path
$DBFILE = $scriptDir . '/../../../db/app.db';
$DBFILE_LOCKED_FILE = $scriptDir . '/../../../log/db_is_locked.log';


//------------------------------------------------------------------------------
// check if authenticated
require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

$db_locked = false;

//------------------------------------------------------------------------------
// Connect DB
//------------------------------------------------------------------------------
function SQLite3_connect($trytoreconnect = true, $retryCount = 0) {
    global $DBFILE, $DBFILE_LOCKED_FILE;
    $maxRetries = 5; // Maximum number of retries
    $baseDelay = 1; // Base delay in seconds

    try {
        // Connect to database
        global $db_locked;
        $db_locked = false;

        if (!file_exists($DBFILE)) {
            die("Database file not found: $DBFILE");
        }
        if (!file_exists(dirname($DBFILE_LOCKED_FILE))) {
            die("Log directory not found: " . dirname($DBFILE_LOCKED_FILE));
        }
       

        // Write unlock status to the locked file
        file_put_contents($DBFILE_LOCKED_FILE, '0');

        return new SQLite3($DBFILE, SQLITE3_OPEN_READWRITE);
    } catch (Exception $exception) {
        // sqlite3 throws an exception when it is unable to connect
        global $db_locked;
        $db_locked = true;

        // Write lock status to the locked file
        file_put_contents($DBFILE_LOCKED_FILE, '1');
        error_log("Failed to connect to database: " . $exception->getMessage());

        // Connection failed, check if we should retry
        if ($trytoreconnect && $retryCount < $maxRetries) {
            // Calculate exponential backoff delay
            $delay = $baseDelay * pow(2, $retryCount);
            sleep($delay);

            // Retry the connection with an increased retry count
            return SQLite3_connect(true, $retryCount + 1);
        } else {
            // Maximum retries reached, hide loading spinner and show failure alert
            $message = 'Failed to connect to database after ' . $retryCount . ' retries.';
            write_notification($message);
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

    public function __construct($filename, $flags = SQLITE3_OPEN_READWRITE | SQLITE3_OPEN_CREATE, 
            $maxRetries = 3, $retryDelay = 1000, $encryptionKey = "") {
        $this->sqlite = new SQLite3($filename, $flags, $encryptionKey);
        $this->maxRetries = $maxRetries;
        $this->retryDelay = $retryDelay;
    }

    public function query(string $query): SQLite3Result|bool {
      global $DBFILE_LOCKED_FILE;

      // Check if the query is an UPDATE, DELETE, or INSERT
      $queryType = strtoupper(substr(trim($query), 0, strpos(trim($query), ' ')));
      $isModificationQuery = in_array($queryType, ['UPDATE', 'DELETE', 'INSERT']);
  
      $attempts = 0;
        while ($attempts < $this->maxRetries) {

          $result = false;

          try {
            $result = $this->sqlite->query($query);   
          } catch (Exception $exception) {
            // continue unless maxRetries reached
            if($attempts > $this->maxRetries)
            {
              throw $exception;
            }            
          }                     

          if ($result !== false and $result !== null) {

            $this->query_log_remove($query);
              
            return $result;
          }

          $this->query_log_add($query);          

          $attempts++;
          usleep($this->retryDelay * 1000 * $attempts); // Retry delay in milliseconds
        }

        // If all retries failed, throw an exception or handle the error as needed
        // Add '0' to indicate that the database is not locked/execution failed 
        file_put_contents($DBFILE_LOCKED_FILE, '0');

        $message = 'Error executing query (attempts: ' . $attempts . '), query: ' . $query;        
        // write_notification($message);
        error_log("Query failed after {$this->maxRetries} attempts: " . $this->sqlite->lastErrorMsg());        
    }

    public function query_log_add($query)
    {
        global $DBFILE_LOCKED_FILE;
    
        // Remove new lines from the query
        $query = str_replace(array("\r", "\n"), ' ', $query);
    
        // Generate a hash of the query
        $queryHash = md5($query);
    
        // Log the query being attempted along with timestamp and query hash
        $executionLog = "1|" . date('Y-m-d H:i:s') . "|$queryHash|$query";
        error_log("Attempting to write '$executionLog' to execution log file after failed query: $query");
        file_put_contents($DBFILE_LOCKED_FILE, $executionLog . PHP_EOL, FILE_APPEND);
        error_log("Execution log file content after failed query attempt: " . file_get_contents($DBFILE_LOCKED_FILE));
    }
    
    public function query_log_remove($query)
    {
        global $DBFILE_LOCKED_FILE;

        // Remove new lines from the query
        $query = str_replace(array("\r", "\n"), ' ', $query);
    
        // Generate a hash of the query
        $queryHash = md5($query);
    
        // Remove the entry corresponding to the finished query from the execution log based on query hash
        $executionLogs = file($DBFILE_LOCKED_FILE, FILE_IGNORE_NEW_LINES);
        $executionLogs = array_filter($executionLogs, function($log) use ($queryHash) {
            return strpos($log, $queryHash) === false;
        });
        file_put_contents($DBFILE_LOCKED_FILE, implode(PHP_EOL, $executionLogs));
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
        $message = 'Database not available';
        echo '<script>alert('.$message.')</script>';
        write_notification($message);
        
        die('<div style="padding-left:150px">'.$message.'</div>');
    }

    try {
        $db = new CustomDatabaseWrapper($DBFILE);
    } catch (Exception $e) {
        $message = "Error connecting to the database";
        echo '<script>alert('.$message.'": ' . $e->getMessage() . '")</script>';
        write_notification($message);
        die('<div style="padding-left:150px">'.$message.'</div>');
    }

    $db->exec('PRAGMA journal_mode = wal;');
}

// Open DB once and keep open
OpenDB(); // main
?>
