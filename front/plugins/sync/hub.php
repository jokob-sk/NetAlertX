<?php

// External files
require '/app/front/php/server/init.php';


if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Retrieve the authorization header
    $headers = apache_request_headers();
    $auth_header = $headers['Authorization'] ?? '';
    $expected_token = 'Bearer ' . getSettingValue('SYNC_api_token');

    // Verify the authorization token
    if ($auth_header !== $expected_token) {
        http_response_code(403);
        echo 'Forbidden';
        write_notification("[Plugin: Sync hub API] Incorrect API Token", "alert"); 
        exit;
    }

    // Retrieve and decode the data from the POST request
    $data = $_POST['data'] ?? '';
    $plugin_folder = $_POST['plugin_folder'] ?? '';
    $node_name = $_POST['node_name'] ?? '';


    $storage_path = "/app/front/plugins/{$plugin_folder}";

    // Create the storage directory if it doesn't exist
    if (!is_dir($storage_path)) {
        echo "Could not open folder: {$storage_path}";
        write_notification("[Plugin: Sync hub API] Could not open folder: {$storage_path}", "alert"); 
        http_response_code(500);
        exit;
    }

    // Generate a unique file path to avoid overwriting existing files
    $files = glob("{$storage_path}/last_result.encoded.{$node_name}.*.log");
    $file_count = count($files) + 1;
    $file_path = "{$storage_path}/last_result.encoded.{$node_name}.{$file_count}.log";

    // Save the decoded data to the file
    file_put_contents($file_path, $data);
    http_response_code(200);
    echo 'Data received and stored successfully';
    write_notification("[Plugin: Sync hub API] Data received ({$plugin_folder})", "info");
} else {
    http_response_code(405);
    echo 'Method Not Allowed';
    write_notification("[Plugin: Sync hub API] Method Not Allowed", "alert");
}
?>
