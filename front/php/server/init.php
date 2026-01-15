<?php
$logPath = rtrim(getenv('NETALERTX_LOG') ?: '/tmp/log', '/') . '/app.php_errors.log';
ini_set('error_log', $logPath); // initializing the app.php_errors.log file for the maintenance section
require dirname(__FILE__).'/../templates/globals.php';
require dirname(__FILE__).'/db.php';
require dirname(__FILE__).'/util.php';
require dirname(__FILE__).'/../templates/language/lang.php';
?>
