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
    $download = isset($_GET['download']) && $_GET['download'] === 'true';

    // Check if file parameter is provided
    if ($file) {
        // Define the folder where files are located
        $configRoot = getenv('NETALERTX_CONFIG') ?: '/data/config';
        $filePath = rtrim($configRoot, '/') . "/" . basename($file);

        // Check if the file exists and is readable
        if (file_exists($filePath) && is_readable($filePath)) {
            // Determine file extension
            $extension = pathinfo($filePath, PATHINFO_EXTENSION);

            if ($download) {
                // Force file download
                header('Content-Description: File Transfer');
                header('Content-Type: application/octet-stream');
                header('Content-Disposition: attachment; filename="' . basename($file) . '"');
                header('Expires: 0');
                header('Cache-Control: must-revalidate');
                header('Pragma: public');
                header('Content-Length: ' . filesize($filePath));
                readfile($filePath);
                exit;
            } else {
                // Serve file based on type
                if ($extension === 'json') {
                    header('Content-Type: application/json');
                    echo json_encode(json_decode(file_get_contents($filePath), true), JSON_PRETTY_PRINT);
                } else {
                    header('Content-Type: text/plain');
                    echo file_get_contents($filePath);
                }
                exit;
            }
        } else {
            // File not found response
            http_response_code(404);
            header('Content-Type: application/json');
            echo json_encode(["error" => "File not found"]);
            exit;
        }
    } else {
        // Missing file parameter response
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(["error" => "Missing 'file' parameter"]);
        exit;
    }
}
?>
