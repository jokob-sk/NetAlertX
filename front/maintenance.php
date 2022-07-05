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

// Language selector config ----------------------------------------------------
//
// For security reasons, new language files must be entered into this array.
// The files in the language directory are compared with this array and only 
// then accepted.
//
$pia_installed_langs = array('en_us', 
                             'de_de');
//
// In addition to this, the language must also be added to the select tag in 
// line 235. Later, the whole thing may become dynamic.

// Skin selector config ----------------------------------------------------
//
// For security reasons, new language files must be entered into this array.
// The files in the language directory are compared with this array and only 
// then accepted.
//
$pia_installed_skins = array('skin-black-light', 
                             'skin-black', 
                             'skin-blue-light', 
                             'skin-blue', 
                             'skin-green-light', 
                             'skin-green', 
                             'skin-purple-light', 
                             'skin-purple', 
                             'skin-red-light', 
                             'skin-red', 
                             'skin-yellow-light', 
                             'skin-yellow');
  

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
         <?php echo $pia_lang['Maintenance_Title'];?>
      </h1>
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">


  <?php

// Size and last mod of DB ------------------------------------------------------

$pia_db = str_replace('front', 'db', getcwd()).'/pialert.db';
$pia_db_size = number_format((filesize($pia_db) / 1000000),2,",",".") . ' MB';
$pia_db_mod = date ("F d Y H:i:s", filemtime($pia_db));

// Pause Arp Scan ---------------------------------------------------------------

if (!file_exists('../db/setting_stoparpscan')) {
  $execstring = 'ps -f -u root | grep "sudo arp-scan" 2>&1';
  $pia_arpscans = "";
  exec($execstring, $pia_arpscans);
  $pia_arpscans_result = sizeof($pia_arpscans).' '.$pia_lang['Maintenance_arp_status_on'];
} else {
  $pia_arpscans_result = '<span style="color:red;">arp-Scan '.$pia_lang['Maintenance_arp_status_off'] .'</span>';
}

// Count and Calc Backups -------------------------------------------------------

$Pia_Archive_Path = str_replace('front', 'db', getcwd()).'/';
$Pia_Archive_count = 0;
$Pia_Archive_diskusage = 0;
$files = glob($Pia_Archive_Path."*.zip");
if ($files){
 $Pia_Archive_count = count($files);
}
foreach ($files as $result) {
    $Pia_Archive_diskusage = $Pia_Archive_diskusage + filesize($result);
}
$Pia_Archive_diskusage = number_format(($Pia_Archive_diskusage / 1000000),2,",",".") . ' MB';

// Find latest Backup for restore -----------------------------------------------

$latestfiles = glob($Pia_Archive_Path."*.zip");
natsort($latestfiles);
$latestfiles = array_reverse($latestfiles,False);
$latestbackup = $latestfiles[0];
$latestbackup_date = date ("Y-m-d H:i:s", filemtime($latestbackup));

// Skin selector -----------------------------------------------------------------

if (submit && isset($_POST['skinselector_set'])) {
  $pia_skin_set_dir = '../db/';
  $pia_skin_selector = htmlspecialchars($_POST['skinselector']);
  if (in_array($pia_skin_selector, $pia_installed_skins)) {
    foreach ($pia_installed_skins as $file) {
      unlink ($pia_skin_set_dir.'/setting_'.$file);
    }
    foreach ($pia_installed_skins as $file) {
      if (file_exists($pia_skin_set_dir.'/setting_'.$file)) {
          $pia_skin_error = True;
          break;
      } else {
          $pia_skin_error = False;
      }
    }
    if ($pia_skin_error == False) {
      $testskin = fopen($pia_skin_set_dir.'setting_'.$pia_skin_selector, 'w');
      $pia_skin_test = '';
      echo("<meta http-equiv='refresh' content='1'>"); 
    } else {
      $pia_skin_test = '';
      echo("<meta http-equiv='refresh' content='1'>");
    }    
  }
}

// Language selector -----------------------------------------------------------------

