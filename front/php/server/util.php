<?php

//------------------------------------------------------------------------------
// Formatting data functions
//------------------------------------------------------------------------------
function formatDate ($date1) {
  return date_format (new DateTime ($date1) , 'Y-m-d   H:i');
}

function formatDateDiff ($date1, $date2) {
  return date_diff (new DateTime ($date1), new DateTime ($date2 ) )-> format ('%ad   %H:%I');
}

function formatDateISO ($date1) {
  return date_format (new DateTime ($date1),'c');
}

function formatEventDate ($date1, $eventType) {
  if (!empty ($date1) ) {
    $ret = formatDate ($date1);
  } elseif ($eventType == '<missing event>') {
    $ret = '<missing event>';
  } else {
    $ret = '<Still Connected>';
  }

  return $ret;
}

function formatIPlong ($IP) {
  return sprintf('%u', ip2long($IP) );
}


//------------------------------------------------------------------------------
// Others functions
//------------------------------------------------------------------------------
function getDateFromPeriod () {
  $period = $_REQUEST['period'];    
  return '"'. date ('Y-m-d', strtotime ('+1 day -'.$period) ) .'"';
}

function logServerConsole ($text) {
  $x = array();
  $y = $x['__________'. $text .'__________'];
}
    
?>
