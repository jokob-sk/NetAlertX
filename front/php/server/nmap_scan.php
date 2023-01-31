<?php

require 'util.php';

$PIA_HOST_IP = $_REQUEST['scan'];
$PIA_SCAN_MODE = $_REQUEST['mode'];

if(filter_var($PIA_HOST_IP, FILTER_VALIDATE_IP))  // Vulnerability fix v22.12.20
{
    if ($PIA_SCAN_MODE == 'fast') {
        exec('nmap -F '.$PIA_HOST_IP, $output);
    } elseif ($PIA_SCAN_MODE == 'normal') {
        exec('nmap '.$PIA_HOST_IP, $output);
    } elseif ($PIA_SCAN_MODE == 'detail') {
        exec('nmap -A '.$PIA_HOST_IP, $output);
    } elseif ($PIA_SCAN_MODE == 'skipdiscovery') {
        exec('nmap -Pn '.$PIA_HOST_IP, $output);
    }

    $message = '<h4>Scan ('.$PIA_SCAN_MODE.') Results of: '.$PIA_HOST_IP.'</h4><br/>'
    .'<pre style="border: none;">';

    foreach($output as $line){
        $message = $message .$line . "<br/>";
    }

    $message = $message .'</pre>';

    displayMessage($message, $logAlert = FALSE, $logConsole = TRUE, $logFile = TRUE, $logEcho = TRUE);

   
} else
{
    echo '<h4>Internal error.</h4>';
}
