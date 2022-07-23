<?php
$Pia_Graph_Device_Time = array();
$Pia_Graph_Device_All = array();
$Pia_Graph_Device_Online = array();
$Pia_Graph_Device_Down = array();
$Pia_Graph_Device_Arch = array();
$db = new SQLite3('../db/pialert.db');
$results = $db->query('SELECT * FROM Online_History ORDER BY Scan_Date DESC LIMIT 144');
while ($row = $results->fetchArray()) {
   $time_raw = explode(' ', $row['Scan_Date']);
   $time = explode(':', $time_raw[1]);
   array_push($Pia_Graph_Device_Time, $time[0].':'.$time[1]);
   array_push($Pia_Graph_Device_Down, $row['Down_Devices']);
   array_push($Pia_Graph_Device_All, $row['All_Devices']);
   array_push($Pia_Graph_Device_Online, $row['Online_Devices']);
   array_push($Pia_Graph_Device_Arch, $row['Archived_Devices']);
}
function pia_graph_devices_data($Pia_Graph_Array) {
  $Pia_Graph_Array_rev = array_reverse($Pia_Graph_Array);
  foreach ($Pia_Graph_Array_rev as $result) {
      echo "'".$result."'";
      echo ",";
  }
}
$db->close();
?>