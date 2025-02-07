<?php

// ###################################
// ## TimeZone processing start
// ###################################

$configFolderPath = dirname(__FILE__)."/../../../config/";
$config_file = "app.conf";
$logFolderPath = "/app/log/";
$log_file = "app_front.log";
$default_tz = "Europe/Berlin";


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
  $timeZone = $default_tz;
}

// Validate the timezone
if (!in_array($timeZone, timezone_identifiers_list())) {
  error_log("Invalid timezone '$timeZone' in config. Falling back to default: '$default_tz' ");
  $timeZone = $default_tz;
}

date_default_timezone_set($timeZone);

$date = new DateTime("now", new DateTimeZone($timeZone) );
$timestamp = $date->format('Y-m-d_H-i-s');

// ###################################
// ## TimeZone processing end
// ###################################

