<?php
//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  devices.php - Front module. Server side. Manage Devices
//------------------------------------------------------------------------------
//  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
//  jokob-sk 2022        jokob.sk@gmail.com        GNU GPLv3
//------------------------------------------------------------------------------


//------------------------------------------------------------------------------
?>

<?php
  require 'php/templates/header.php';
?>
<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
         Maintenance tools
      </h1>
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content" style="min-height: 400px;">


  <?php

$pia_db = str_replace('front', 'db', getcwd()).'/pialert.db';
//echo $pia_db;
$pia_db_size = number_format(filesize($pia_db),0,",",".") . ' Byte';
//echo $pia_db_size;
$pia_db_mod = date ("F d Y H:i:s", filemtime($pia_db));

$execstring = 'ps -f -u root | grep "sudo arp-scan" 2>&1';
$pia_arpscans = "";
exec($execstring, $pia_arpscans);

$execstring = 'ps -f -u pi | grep "nmap" 2>&1';
$pia_nmapscans = "";
exec($execstring, $pia_nmapscans);

$Pia_Archive_Path = str_replace('front', 'db', getcwd()).'/';
$Pia_Archive_count = 0;
$files = glob($Pia_Archive_Path . "*.zip");
if ($files){
 $Pia_Archive_count = count($files);
}


  ?>

<div class="table">
<div class="table-row">
   <div class="table-cell">Database-Path</div>
   <div class="table-cell"><?php echo $pia_db;?></div>
</div>
<div class="table-row">
   <div class="table-cell">Database-Size</div>
   <div class="table-cell"><?php echo $pia_db_size;?></div>
</div>
<div class="table-row">
   <div class="table-cell">last Modification</div>
   <div class="table-cell"><?php echo $pia_db_mod;?></div>
</div>
<div class="table-row">
   <div class="table-cell">DB Backup</div>
   <div class="table-cell"><?php echo $Pia_Archive_count.' Backups where found';?></div>
</div>
<div class="table-row">
   <div class="table-cell">Scan Status (arp)</div>
   <div class="table-cell"><?php echo sizeof($pia_arpscans);?> scan(s) currently running</div>
</div>
<div class="table-row">
   <div class="table-cell">Scan Status (nmap)</div>
   <div class="table-cell"><?php echo sizeof($pia_nmapscans);?> scan(s) currently running</div>
</div>
</div>


    <div class="col-xs-12" style="text-align:center; padding-top: 10px; margin-bottom: 50px;">

          <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteMAC" style="border-top: solid 3px #dd4b39;" onclick="askDeleteDevicesWithEmptyMACs()">Delete Devices with empty MACs</button>

          <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteMAC" style="border-top: solid 3px #dd4b39;" onclick="askDeleteAllDevices()">Delete All Devices</button>

          <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteUnknown" style="border-top: solid 3px #dd4b39;" onclick="askDeleteUnknown()">Delete (unknown) Devices</button>

          <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteEvents" style="border-top: solid 3px #dd4b39;" onclick="askDeleteEvents()">Delete all Events (Reset Presence)</button>

          <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnPiaBackupDBtoArchive" style="border-top: solid 3px #dd4b39;" onclick="askPiaBackupDBtoArchive()">Execute DB Backup</button>

    </div>

    <!-- ----------------------------------------------------------------------- -->

</section>

    <!-- /.content -->
  </div>
  <!-- /.content-wrapper -->


<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>


<script>

// delete devices with emty macs

function askDeleteDevicesWithEmptyMACs () {
  // Ask 
  showModalWarning('Delete Devices', 'Are you sure you want to delete all devices with empty MAC addresses?<br>(maybe you prefer to archive it)',
    'Cancel', 'Delete', 'deleteDevicesWithEmptyMACs');
}


function deleteDevicesWithEmptyMACs()
{ 
  // Delete device
  $.get('php/server/devices.php?action=deleteAllWithEmptyMACs', function(msg) {
    showMessage (msg);
  });
}

// delete all devices 
function askDeleteAllDevices () {
  // Ask 
  showModalWarning('Delete Devices', 'Are you sure you want to delete all devices?',
    'Cancel', 'Delete', 'deleteAllDevices');
}


function deleteAllDevices()
{ 
  // Delete device
  $.get('php/server/devices.php?action=deleteAllDevices', function(msg) {
    showMessage (msg);
  });
}

// delete all (unknown) devices 
function askDeleteUnknown () {
  // Ask 
  showModalWarning('Delete (unknown) Devices', 'Are you sure you want to delete all (unknown) devices?',
    'Cancel', 'Delete', 'deleteUnknownDevices');
}


function deleteUnknownDevices()
{ 
  // Execute
  $.get('php/server/devices.php?action=deleteUnknownDevices', function(msg) {
    showMessage (msg);
  });
}

// delete all Events 
function askDeleteEvents () {
  // Ask 
  showModalWarning('Delete Events', 'Are you sure you want to delete all Events?',
    'Cancel', 'Delete', 'deleteEvents');
}


function deleteEvents()
{ 
  // Execute
  $.get('php/server/devices.php?action=deleteEvents', function(msg) {
    showMessage (msg);
  });
}


// Backup DB to Archive 
function askPiaBackupDBtoArchive () {
  // Ask 
  showModalWarning('DB Backup', 'Are you sure you want to exectute the the DB Backup? Be sure that no scan is currently running.',
    'Cancel', 'Run Backup', 'PiaBackupDBtoArchive');
}


function PiaBackupDBtoArchive()
{ 
  // Execute
  $.get('php/server/devices.php?action=PiaBackupDBtoArchive', function(msg) {
    showMessage (msg);
  });
}


</script>