if (submit && isset($_POST['langselector_set'])) {
  $pia_lang_set_dir = '../db/';
  $pia_lang_selector = htmlspecialchars($_POST['langselector']);
  if (in_array($pia_lang_selector, $pia_installed_langs)) {
    foreach ($pia_installed_langs as $file) {
      unlink ($pia_lang_set_dir.'/setting_language_'.$file);
    }
    foreach ($pia_installed_langs as $file) {
      if (file_exists($pia_lang_set_dir.'/setting_language_'.$file)) {
          $pia_lang_error = True;
          break;
      } else {
          $pia_lang_error = False;
      }
    }
    if ($pia_lang_error == False) {
      $testlang = fopen($pia_lang_set_dir.'setting_language_'.$pia_lang_selector, 'w');
      $pia_lang_test = '';
      echo("<meta http-equiv='refresh' content='1'>"); 
    } else {
      $pia_lang_test = '';
      echo("<meta http-equiv='refresh' content='1'>");
    }    
  }
}
?>

<div class="db_info_table">
    <div class="db_info_table_row">
        <div class="db_info_table_cell" style="min-width: 140px"><?php echo $pia_lang['Maintenance_database_path'];?></div>
        <div class="db_info_table_cell">
            <?php echo $pia_db;?>
        </div>
    </div>
    <div class="db_info_table_row">
        <div class="db_info_table_cell"><?php echo $pia_lang['Maintenance_database_size'];?></div>
        <div class="db_info_table_cell">
            <?php echo $pia_db_size;?>
        </div>
    </div>
    <div class="db_info_table_row">
        <div class="db_info_table_cell"><?php echo $pia_lang['Maintenance_database_lastmod'];?></div>
        <div class="db_info_table_cell">
            <?php echo $pia_db_mod;?>
        </div>
    </div>
    <div class="db_info_table_row">
        <div class="db_info_table_cell"><?php echo $pia_lang['Maintenance_database_backup'];?></div>
        <div class="db_info_table_cell">
            <?php echo $Pia_Archive_count.' '.$pia_lang['Maintenance_database_backup_found'].' / '.$pia_lang['Maintenance_database_backup_total'].': '.$Pia_Archive_diskusage;?>
        </div>
    </div>
    <div class="db_info_table_row">
        <div class="db_info_table_cell"><?php echo $pia_lang['Maintenance_arp_status'];?></div>
        <div class="db_info_table_cell">
            <?php echo $pia_arpscans_result;?></div>
    </div>
</div>

<form method="post" action="maintenance.php">
<div class="db_info_table">
    <div class="db_info_table_row">
        <div class="db_info_table_cell" style="padding-left: 5px; height:50px; text-align:center; vertical-align: middle;">
            <div style="display: inline-block; margin-right: 10px;"><?php echo $pia_lang['Maintenance_themeselector_lable'];?>:</div>
            <div style="display: inline-block;">
                <select name="skinselector">
                    <option value=""><?php echo $pia_lang['Maintenance_themeselector_empty'];?></option>
                    <option value="skin-black-light">black light</option>
                    <option value="skin-black">black</option>
                    <option value="skin-blue-light">blue light</option>
                    <option value="skin-blue">blue</option>
                    <option value="skin-green-light">green light</option>
                    <option value="skin-green">green</option>
                    <option value="skin-purple-light">purple light</option>
                    <option value="skin-purple">purple</option>
                    <option value="skin-red-light">red light</option>
                    <option value="skin-red">red</option>
                    <option value="skin-yellow-light">yellow light</option>
                    <option value="skin-yellow">yellow</option>
                </select></div>
            <div style="display: inline-block;"><input type="submit" name="skinselector_set" value="Okay">
                <?php echo $pia_skin_test; ?>
            </div>
        </div>
    </div>
    <div class="db_info_table_row">
        <div class="db_info_table_cell" style="padding: 10px; height:40px; text-align:center; vertical-align: middle;">
            <?php echo $pia_lang['Maintenance_themeselector_text'];?>
        </div>
    </div>
</div>
</form>


