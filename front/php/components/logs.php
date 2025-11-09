<?php

require '../server/init.php';

$logBasePath = rtrim(getenv('NETALERTX_LOG') ?: '/tmp/log', '/');

function resolveLogPath($path)
{
    global $logBasePath;

    if ($path === null || $path === '') {
        return $path;
    }

    $placeholder = '__NETALERTX_LOG__';
    if (strpos($path, $placeholder) === 0) {
        return $logBasePath . substr($path, strlen($placeholder));
    }

    return $path;
}

//------------------------------------------------------------------------------
// check if authenticated
require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

// Function to render the log area component
function renderLogArea($params) {
    global $logBasePath;

    $fileName = isset($params['fileName']) ? $params['fileName'] : '';
    $filePath = isset($params['filePath']) ? $params['filePath'] : '';
    $textAreaCssClass = isset($params['textAreaCssClass']) ? $params['textAreaCssClass'] : '';
    $buttons = isset($params['buttons']) ? $params['buttons'] : [];
    $content = "";
    $fileSize = 0;

    $filePath = resolveLogPath($filePath);

    if (!is_file($filePath)) {
        $content = "";
        $fileSizeMb = 0.0;
    } elseif (filesize($filePath) > 2000000) {
        $content = file_get_contents($filePath, false, null, -2000000);
        $fileSizeMb = filesize($filePath) / 1000000;
    } else {
        $content = file_get_contents($filePath);
        $fileSizeMb = filesize($filePath) / 1000000;
    }

    // Prepare the download button HTML if filePath resides under the active log base path
    $downloadButtonHtml = '';
    $logPrefix = $logBasePath . '/';
    if ($logPrefix !== '/' && strpos($filePath, $logPrefix) === 0) {
        $downloadName = basename($filePath);
        $downloadButtonHtml = '
            <span class="span-padding">
                <a href="' . htmlspecialchars('/php/server/query_logs.php?file=' . rawurlencode($downloadName)) . '" target="_blank">
                    <i class="fa fa-download"></i>
                </a>
            </span>';
    }

    // Prepare buttons HTML
    $buttonsHtml = '';
    $totalButtons = count($buttons);
    $colClass = $totalButtons > 0 ? (12 / $totalButtons) : 12;

    foreach ($buttons as $button) {
        $labelStringCode = isset($button['labelStringCode']) ? $button['labelStringCode'] : '';
        $event = isset($button['event']) ? $button['event'] : '';

        $buttonsHtml .= '
            <div class="button-wrap col-sm-' . $colClass . ' col-xs-' . $colClass . '">
                <button class="btn btn-primary col-sm-12 col-xs-12" onclick="' . htmlspecialchars($event) . '">' . lang($labelStringCode) . '</button>
            </div>';
    }

    // Render HTML
    $html = '
        <div class="log-area box box-solid box-primary">
            <div class="row logs-row col-sm-12 col-xs-12">
                <textarea class="' . htmlspecialchars($textAreaCssClass) . '" cols="70" rows="20" wrap="off" readonly>'
                    . htmlspecialchars($content) .
                '</textarea>
            </div>
            <div class="row logs-row">
                <div class="log-file col-sm-6 col-xs-12">' . htmlspecialchars($filePath) . '
                    <div class="logs-size">' . number_format($fileSizeMb, 2, ",", ".") . ' MB'
                    . $downloadButtonHtml .
                    '</div>
                </div>
                <div class="col-sm-6 col-xs-12">'
                    . $buttonsHtml .
                '</div>
            </div>
        </div>';

    return $html;
}

// Load default data from JSON file
$defaultDataFile = 'logs_defaults.json';
$defaultData = file_exists($defaultDataFile) ? json_decode(file_get_contents($defaultDataFile), true) : [];

// Check if JSON data is submitted via POST
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['items'])) {
    $items = json_decode($_POST['items'], true);
} else {
    $items = $defaultData;
}

// Render the log areas with the retrieved or default data
$html = '';
foreach ($items as $item) {
    $html .= renderLogArea($item);
}

echo $html;
exit();
?>
