<?php

// External files
require '/app/front/php/server/init.php';


function decrypt_data($encoded_data, $key) {
    // Base64 decode the encrypted data
    $data = base64_decode($encoded_data);

    // Extract the IV and the ciphertext
    $iv = substr($data, 0, 16);
    $ciphertext = substr($data, 16);

    // Derive the key using SHA-256
    $key = hash('sha256', $key, true);

    // Decrypt the ciphertext using AES-256-CBC
    $decrypted_data = openssl_decrypt($ciphertext, 'aes-256-cbc', $key, OPENSSL_RAW_DATA, $iv);

    // Remove padding
    $decrypted_data = rtrim($decrypted_data, "\0");
    
    return $decrypted_data;
}

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

    $decoded_data = decrypt_data($data, getSettingValue('SYNC_encryption_key'));

    if ($decoded_data === false or $decoded_data === null) {
        write_notification("[Plugin: Sync hub API] Bad Request: Decryption failed", "alert");
        http_response_code(400);
        echo 'Bad Request: Decryption failed';
        exit;
    }

    $storage_path = "/app/front/plugins/{$plugin_folder}";

    // Create the storage directory if it doesn't exist
    if (!is_dir($storage_path)) {
        echo "Could not open folder: {$storage_path}";
        write_notification("[Plugin: Sync hub API] Could not open folder: {$storage_path}", "alert"); 
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
    write_notification("[Plugin: Sync hub API] Method Not Allowed", "alert");
}
?>
