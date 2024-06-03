<?php

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Retrieve the authorization header
    $headers = apache_request_headers();
    $auth_header = $headers['Authorization'] ?? '';
    $expected_token = 'Bearer ' . getSettingValue('SYNC_api_token');

    // Verify the authorization token
    if ($auth_header !== $expected_token) {
        http_response_code(403);
        echo 'Forbidden';
        exit;
    }

    // Retrieve and decode the data from the POST request
    $data = $_POST['data'] ?? '';
    $plugin_folder = $_POST['plugin_folder'] ?? '';
    $node_name = $_POST['node_name'] ?? '';

    $decoded_data = hex2bin($data);
    $storage_path = "/app/front/plugins/{$plugin_folder}";

    // Create the storage directory if it doesn't exist
    if (!is_dir($storage_path)) {
        echo "Could not open folder: {$storage_path}";
        http_response_code(500);
        exit;
    }

    // Generate a unique file path to avoid overwriting existing files
    $files = glob("{$storage_path}/last_result.{$node_name}.*.log");
    $files = array_filter($files, function($file) {
        return preg_match('/last_result\.\d+\.log$/', basename($file));
    });
    $file_count = count($files) + 1;
    $file_path = "{$storage_path}/last_result.{$node_name}.{$file_count}.log";

    // Save the decoded data to the file
    file_put_contents($file_path, $decoded_data);
    http_response_code(200);
    echo 'Data received and stored successfully';
} else {
    http_response_code(405);
    echo 'Method Not Allowed';
}
?>
