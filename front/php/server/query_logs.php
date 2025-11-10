<?php

// ---- IMPORTS ----
//------------------------------------------------------------------------------
// Check if authenticated
require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
// Get init.php
require dirname(__FILE__).'/../server/init.php';
// ---- IMPORTS ----

//------------------------------------------------------------------------------
// Handle incoming requests
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    // Get query string parameter ?file=settings_table.json
    $file = isset($_GET['file']) ? $_GET['file'] : null;

    // Check if file parameter is provided
    if ($file) {
    // Define the folder where files are located
    $logBasePath = rtrim(getenv('NETALERTX_LOG') ?: '/tmp/log', '/');
    $filePath = $logBasePath . '/' . basename($file);

        // Check if the file exists
        if (file_exists($filePath)) {
            // Send the response back to the client
            header('Content-Type: text/plain');
            echo file_get_contents($filePath);
        } else {
            // File not found response
            http_response_code(404);
            echo json_encode(["error" => "File not found"]);
        }
    } else {
        // Missing file parameter response
        http_response_code(400);
        echo json_encode(["error" => "Missing 'file' parameter"]);
    }
}
?>