<form method="post" action="maintenance.php">
<div class="db_info_table">
    <div class="db_info_table_row">
        <div class="db_info_table_cell" style="padding-left: 5px; height:50px; text-align:center; vertical-align: middle;">
            <div style="display: inline-block; margin-right: 10px;"><?php echo $pia_lang['Maintenance_lang_selector_lable'];?>:</div>
            <div style="display: inline-block;">
                <select name="langselector">
                    <option value=""><?php echo $pia_lang['Maintenance_lang_selector_empty'];?></option>
                    <option value="en_us"><?php echo $pia_lang['Maintenance_lang_en_us'];?></option>
                    <option value="de_de"><?php echo $pia_lang['Maintenance_lang_de_de'];?></option>
                </select></div>
            <div style="display: inline-block;"><input type="submit" name="langselector_set" value="Okay">
                <?php echo $pia_lang_test; ?>
            </div>
        </div>
    </div>
    <div class="db_info_table_row">
        <div class="db_info_table_cell" style="padding: 10px; height:40px; text-align:center; vertical-align: middle;">
            <?php echo $pia_lang['Maintenance_lang_selector_text'];?>
        </div>
    </div>
</div>
</form>




<div class="db_info_table">
    <div class="db_info_table_row">
        <div class="db_tools_table_cell_a" style="">
            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-green dbtools-button" id="btnPiaEnableDarkmode" style="border-top: solid 3px #00a65a;" onclick="askPiaEnableDarkmode()"><?php echo $pia_lang['Maintenance_Tool_darkmode'];?></button>
        </div>
        <div class="db_tools_table_cell_b" style=""><?php echo $pia_lang['Maintenance_Tool_darkmode_text'];?></div>
    </div>
    <div class="db_info_table_row">
        <div class="db_tools_table_cell_a">
            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-yellow dbtools-button" id="btnPiaToggleArpScan" style="border-top: solid 3px #ffd080;" onclick="askPiaToggleArpScan()"><?php echo $pia_lang['Maintenance_Tool_arpscansw'];?></button>
        </div>
        <div class="db_tools_table_cell_b" style=""><?php echo $pia_lang['Maintenance_Tool_arpscansw_text'];?></div>
    </div>
    <div class="db_info_table_row">
        <div class="db_tools_table_cell_a" style="">
            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteMAC" style="border-top: solid 3px #dd4b39;" onclick="askDeleteDevicesWithEmptyMACs()"><?php echo $pia_lang['Maintenance_Tool_del_empty_macs'];?></button>
        </div>
        <div class="db_tools_table_cell_b"><?php echo $pia_lang['Maintenance_Tool_del_empty_macs_text'];?></div>
    </div>
    <div class="db_info_table_row">
        <div class="db_tools_table_cell_a" style="">
            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteMAC" style="border-top: solid 3px #dd4b39;" onclick="askDeleteAllDevices()"><?php echo $pia_lang['Maintenance_Tool_del_alldev'];?></button>
        </div>
        <div class="db_tools_table_cell_b"><?php echo $pia_lang['Maintenance_Tool_del_alldev_text'];?></div>
    </div>
    <div class="db_info_table_row">
        <div class="db_tools_table_cell_a" style="">
            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteUnknown" style="border-top: solid 3px #dd4b39;" onclick="askDeleteUnknown()"><?php echo $pia_lang['Maintenance_Tool_del_unknowndev'];?></button>
        </div>
        <div class="db_tools_table_cell_b"><?php echo $pia_lang['Maintenance_Tool_del_unknowndev_text'];?></div>
    </div>
    <div class="db_info_table_row">
        <div class="db_tools_table_cell_a" style="">
            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteEvents" style="border-top: solid 3px #dd4b39;" onclick="askDeleteEvents()"><?php echo $pia_lang['Maintenance_Tool_del_allevents'];?></button>
        </div>
        <div class="db_tools_table_cell_b"><?php echo $pia_lang['Maintenance_Tool_del_allevents_text'];?></div>
    </div>
    <div class="db_info_table_row">
        <div class="db_tools_table_cell_a" style="">
            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnPiaBackupDBtoArchive" style="border-top: solid 3px #dd4b39;" onclick="askPiaBackupDBtoArchive()"><?php echo $pia_lang['Maintenance_Tool_backup'];?></button>
        </div>
        <div class="db_tools_table_cell_b"><?php echo $pia_lang['Maintenance_Tool_backup_text'];?></div>
    </div>
    <div class="db_info_table_row">
        <div class="db_tools_table_cell_a" style="">
            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnPiaRestoreDBfromArchive" style="border-top: solid 3px #dd4b39;" onclick="askPiaRestoreDBfromArchive()"><?php echo $pia_lang['Maintenance_Tool_restore'];?><br><?php echo $latestbackup_date;?></button>
        </div>
        <div class="db_tools_table_cell_b"><?php echo $pia_lang['Maintenance_Tool_restore_text'];?></div>
    </div>
