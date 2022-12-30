<?php

// ###################################
// ## Languages
// ###################################

$defaultLang = "en_us";

if(!isset($_COOKIE["language"])) {
  $pia_lang_selected = $defaultLang;
} else {   
  $pia_lang_selected = $_COOKIE["language"];
}

if (isset($pia_lang_selected) == FALSE or (strlen($pia_lang_selected) == 0)) {$pia_lang_selected = defaultLang;}

require 'en_us.php';
require 'de_de.php';
require 'es_es.php';

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
?>