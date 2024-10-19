<?php

// ###################################
// ## GUI settings processing start
// ###################################

if( isset($_COOKIE['UI_theme']))
{
    $UI_THEME = $_COOKIE['UI_theme'];
}else
{
    $UI_THEME = "Light";
}

$pia_skin_selected = 'skin-blue';

// ###################################
// ## GUI settings processing end
// ###################################

?>
