<?php

// External files
require '/app/front/php/server/init.php';

$method = $_SERVER['REQUEST_METHOD'];

// ----------------------------------------------
// Method to check authorization
function checkAuthorization($method) {
    // Retrieve the authorization header
    $headers = apache_request_headers();
    $auth_header = $headers['Authorization'] ?? '';
    $expected_token = 'Bearer ' . getSettingValue('SYNC_api_token');

    // Verify the authorization token
    if ($auth_header !== $expected_token) {
        http_response_code(403);
        echo 'Forbidden';
        write_notification("[Plugin: SYNC] Incoming data: Incorrect API Token (".$method.")", "alert");
        exit;
    }
}

// ----------------------------------------------
// Function to return JSON response
function jsonResponse($status, $data = [], $message = '') {
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode([
        'node_name' => getSettingValue('SYNC_node_name'),
        'status' => $status,
        'message' => $message,
        'data' => $data,
        'timestamp' => date('Y-m-d H:i:s')
    ]);
}

// ----------------------------------------------
//  MAIN
// ----------------------------------------------


// requesting data (this is a NODE)
if ($method === 'GET') {
    checkAuthorization($method);

    $file_path = "/app/front/api/table_devices.json";

    $data = file_get_contents($file_path);   

    // Prepare the data to return as a JSON response
    $response_data = [
        'data_base64' => base64_encode($data),  
    ];

    // Return JSON response
    jsonResponse(200, $response_data, 'OK');

}
// receiving data (this is a HUB)
else if ($method === 'POST') {
    checkAuthorization($method);

    // Retrieve and decode the data from the POST request
    $data = $_POST['data'] ?? '';
    $plugin_folder = $_POST['plugin_folder'] ?? '';
    $node_name = $_POST['node_name'] ?? '';

    $storage_path = "/app/front/plugins/{$plugin_folder}";

    // Create the storage directory if it doesn't exist
    if (!is_dir($storage_path)) {
        echo "Could not open folder: {$storage_path}";
        write_notification("[Plugin: SYNC] Could not open folder: {$storage_path}", "alert"); 
        http_response_code(500);
        exit;
    }

    // Generate a unique file path to avoid overwriting existing files
    $encoded_files = glob("{$storage_path}/last_result.encoded.{$node_name}.*.log");
    $decoded_files = glob("{$storage_path}/last_result.decoded.{$node_name}.*.log");

    $files = array_merge($encoded_files, $decoded_files);
    $file_count = count($files) + 1;

    $file_path = "{$storage_path}/last_result.encoded.{$node_name}.{$file_count}.log";

    // Save the decoded data to the file
    file_put_contents($file_path, $data);
    http_response_code(200);
    echo 'Data received and stored successfully';
    write_notification("[Plugin: SYNC] Data received ({$plugin_folder})", "info");

} else {
    http_response_code(405);
    echo 'Method Not Allowed';
    write_notification("[Plugin: SYNC] Method Not Allowed", "alert");
}
?>
