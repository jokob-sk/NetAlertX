<?php

// ###################################
// ## GUI settings processing start
// ###################################

if( isset($_COOKIE['UI_dark_mode']))
{
    $ENABLED_DARKMODE = $_COOKIE['UI_dark_mode'] == "True";
}else
{
    $ENABLED_DARKMODE = False;
}

$pia_skin_selected = 'skin-blue';

// ###################################
// ## GUI settings processing end
// ###################################

?>