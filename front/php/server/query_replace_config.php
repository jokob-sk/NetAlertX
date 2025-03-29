<?php

// ---- IMPORTS ----
//------------------------------------------------------------------------------
// Check if authenticated
require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
// Get init.php 
require dirname(__FILE__).'/../server/init.php';
// ---- IMPORTS ----

global $configFolderPath;

//------------------------------------------------------------------------------
// Handle incoming requests
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Access the 'config' parameter from the POST request
    $base64Data = $_POST['base64data'] ?? null;

    if (!$base64Data) {
        $msg = "Missing 'base64data' parameter.";
        echo $msg;
        http_response_code(400); // Bad request
        die($msg);
    }
    $fileName = $_POST['fileName'] ?? null;

    if (!$fileName) {
        $msg = "Missing 'fileName' parameter.";
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

    $fullPath = $configFolderPath.$fileName;

    // Backup the original file
    if (file_exists($fullPath)) {
        copy($fullPath, $fullPath . ".bak");
    }

    // Write the new configuration
    $file = fopen($fullPath, "w");
    if (!$file) {
        $msg = "Unable to open file: ". $fullPath;
        echo $msg;
        http_response_code(500); // Server error
        die($msg);
    }

    fwrite($file, $input);
    fclose($file);

    echo "Configuration file saved successfully: " .$fileName ;
}
?>
