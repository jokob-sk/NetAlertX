<?php

$url = 'http://' . $_SERVER['SERVER_NAME'] . $_SERVER['REQUEST_URI'];
$isLogonPage = FALSE;

$CookieSaveLoginName = "NetAlertX_SaveLogin";


if (strpos($url,'index.php') !== false) {
    $isLogonPage = TRUE;
} 

// start session if not started yet
if (session_status() == PHP_SESSION_NONE) {
    session_start();
}

if(array_search('action', $_REQUEST) != FALSE)
{
  if ($_REQUEST['action'] == 'logout') {
    session_destroy();
    setcookie($CookieSaveLoginName, "", time() - 3600);
    header('Location: index.php');
    exit(); // ensure script stops after header redirection
  }    
}

// ##################################################
// ## Login Processing start
// ##################################################
$config_file = $_SERVER['DOCUMENT_ROOT'] . "/../config/app.conf";

if (file_exists($config_file)) {
    $config_file_lines = file($config_file);
} else {
    // handle missing config file
    die("Configuration file not found.");
}

$CookieSaveLoginName = "NetAlertX_SaveLogin";

// ###################################
// ## SETPWD_enable_password FALSE
// ###################################

// Find SETPWD_enable_password line
$config_file_lines_bypass = array_values(preg_grep('/^SETPWD_enable_password.*=/', $config_file_lines));

if (!empty($config_file_lines_bypass)) {
    $protection_line = explode("=", $config_file_lines_bypass[0]);
    $nax_WebProtection = strtolower(trim($protection_line[1]));
} else {
    // Default behavior if SETPWD_enable_password is not found
    $nax_WebProtection = 'false'; // or another default value
}

// ###################################
// ## SETPWD_enable_password TRUE
// ###################################

// Find SETPWD_password line
$config_file_lines_password = array_values(preg_grep('/^SETPWD_password.*=/', $config_file_lines));

if (!empty($config_file_lines_password)) {
    $password_line = explode("'", $config_file_lines_password[0]);
    $nax_Password = $password_line[1];
} else {
    // Default behavior if SETPWD_password is not found
    $nax_Password = ''; // or handle accordingly
}

// active Session or valid cookie (cookie not extends)
if($nax_WebProtection == 'true')
{
    if(isset($_SESSION["login"]) == FALSE )
    {
        $_SESSION["login"] = 0;
    }     

    if ($_SESSION["login"] == 1 || $isLogonPage || (isset($_COOKIE[$CookieSaveLoginName]) && $nax_Password == $_COOKIE[$CookieSaveLoginName]))
    {
        // Logged in or stay on this page if we are on the index.php already   
        
    } else 
    {
        // we need to redirect        
        header('Location: /index.php');
        exit(); // ensure script stops after header redirection
    } 

}

?>
