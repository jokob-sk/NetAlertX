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
    <section class="content">


    <div class="col-xs-12">
      <div class="pull-right">
          <button type="button" class="btn btn-default pa-btn pa-btn-delete"  style="margin-left:0px;"
            id="btnDeleteMAC"   onclick="askDeleteDevicesWithEmptyMACs()">   Delete Devices with empty MACs </button>     
      </div>
   
      <div class="pull-right">
          <button type="button" class="btn btn-default pa-btn pa-btn-delete"  style="margin-left:0px;"
            id="btnDeleteMAC"   onclick="askDeleteAllDevices()">   Delete All Devices </button>     
      </div>
      <!-- <div class="pull-right">
          <button type="button" class="btn btn-default pa-btn pa-btn-create"  style="margin-left:0px;"
            id="btnDelete"   onclick="askRunScan1min()">   Run 1 min scan now</button>     
      </div>

      <div class="pull-right">
          <button type="button" class="btn btn-default pa-btn pa-btn-create"  style="margin-left:0px;"
            id="btnDelete"   onclick="askRunScan15min()">   Run 15 min scan now</button>     
      </div>

      <div class="pull-right">
          <button type="button" class="btn btn-default pa-btn pa-btn-create"  style="margin-left:0px;"
            id="btnBackup"   onclick="askCreateBackupDB()"> Backup DB </button>     
      </div>
      <div class="pull-right">
          <button type="button" class="btn btn-default pa-btn pa-btn-delete"  style="margin-left:0px;"
            id="btnRestore"   onclick="askRestoreBackupDB()"> Restore DB </button>     
      </div> -->
   
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
  // Ask delete device 

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
  // Ask delete device 

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


// Run ad-hoc scans

function askRunScan1min () {
  // Ask delete device

  showModalWarning('Scan 1 min now', 'This runs the 1 min scan sequence',
    'Cancel', 'Scan', 'runScan1min');
}


function runScan1min()
{ 
  // Scan
  $.get('php/server/devices.php?action=runScan1min', function(msg) {
    showMessage (msg);
  });
}

function askRunScan15min () {
  // Ask delete device

  showModalWarning('Scan 15 min now', 'This runs the 15 min scan sequence',
    'Cancel', 'Scan', 'runScan15min');
}


function runScan15min()
{ 
  // Scan
  $.get('php/server/devices.php?action=runScan15min', function(msg) {
    showMessage (msg);
  });
}


// DB backup

function askCreateBackupDB () {
  // Ask delete device

  showModalWarning('Backup DB', 'This creates a pialert.db_bak file in the /config folder',
    'Cancel', 'Create', 'createBackupDB');
}


function createBackupDB()
{ 
  // Delete device
  $.get('php/server/devices.php?action=createBackupDB', function(msg) {
    showMessage (msg);
  });
}


// DB restore

function askRestoreBackupDB () {
  // Ask delete device

  showModalWarning('Restore DB', 'This restores a pialert.db_bak file from the /config folder',
    'Cancel', 'Restore', 'restoreBackupDB');
}


function restoreBackupDB()
{ 
  // Delete device
  $.get('php/server/devices.php?action=restoreBackupDB', function(msg) {
    showMessage (msg);
  });
}





</script>


