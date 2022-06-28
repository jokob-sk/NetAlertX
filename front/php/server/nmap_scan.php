<?php

$PIA_HOST_IP = $_REQUEST['scan'];
exec('nmap '.$PIA_HOST_IP, $output);
echo '<pre style="border: none;">'; 
foreach($output as $line){
    echo $line . "\n";
}
echo '</pre>';
?>