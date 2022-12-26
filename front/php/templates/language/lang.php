<?php

// ###################################
// ## Languages
// ###################################

if(!isset($_COOKIE["language"])) {
  $pia_lang_selected = "en_us";
} else {   
  $pia_lang_selected = $_COOKIE["language"];
}

if (isset($pia_lang_selected) == FALSE or (strlen($pia_lang_selected) == 0)) {$pia_lang_selected = 'en_us';}

require 'en_us.php';
require 'de_de.php';
require 'es_es.php';

function lang($key)
{
  global $pia_lang_selected, $lang ;

  // try to get the selected language translation
  $temp = $lang[$pia_lang_selected][$key];

  if(isset($temp) == FALSE)
  {    
    // if not found, use English
    $temp = $lang[$pia_lang_selected]["en_us"];

    // echo $temp;
    if(isset($temp) == FALSE)
    {
      // if not found, in English, use placeholder
      $temp = "String not found";
    }
  }

  // echo $temp;
  
  return $temp;
}
?>