<?php

###################################################################################
#  Pi.Alert                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #
#                                                                                 #
#  nslookup.php # Front module. Server side. System Information                   #
###################################################################################
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob#sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
###################################################################################

// Get init.php 
require dirname(__FILE__).'/../server/init.php';

// Get IP
$ip = $_GET['ip'];

// Check if IP is valid
if (!filter_var($ip, FILTER_VALIDATE_IP)) {
	// Error message
	$output = lang('DevDetail_Tab_Tools_Nslookup_Error');
	// Show the result
	echo "<pre>";
	echo $output;
	echo "</pre>";
	exit;
}

// Test with the "nslookup" command
$output = shell_exec("nslookup $ip");

// Show the result
echo "<pre>";
echo $output;
echo "</pre>";

?>
