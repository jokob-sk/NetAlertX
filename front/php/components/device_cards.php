<?php

require '../server/init.php';

//------------------------------------------------------------------------------
// check if authenticated
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
            <h3 id="' . htmlspecialchars($headerId) . '" style="' . htmlspecialchars($headerStyle) . '"> '.$dataValue.' </h3>
            <p class="infobox_label">'.lang(htmlspecialchars($labelLang)).'</p>
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

// Check if 'items' parameter exists and is valid JSON
$items = isset($_POST['items']) ? json_decode($_POST['items'], true) : [];

// Use default data if 'items' is not provided or cannot be decoded
if (empty($items)) {
  $items = $defaultData;
}

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
