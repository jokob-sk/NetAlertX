<?php
if (session_status() == PHP_SESSION_NONE) {
    session_start();
}

$isAuthenticated = false;

// Check if the user is logged in
if (isset($_SESSION["login"]) && $_SESSION["login"] == 1) {
    $isAuthenticated = true;
}

// $current_directory = __DIR__;
// echo "Current directory: " . $current_directory;

// Check if a valid cookie is present
$CookieSaveLoginName = "NetAlertX_SaveLogin";
$config_file = "../../../config/app.conf"; // depends on where this file is called from
$config_file_lines = file($config_file);
$config_file_lines = array_values(preg_grep('/^SETPWD_password.*=/', $config_file_lines));
$password_line = explode("'", $config_file_lines[0]);
$nax_Password = $password_line[1];

if (isset($_COOKIE[$CookieSaveLoginName]) && $nax_Password === $_COOKIE[$CookieSaveLoginName]) {
    $isAuthenticated = true;
}

if ($isAuthenticated) {
    echo 'Authorized 200';
    http_response_code(200);
    exit;  // Important: Ensure script exits after successful authentication
} else {
    http_response_code(401);
    echo 'Unauthorized 401';
    exit;  // Ensure script exits after failed authentication
}
?>
