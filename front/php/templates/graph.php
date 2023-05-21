<?php

global $db;

$Pia_Graph_Device_Time = array();
$Pia_Graph_Device_All = array();
$Pia_Graph_Device_Online = array();
$Pia_Graph_Device_Down = array();
$Pia_Graph_Device_Arch = array();

$statusesToShow = "'online', 'offline', 'archived'";

$statQuery = $db->query("SELECT * FROM Settings WHERE Code_Name = 'UI_PRESENCE'");

while($r = $statQuery->fetchArray(SQLITE3_ASSOC))
{
  $statusesToShow =  $r['Value'];
}

$results = $db->query('SELECT * FROM Online_History ORDER BY Scan_Date DESC LIMIT 144');

while ($row = $results->fetchArray()) 
{
    $time_raw = explode(' ', $row['Scan_Date']);
    $time = explode(':', $time_raw[1]);
    array_push($Pia_Graph_Device_Time, $time[0].':'.$time[1]);
    
    //  Offline
    if(strpos($statusesToShow, 'offline') !== false) 
    {
      array_push($Pia_Graph_Device_Down, $row['Down_Devices']);
    }

    //  All
    array_push($Pia_Graph_Device_All, $row['All_Devices']);

    // Online
    if(strpos($statusesToShow, 'online') !== false)
    {
      array_push($Pia_Graph_Device_Online, $row['Online_Devices']);
    }
    
    // Archived
    if(strpos($statusesToShow, 'archived') !== false)
    {   
      array_push($Pia_Graph_Device_Arch, $row['Archived_Devices']);
    }
}
function pia_graph_devices_data($Pia_Graph_Array) {
  $Pia_Graph_Array_rev = array_reverse($Pia_Graph_Array);
  foreach ($Pia_Graph_Array_rev as $result) {
      echo "'".$result."'";
      echo ",";
  }
}
