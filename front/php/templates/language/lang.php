<?php

// ###################################
// ## Languages
// ###################################

$defaultLang = "en_us";

global $db;

$result = $db->querySingle("SELECT Value FROM Settings WHERE Code_Name = 'UI_LANG'"); 
switch($result){
  case 'Spanish': $pia_lang_selected = 'es_es'; break;
  case 'German': $pia_lang_selected = 'de_de'; break;
  default: $pia_lang_selected = 'en_us'; break;
}

if (isset($pia_lang_selected) == FALSE or (strlen($pia_lang_selected) == 0)) {$pia_lang_selected = $defaultLang;}

require dirname(__FILE__).'/../skinUI.php';
require dirname(__FILE__).'/en_us.php';
require dirname(__FILE__).'/de_de.php';
require dirname(__FILE__).'/es_es.php';

function lang($key)
{
  global $pia_lang_selected, $lang, $defaultLang;

  // check if key exists in selected language
  if(array_key_exists($key, $lang[$pia_lang_selected]) == FALSE) 
  {
    // check if key exists in the default language if not available in the selected
    if (array_key_exists($key, $lang[$defaultLang]) == TRUE) 
    {
      // if found, use default language
      $temp = $lang[$defaultLang][$key];

    } else
    {
      // String not found in the default or selected language
      $temp = "String not found for key: ".$key;
    }
  } else
  {
    // use selected language translation
    $temp = $lang[$pia_lang_selected][$key];
  } 
    
  return $temp;
}
