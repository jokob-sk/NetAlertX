<?php

require '../server/init.php';

//------------------------------------------------------------------------------
// Check if authenticated
require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

function renderSmallBox($params) {
    $onclickEvent = isset($params['onclickEvent']) ? $params['onclickEvent'] : '';
    $color = isset($params['color']) ? $params['color'] : '';
    $headerId = isset($params['headerId']) ? $params['headerId'] : '';
    $headerStyle = isset($params['headerStyle']) ? $params['headerStyle'] : '';
    $labelLang = isset($params['labelLang']) ? $params['labelLang'] : '';
    $iconId = isset($params['iconId']) ? $params['iconId'] : '';
    $iconClass = isset($params['iconClass']) ? $params['iconClass'] : '';
    $dataValue = isset($params['dataValue']) ? $params['dataValue'] : '';

    return '
        <div class="col-lg-3 col-sm-6 col-xs-6">
            <a href="#" onclick="javascript: ' . htmlspecialchars($onclickEvent) . '">
                <div class="small-box ' . htmlspecialchars($color) . '">
                    <div class="inner">
                        <h3 id="' . htmlspecialchars($headerId) . '" style="' . htmlspecialchars($headerStyle) . '"> ' . htmlspecialchars($dataValue) . ' </h3>
                        <p class="infobox_label">' . lang(htmlspecialchars($labelLang)) . '</p>
                    </div>
                    <div class="icon">
                        <i id="' . htmlspecialchars($iconId) . '" class="' . htmlspecialchars($iconClass) . '"></i>
                    </div>
                </div>
            </a>
        </div>';
}

// Load default data from JSON file
$defaultDataFile = 'device_cards_defaults.json';
$defaultData = file_exists($defaultDataFile) ? json_decode(file_get_contents($defaultDataFile), true) : [];

// Decode raw JSON input from body
$requestBody = file_get_contents('php://input');
$data = json_decode($requestBody, true);

// Debugging logs
if (json_last_error() !== JSON_ERROR_NONE) {
    error_log('JSON Decode Error: ' . json_last_error_msg());
    error_log('Raw body: ' . $requestBody);
    $data = null;
}

// Extract 'items' or fall back to default data
$items = isset($data['items']) ? $data['items'] : $defaultData;

// Generate HTML
$html = '<div class="row">';
foreach ($items as $item) {
    $html .= renderSmallBox($item);
}
$html .= '</div>';

// Output generated HTML
echo $html;
exit();
?>
