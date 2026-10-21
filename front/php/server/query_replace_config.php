<?php

// ---- IMPORTS ----
//------------------------------------------------------------------------------
// Check if authenticated
require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

// Get init.php
require dirname(__FILE__) . '/../server/init.php';
// ---- IMPORTS ----

header('Content-Type: text/plain; charset=utf-8');

global $configFolderPath;

//------------------------------------------------------------------------------
// Handle incoming requests
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    requireCsrfToken();

    $base64Data = $_POST['base64data'] ?? null;
    if (!$base64Data) {
        http_response_code(400);
        die("Missing 'base64data' parameter.");
    }

    $fileName = $_POST['fileName'] ?? null;
    if (!$fileName) {
        http_response_code(400);
        die("Missing 'fileName' parameter.");
    }

    //--------------------------------------------------------------------------
    // Only allow known configuration files
    $safeName = basename($fileName);

    $allowedFiles = [
        'app.conf',
        'workflows.json',
        'devices.csv',
    ];

    if (!in_array($safeName, $allowedFiles, true)) {
        http_response_code(400);
        die("Invalid fileName.");
    }

    $fullPath = rtrim($configFolderPath, DIRECTORY_SEPARATOR)
        . DIRECTORY_SEPARATOR
        . $safeName;

    //--------------------------------------------------------------------------
    // Decode incoming base64 data
    $input = base64_decode($base64Data, true);

    if ($input === false) {
        http_response_code(400);
        die("Invalid base64 data.");
    }

    //--------------------------------------------------------------------------
    // Backup the original file
    if (file_exists($fullPath)) {
        copy($fullPath, $fullPath . ".bak");
    }

    //--------------------------------------------------------------------------
    // Write the new configuration
    if (file_put_contents($fullPath, $input, LOCK_EX) === false) {
        http_response_code(500);
        die("Unable to save configuration file.");
    }

    echo "Configuration file saved successfully: " . $safeName;
}