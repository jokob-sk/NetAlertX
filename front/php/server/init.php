<?php
if(!file_exists(dirname(__FILE__).'/../../../config/settings.json')){
    $config = [
        'skin' => 'skin-blue',
        'columnsTable' => [
            "0","1","2","3","4","5","6","7","8","9","10","12","13","14","15","16","17"
        ],
        'numElementDevicesTable' => 50
    ];
    $fp = fopen(dirname(__FILE__).'/../../../config/settings.json', 'w');
    fwrite($fp, json_encode($config, true));
    fclose($fp);
    unset($config);
}
define('_CONFIG_', json_decode(file_get_contents(dirname(__FILE__).'/../../../config/settings.json'), true));


require dirname(__FILE__).'/../templates/timezone.php';
require dirname(__FILE__).'/db.php';
require dirname(__FILE__).'/util.php';
require dirname(__FILE__).'/../templates/language/lang.php';
