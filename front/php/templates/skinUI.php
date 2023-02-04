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
