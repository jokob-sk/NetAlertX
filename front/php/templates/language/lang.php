<?php

// ###################################
// ## Languages
// ###################################

$defaultLang = "en_us";
$allLanguages = ["en_us","es_es","de_de"];

global $db;

$result = $db->querySingle("SELECT Value FROM Settings WHERE Code_Name = 'UI_LANG'"); 
switch($result){
  case 'Spanish': $pia_lang_selected = 'es_es'; break;
  case 'German': $pia_lang_selected = 'de_de'; break;
  default: $pia_lang_selected = 'en_us'; break;
}

if (isset($pia_lang_selected) == FALSE or (strlen($pia_lang_selected) == 0)) {$pia_lang_selected = $defaultLang;}

//Language_Strings ("Language_Code", "String_Key", "String_Value", "Extra")
$result = $db->query("SELECT * FROM Language_Strings");  

// array 
$strings = array();
while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {   
  // Push row data      
  $strings[] = array(  'Language_Code'     => $row['Language_Code'],
                        'String_Key'       => $row['String_Key'],                        
                        'String_Value'     => $row['String_Value'],
                        'Extra'            => $row['Extra']
                      ); 
}

require dirname(__FILE__).'/../skinUI.php';
require dirname(__FILE__).'/en_us.php';
require dirname(__FILE__).'/de_de.php';
require dirname(__FILE__).'/es_es.php';

function lang($key)
{
  global $pia_lang_selected, $lang, $defaultLang, $strings;

  // get strings from the DB and append them to the ones from the files
  foreach ($strings as $string) 
  { 
    $lang[$string["Language_Code"]][$string["String_Key"]] = $string["String_Value"]; 
  }

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
