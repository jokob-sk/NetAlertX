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
    // Get query string parameters ?file=settings_table.json&download=true
    $file = isset($_GET['file']) ? $_GET['file'] : null;
    $download = isset($_GET['download']) ? $_GET['download'] === 'true' : false;

    // Check if file parameter is provided
    if ($file) {
        // Define the folder where files are located
        $filePath = "/app/config/" . basename($file);

        // Check if the file exists
        if (file_exists($filePath)) {
            // Handle download behavior
            if ($download) {
                // Force file download
                header('Content-Description: File Transfer');
                header('Content-Type: application/octet-stream');
                header('Content-Disposition: attachment; filename="' . basename($filePath) . '"');
                header('Expires: 0');
                header('Cache-Control: must-revalidate');
                header('Pragma: public');
                header('Content-Length: ' . filesize($filePath));
                readfile($filePath);
                exit;
            } else {
                // Display file content
                header('Content-Type: text/plain');
                echo file_get_contents($filePath);
            }
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
