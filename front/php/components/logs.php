<?php

require '../server/init.php';

// Function to render the log area component
function renderLogArea($params) {
    $fileName = isset($params['fileName']) ? $params['fileName'] : '';
    $filePath = isset($params['filePath']) ? $params['filePath'] : '';
    $textAreaCssClass = isset($params['textAreaCssClass']) ? $params['textAreaCssClass'] : '';
    $buttons = isset($params['buttons']) ? $params['buttons'] : [];
    $content = "";

    if(filesize($filePath) > 2000000) {
        $content =  file_get_contents($filePath, false, null, -2000000); 
    } else {
        $content = file_get_contents($filePath);
    }    

    // Render the log area HTML
    $html = '
        <div class="log-area box box-solid box-primary">
            <div class="row logs-row col-sm-12 col-xs-12">
                <textarea id="app_log" class="' . $textAreaCssClass . '" cols="70" rows="10" wrap="off" readonly>'
                    .$content.
                '</textarea>
            </div>
            <div class="row logs-row">
                <div class="log-file col-sm-8 col-xs-12">' . $fileName . '
                    <div class="logs-size">' . number_format((filesize($filePath) / 1000000), 2, ",", ".") . ' MB
                        <span class="span-padding"><a href="' . $filePath . '" target="_blank"><i class="fa fa-download"></i></a></span>
                    </div>
                </div>
                <div class="col-sm-4 col-xs-12">
    ';

    // Render each button
    foreach ($buttons as $button) {
        $labelStringCode = isset($button['labelStringCode']) ? $button['labelStringCode'] : '';
        $event = isset($button['event']) ? $button['event'] : '';

        $html .= '
            <div class="col-sm-6 col-xs-6">
                <button class="btn btn-primary" onclick="' . $event . '">' . lang($labelStringCode) . '</button>
            </div>
        ';
    }

    $html .= '
                </div>
            </div>
        </div>
    ';

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