</div>


<div style="width: 100%; height: 20px;"></div>
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
  showModalWarning('<?php echo $pia_lang['Maintenance_Tool_del_empty_macs_noti'];?>', '<?php echo $pia_lang['Maintenance_Tool_del_empty_macs_noti_text'];?>',
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
  showModalWarning('<?php echo $pia_lang['Maintenance_Tool_del_alldev_noti'];?>', '<?php echo $pia_lang['Maintenance_Tool_del_alldev_noti_text'];?>',
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
  showModalWarning('<?php echo $pia_lang['Maintenance_Tool_del_unknowndev_noti'];?>', '<?php echo $pia_lang['Maintenance_Tool_del_unknowndev_noti_text'];?>',
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
  showModalWarning('<?php echo $pia_lang['Maintenance_Tool_del_allevents_noti'];?>', '<?php echo $pia_lang['Maintenance_Tool_del_allevents_noti_text'];?>',
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
  showModalWarning('<?php echo $pia_lang['Maintenance_Tool_backup_noti'];?>', '<?php echo $pia_lang['Maintenance_Tool_backup_noti_text'];?>',
    'Cancel', 'Run Backup', 'PiaBackupDBtoArchive');
}
function PiaBackupDBtoArchive()
{ 
  // Execute
  $.get('php/server/devices.php?action=PiaBackupDBtoArchive', function(msg) {
    showMessage (msg);
  });
}


// Restore DB from Archive 
function askPiaRestoreDBfromArchive () {
  // Ask 
  showModalWarning('<?php echo $pia_lang['Maintenance_Tool_restore_noti'];?>', '<?php echo $pia_lang['Maintenance_Tool_restore_noti_text'];?>',
    'Cancel', 'Run Restore', 'PiaRestoreDBfromArchive');
}
function PiaRestoreDBfromArchive()
{ 
  // Execute
  $.get('php/server/devices.php?action=PiaRestoreDBfromArchive', function(msg) {
    showMessage (msg);
  });
}

// Restore DB from Archive 
function askPiaEnableDarkmode () {
  // Ask 
  showModalWarning('<?php echo $pia_lang['Maintenance_Tool_darkmode_noti'];?>', '<?php echo $pia_lang['Maintenance_Tool_darkmode_noti_text'];?>',
    'Cancel', 'Switch', 'PiaEnableDarkmode');
}
function PiaEnableDarkmode()
{ 
  // Execute
  $.get('php/server/devices.php?action=PiaEnableDarkmode', function(msg) {
    showMessage (msg);
  });
}

// Toggle the Arp-Scans 
function askPiaToggleArpScan () {
  // Ask 
  showModalWarning('<?php echo $pia_lang['Maintenance_Tool_arpscansw_noti'];?>', '<?php echo $pia_lang['Maintenance_Tool_arpscansw_noti_text'];?>',
    'Cancel', 'Switch', 'PiaToggleArpScan');
}
function PiaToggleArpScan()
{ 
  // Execute
  $.get('php/server/devices.php?action=PiaToggleArpScan', function(msg) {
    showMessage (msg);
  });
}

</script>


