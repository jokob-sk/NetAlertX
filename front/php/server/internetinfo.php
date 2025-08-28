<?php

###################################################################################
#  NetAlertX                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #
#                                                                                 #
#  internetinfo.php # Front module. Server side. System Information               #
###################################################################################
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob#sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
###################################################################################


// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /nettools
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺

// Get init.php 
require dirname(__FILE__).'/../server/init.php';

//------------------------------------------------------------------------------
// check if authenticated
require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

// Perform a test with the PING command
$output = shell_exec("curl ipinfo.io");

// Check if there is error
if (!isset($output) || empty($output)) {
	// Error message
	$output = lang('DevDetail_Tab_Tool_Internet_Info_Error');
	// Show the result
	echo "<pre>";
	echo $output;
	echo "</pre>";
	exit;	
} 
	
// Replace "{" with ""
$output = str_replace("{", "", $output);

// Replace "}" with ""
$output = str_replace("}", "", $output);

// Replace "," with ""
$output = str_replace(",", "", $output);

// Replace '"' with ""
$output = str_replace('"', "", $output);

// Show the result
echo "<pre>";
echo $output;
echo "</pre>";

?>
