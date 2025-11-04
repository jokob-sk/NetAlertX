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
    $configRoot = getenv('NETALERTX_CONFIG') ?: '/data/config';
    $apiRoot = getenv('NETALERTX_API') ?: '/tmp/api';
    // Get query string parameter ?file=settings_table.json
    $file = isset($_GET['file']) ? $_GET['file'] : null;

    // Check if file parameter is provided
    if ($file) {
        // Define the folder where files are located
        if ($file == "workflows.json") 
        {
            $filePath = rtrim($configRoot, '/') . "/" . basename($file);
        } else
        {       
            $filePath = rtrim($apiRoot, '/') . "/" . basename($file);
        }

        // Check if the file exists
        if (file_exists($filePath)) {
            // Send the response back to the client
            header('Content-Type: application/json');
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
} elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Read the input JSON data
    $inputData = file_get_contents("php://input");
    $decodedData = json_decode($inputData, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        http_response_code(400);
        echo json_encode(["error" => "Invalid JSON data"]);
        exit;
    }

    // Check if file parameter is provided and is workflows.json
    if (!isset($_GET['file']) || $_GET['file'] !== "workflows.json") {
        http_response_code(400);
        echo json_encode(["error" => "Invalid or missing file parameter"]);
        exit;
    }
    
    $file = $_GET['file'];
    $configRoot = getenv('NETALERTX_CONFIG') ?: '/data/config';
    $filePath = rtrim($configRoot, '/') . "/" . basename($file);

    // Save new workflows.json (replace existing content)
    if (file_put_contents($filePath, json_encode($decodedData, JSON_PRETTY_PRINT))) {
        http_response_code(200);
        echo json_encode(["success" => "Workflows replaced successfully"]);
    } else {
        http_response_code(500);
        echo json_encode(["error" => "Failed to update workflows.json"]);
    }
}
else {
    http_response_code(405);
    echo json_encode(["error" => "Method Not Allowed"]);
}
?>
