<?php

#---------------------------------------------------------------------------------#
#  Pi.Alert                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #  
#                                                                                 #
#  wol.php - Front module. Server side. System Information                        #
#---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
#---------------------------------------------------------------------------------#

/*
 * This code will send a Wake-on-LAN packet to the specified MAC address.
 *
 * The MAC address must be in the format AA:BB:CC:DD:EE:FF.
 *
 * The port and password are optional. If no port is specified, the default port of 9 is used.
 * If no password is specified, no password is used.
 */
 
// Get init.php 
require dirname(__FILE__).'/../server/init.php';

// Get the MAC address of the device to wake up
$mac = $_GET['mac'];

// Validate the MAC address
if (!filter_var($mac, FILTER_VALIDATE_MAC)) {
	// Error message
	$output = lang('DevDetail_Tab_Tools_WOL_Error_MAC');
	// Show the result
	echo "<pre>";
	echo $output;
	echo "</pre>";
	exit;
}

// Get the port 
$port = isset($_GET['port']) ? $_GET['port'] : 9;

// Validate the port
if (!filter_var($port, FILTER_VALIDATE_INT, array('options' => array('min_range' => 1, 'max_range' => 65535)))) {
	// Error message
	$output = lang('DevDetail_Tab_Tools_WOL_Error_Port');
	// Show the result
	echo "<pre>";
	echo $output;
	echo "</pre>";
	exit;
}

// Get password
$password = isset($_GET['password']) ? $_GET['password'] : '';

// Validate the password
if (!filter_var($password, FILTER_VALIDATE_REGEXP, array("options" => array("regexp" => "/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/"))) {
	// Error message
	$output = lang('DevDetail_Tab_Tools_WOL_Error_Password');
	// Show the result
	echo "<pre>";
	echo $output;
	echo "</pre>";
	exit;
}

// Create the magic packet
$magicPacket = pack('H*', 'FF FF FF FF FF FF FF ' . $mac);

// Create a UDP socket
$socket = socket_create(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

// Set the socket options
socket_set_option($socket, SOL_SOCKET, SO_BROADCAST, true);

// Send the WoL packet
socket_sendto($socket, $magicPacket, strlen($magicPacket), 0, '255.255.255.255', $port);

// Close the socket
socket_close($socket);

// Print a message to indicate that the device has been woken up
echo "<pre>";
$output = lang('DevDetail_Tab_Tools_WOL_Message');
echo $output;
echo "</pre>";

?>
