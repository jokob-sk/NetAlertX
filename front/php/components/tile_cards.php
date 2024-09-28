<?php

//------------------------------------------------------------------------------
// check if authenticated
require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

function renderInfobox($params) {
  $onclickEvent = isset($params['onclickEvent']) ? $params['onclickEvent'] : '';
  $color = isset($params['color']) ? $params['color'] : '';
  $title = isset($params['title']) ? $params['title'] : '';
  $label = isset($params['label']) ? $params['label'] : '';
  $icon = isset($params['icon']) ? $params['icon'] : '';

  return '
    <div class="tile col-lg-2 col-sm-4 col-xs-6">
      <a href="#" onclick="javascript: ' . htmlspecialchars($onclickEvent) . ';">
        <div class="small-box ' . htmlspecialchars($color) . '">
          <div class="inner">
            <h3>' . htmlspecialchars($title) . '</h3>
            <p class="infobox_label">' . htmlspecialchars($label) . '</p>
          </div>
          <div class="icon">
            <i class="fa ' . htmlspecialchars($icon) . ' text-aqua-40"></i>
          </div>
        </div>
      </a>
    </div>';
}

// Load default data from JSON file
$defaultDataFile = 'tile_cards_defaults.json';
$defaultData = file_exists($defaultDataFile) ? json_decode(file_get_contents($defaultDataFile), true) : [];

// Check if 'items' parameter exists and is valid JSON
$items = isset($_POST['items']) ? json_decode($_POST['items'], true) : [];

// Use default data if 'items' is not provided or cannot be decoded
if (empty($items)) {
  $items = $defaultData;
}

$html = '';
foreach ($items as $item) {
  $html .= renderInfobox($item);
}
echo $html;
exit();
?>
