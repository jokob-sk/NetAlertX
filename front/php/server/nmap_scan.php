<?php

$PIA_HOST_IP = $_REQUEST['scan'];
$PIA_SCAN_MODE = $_REQUEST['mode'];

if ($PIA_SCAN_MODE == 'fast') {
    exec('nmap -F '.$PIA_HOST_IP, $output);
} elseif ($PIA_SCAN_MODE == 'normal') {
    exec('nmap '.$PIA_HOST_IP, $output);
} elseif ($PIA_SCAN_MODE == 'detail') {
    exec('nmap -A '.$PIA_HOST_IP, $output);
}

echo '<h4>Scan ('.$PIA_SCAN_MODE.') Results of: '.$PIA_HOST_IP.'</h4>';
echo '<pre style="border: none;">'; 
foreach($output as $line){
    echo $line . "\n";
}
echo '</pre>';
?>