<?php

// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /messaging/in-app
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺

require dirname(__FILE__).'/../templates/globals.php';

function get_notification_store_path(): string {
    $apiRoot = getenv('NETALERTX_API') ?: '/tmp/api';
    return rtrim($apiRoot, '/') . '/user_notifications.json';
}

//------------------------------------------------------------------------------
// check if authenticated
require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

// ----------------------------------------------------------------------------------------
// Check if the action parameter is set in the GET request
if (isset($_GET['action'])) {
    // Collect GUID if provided
    $guid = isset($_GET['guid']) ? $_GET['guid'] : null;

    // Perform the appropriate action based on the action parameter
    switch ($_GET['action']) {
        case 'write_notification':
            // Call the write_notification function with content and level parameters
            if (isset($_GET['content'])) {
                $content = $_GET['content'];
                $level = isset($_GET['level']) ? $_GET['level'] : "interrupt";
                write_notification($content, $level);
            }
            break;
        case 'remove_notification':
            // Call the remove_notification function with guid parameter
            if ($guid) {
                remove_notification($guid);
            }
            break;
        case 'mark_notification_as_read':
            // Call the mark_notification_as_read function with guid parameter
            if ($guid) {
                mark_notification_as_read($guid);
            }
            break;
        case 'notifications_clear':
            // Call the notifications_clear function
            notifications_clear();
            break;
        case 'notifications_mark_all_read':
            // Call the notifications_mark_all_read function
            notifications_mark_all_read();
            break;
        case 'get_unread_notifications':
            // Call the get_unread_notifications function
            get_unread_notifications();
            break;
    }
}

// ----------------------------------------------------------------------------------------
// Generates a random GUID
function generate_guid() {
    if (function_exists('com_create_guid') === true) {
        return trim(com_create_guid(), '{}');
    }
    return sprintf('%04X%04X-%04X-%04X-%04X-%04X%04X%04X',
        mt_rand(0, 65535), mt_rand(0, 65535), mt_rand(0, 65535),
        mt_rand(16384, 20479), mt_rand(32768, 49151), mt_rand(0, 65535),
        mt_rand(0, 65535), mt_rand(0, 65535));
  }

// ----------------------------------------------------------------------------------------
// Logs a notification in in-app notification system
function write_notification($content, $level = "interrupt") {
    $NOTIFICATION_API_FILE = get_notification_store_path();

    // Generate GUID
    $guid = generate_guid();

    // Generate timestamp
    $timestamp = (new DateTime('now'))->format('Y-m-d H:i:s');

    // Escape content to prevent breaking JSON
    $escaped_content = json_encode($content);

    // Prepare notification array
    $notification = array(
        'timestamp' => $timestamp,
        'guid' => $guid,
        'read' => 0,
        'level'=> $level,
        'content' => $escaped_content,
    );

    // Read existing notifications
    $notifications = json_decode(file_get_contents($NOTIFICATION_API_FILE), true);

    // Add new notification
    $notifications[] = $notification;

    // Write notifications to file
    file_put_contents($NOTIFICATION_API_FILE, json_encode($notifications));
}

// ----------------------------------------------------------------------------------------
// Removes a notification based on GUID
function remove_notification($guid) {
    $NOTIFICATION_API_FILE = get_notification_store_path();

    // Read existing notifications
    $notifications = json_decode(file_get_contents($NOTIFICATION_API_FILE), true);

    // Filter out the notification with the specified GUID
    $filtered_notifications = array_filter($notifications, function($notification) use ($guid) {
        return $notification['guid'] !== $guid;
    });

    // Write filtered notifications back to file
    file_put_contents($NOTIFICATION_API_FILE, json_encode(array_values($filtered_notifications)));
}

// ----------------------------------------------------------------------------------------
// Deletes all notifications
function notifications_clear() {
    $NOTIFICATION_API_FILE = get_notification_store_path();

    // Clear notifications by writing an empty array to the file
    file_put_contents($NOTIFICATION_API_FILE, json_encode(array()));
}

// ----------------------------------------------------------------------------------------
// Mark a notification read based on GUID
function mark_notification_as_read($guid) {
    $NOTIFICATION_API_FILE = get_notification_store_path();
    $max_attempts = 3;
    $attempts = 0;

    do {
        // Check if the file exists and is readable
        if (file_exists($NOTIFICATION_API_FILE) && is_readable($NOTIFICATION_API_FILE)) {
            // Attempt to read existing notifications
            $notifications = json_decode(file_get_contents($NOTIFICATION_API_FILE), true);

            // Check if reading was successful
            if ($notifications !== null) {
                // Iterate over notifications to find the one with the specified GUID
                foreach ($notifications as &$notification) {
                    if ($notification['guid'] === $guid) {
                        // Mark the notification as read
                        $notification['read'] = 1;
                        break;
                    } elseif ($guid == null) // no guid given, mark all read
                    {
                        $notification['read'] = 1;
                    }
                }

                // Write updated notifications back to file
                file_put_contents($NOTIFICATION_API_FILE, json_encode($notifications));
                return; // Exit the function after successful operation
            }
        }

        // Increment the attempt count
        $attempts++;

        // Sleep for a short duration before retrying
        usleep(500000); // Sleep for 0.5 seconds (500,000 microseconds) before retrying

    } while ($attempts < $max_attempts);

    // If maximum attempts reached or file reading failed, handle the error
    echo "Failed to read notification file after $max_attempts attempts.";
}

// ----------------------------------------------------------------------------------------
function notifications_mark_all_read() {
    mark_notification_as_read(null);
}

// ----------------------------------------------------------------------------------------
function get_unread_notifications() {
    $NOTIFICATION_API_FILE = get_notification_store_path();

    // Read existing notifications
    if (file_exists($NOTIFICATION_API_FILE) && is_readable($NOTIFICATION_API_FILE)) {
        $notifications = json_decode(file_get_contents($NOTIFICATION_API_FILE), true);

        if ($notifications !== null) {
            // Filter unread notifications
            $unread_notifications = array_filter($notifications, function($notification) {
                return $notification['read'] === 0;
            });

            // Return unread notifications as JSON
            header('Content-Type: application/json');
            echo json_encode(array_values($unread_notifications));
        } else {
            echo json_encode([]);
        }
    } else {
        echo json_encode([]);
    }
}


?>