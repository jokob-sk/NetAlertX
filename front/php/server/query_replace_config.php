<?php

// ---- IMPORTS ----
//------------------------------------------------------------------------------
// Check if authenticated
require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
// Get init.php 
require dirname(__FILE__).'/../server/init.php';
// ---- IMPORTS ----

global $fullConfPath;

//------------------------------------------------------------------------------
// Handle incoming requests
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Access the 'config' parameter from the POST request
    $base64Data = $_POST['config'] ?? null;

    if (!$base64Data) {
        $msg = "Missing 'config' parameter.";
        echo $msg;
        http_response_code(400); // Bad request
        die($msg);
    }

    // Decode incoming base64 data
    $input = base64_decode($base64Data, true);

    if ($input === false) {
        $msg = "Invalid base64 data.";
        echo $msg;
        http_response_code(400); // Bad request
        die($msg);
    }

    // Backup the original file
    if (file_exists($fullConfPath)) {
        copy($fullConfPath, $fullConfPath . ".bak");
    }

    // Write the new configuration
    $file = fopen($fullConfPath, "w");
    if (!$file) {
        $msg = "Unable to open file!";
        echo $msg;
        http_response_code(500); // Server error
        die($msg);
    }

    fwrite($file, $input);
    fclose($file);

    echo "Configuration saved successfully.";
}
?>
