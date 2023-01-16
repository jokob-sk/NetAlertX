<?php

// ###################################
// ## GUI settings processing start
// ###################################

if( isset($_COOKIE['Front_Dark_Mode_Enabled']))
{
    $ENABLED_DARKMODE = $_COOKIE['Front_Dark_Mode_Enabled'] == "true";
}else
{
    $ENABLED_DARKMODE = False;
}

foreach (glob("/home/pi/pialert/db/setting_skin*") as $filename) {
    $pia_skin_selected = str_replace('setting_','',basename($filename));
}
if (isset($pia_skin_selected) == FALSE or (strlen($pia_skin_selected) == 0)) {$pia_skin_selected = 'skin-blue';}

// ###################################
// ## GUI settings processing end
// ###################################

?>