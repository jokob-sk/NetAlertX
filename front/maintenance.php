<?php
#---------------------------------------------------------------------------------#
#  NetAlertX                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #  
#                                                                                 #
#  maintenance.php - Front module. Server side. Maintenance                       #
#---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
#---------------------------------------------------------------------------------#

 

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
        <i class="fa fa-wrench"></i>         
        <?= lang('Maintenance_Title');?>
      </h1>
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">


  <?php

// Size and last mod of DB ------------------------------------------------------

$pia_db = str_replace('front', 'db', getcwd()).'/app.db';
$pia_db_size = number_format((filesize($pia_db) / 1000000),2,",",".") . ' MB';
$pia_db_mod = date ("F d Y H:i:s", filemtime($pia_db));


// Count and Calc Backups -------------------------------------------------------

$Pia_Archive_Path = str_replace('front', 'db', getcwd()).'/';
$Pia_Archive_count = 0;
$Pia_Archive_diskusage = 0;
$files = glob($Pia_Archive_Path."appdb_*.zip");
if ($files){
 $Pia_Archive_count = count($files);
}
foreach ($files as $result) {
    $Pia_Archive_diskusage = $Pia_Archive_diskusage + filesize($result);
}
$Pia_Archive_diskusage = number_format(($Pia_Archive_diskusage / 1000000),2,",",".") . ' MB';

// Find latest Backup for restore -----------------------------------------------

$latestfiles = glob($Pia_Archive_Path."appdb_*.zip");
natsort($latestfiles);
$latestfiles = array_reverse($latestfiles,False);

$latestbackup = 'none';
$latestbackup_date = 'no backup';

if (count($latestfiles) > 0)
{
  $latestbackup = $latestfiles[0];
  $latestbackup_date = date ("Y-m-d H:i:s", filemtime($latestbackup));
}

// Table sizes -----------------------------------------------------------------

$tableSizesHTML = "";
                        
// Open a connection to the SQLite database
$db = new SQLite3($pia_db);

// Retrieve the table names from sqlite_master
$query = "SELECT name FROM sqlite_master WHERE type='table'";
$result = $db->query($query);

// Iterate over the tables and get the row counts
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $tableName = $row['name'];
    $query = "SELECT COUNT(*) FROM $tableName";
    $countResult = $db->querySingle($query);
    $tableSizesHTML = $tableSizesHTML . "$tableName (<b>$countResult</b>), ";
}

// Close the database connection
$db->close();
                            

?>

      <div class="row">
          <div class="col-md-12">
          <div class="box" id="Maintain-Status">
              <div class="box-header with-border">
                <h3 class="box-title">
                  <i class="fa fa-display"></i></i>         
                  <?= lang('Maintenance_Status');?>
                </h3>
              </div>
              <div class="box-body" style="padding-bottom: 5px;">
                <div class="db_info_table">
                    <div class="db_info_table_row">                      
                        <div class="db_info_table_cell" style="min-width: 140px"><?= lang('Maintenance_version');?>
                          <a href="https://github.com/jokob-sk/NetAlertX/blob/main/docs/VERSIONS.md" target="_blank"> <span><i class="fa fa-circle-question"></i></a><span>

                        </div>
                        <div class="db_info_table_cell">
                        <div class="version" id="version" data-build-time="<?php echo file_get_contents( "buildtimestamp.txt");?>"><?php echo '<span id="new-version-text" class="myhidden">' .lang('Maintenance_new_version').'</span>'.'<span id="current-version-text" class="myhidden">' .lang('Maintenance_current_version').'</span>';?></div>
                        </div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_info_table_cell" style="min-width: 140px"><?= lang('Maintenance_built_on');?></div>
                        <div class="db_info_table_cell">                               
                            <?php echo date("Y-m-d", ((int)file_get_contents( "buildtimestamp.txt")));?> 
                        </div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_info_table_cell" style="min-width: 140px"><?= lang('Maintenance_Running_Version');?></div>
                        <div class="db_info_table_cell">                               
                          <?php include 'php/templates/version.php'; ?> 
                        </div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_info_table_cell" style="min-width: 140px"><?= lang('Maintenance_database_path');?></div>
                        <div class="db_info_table_cell">
                            <?php echo $pia_db;?>
                        </div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_info_table_cell"><?= lang('Maintenance_database_size');?></div>
                        <div class="db_info_table_cell">
                            <?php echo $pia_db_size;?>
                        </div>                        
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_info_table_cell"><?= lang('Maintenance_database_rows');?></div>
                        <div class="db_info_table_cell">
                            <?php echo $tableSizesHTML;?>
                        </div>                        
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_info_table_cell"><?= lang('Maintenance_database_lastmod');?></div>
                        <div class="db_info_table_cell">
                            <?php echo $pia_db_mod;?>
                        </div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_info_table_cell"><?= lang('Maintenance_database_backup');?></div>
                        <div class="db_info_table_cell">
                            <?php echo $Pia_Archive_count.' '.lang('Maintenance_database_backup_found').' / '.lang('Maintenance_database_backup_total').': '.$Pia_Archive_diskusage;?>
                        </div>
                    </div>                    
                </div>                
              </div>
              <!-- /.box-body -->
            </div>
          </div>
      </div>

    <div class="nav-tabs-custom">
    <ul class="nav nav-tabs">
        <li class="active">
          <a id="tab_DBTools_id" href="#tab_DBTools" data-toggle="tab">
            <i class="fa fa-toolbox"></i> 
            <?= lang('Maintenance_Tools_Tab_Tools');?>
          </a>
        </li>
        <li>
          <a id="tab_BackupRestore_id" href="#tab_BackupRestore" data-toggle="tab">
            <i class="fa fa-file-shield"></i> 
            <?= lang('Maintenance_Tools_Tab_BackupRestore');?>
          </a>
        </li>
        <li>
          <a id="tab_Logging_id" href="#tab_Logging" data-toggle="tab">
            <i class="fa fa-triangle-exclamation"></i> 
            <?= lang('Maintenance_Tools_Tab_Logging');?>
          </a>
        </li>
        <li>
          <a id="tab_multiEdit_id" href="#tab_multiEdit" data-toggle="tab">
            <i class="fa fa-pencil pointer" ></i>  
            <?= lang('Device_MultiEdit');?>
          </a>
        </li>
    </ul>
    <div class="tab-content">
        <div class="tab-pane active" id="tab_DBTools">
                <div class="db_info_table">
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteMAC" onclick="askDeleteDevicesWithEmptyMACs()"><?= lang('Maintenance_Tool_del_empty_macs');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_del_empty_macs_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteMAC" onclick="askDeleteAllDevices()"><?= lang('Maintenance_Tool_del_alldev');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_del_alldev_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteUnknown" onclick="askDeleteUnknown()"><?= lang('Maintenance_Tool_del_unknowndev');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_del_unknowndev_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteEvents" onclick="askDeleteEvents()"><?= lang('Maintenance_Tool_del_allevents');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_del_allevents_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteEvents30" onclick="askDeleteEvents30()"><?= lang('Maintenance_Tool_del_allevents30');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_del_allevents30_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnDeleteActHistory" onclick="askDeleteActHistory()"><?= lang('Maintenance_Tool_del_ActHistory');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_del_ActHistory_text');?></div>
                    </div>
                </div>
        </div>
        <div class="tab-pane" id="tab_BackupRestore">
                <div class="db_info_table">
                  <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn bg-green dbtools-button" id="btnExportCSV" onclick="ExportCSV()"><?= lang('Maintenance_Tool_ExportCSV');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_ExportCSV_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnImportCSV" onclick="askImportCSV()"><?= lang('Maintenance_Tool_ImportCSV');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_ImportCSV_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnImportPastedCSV" onclick="askImportPastedCSV()"><?= lang('Maintenance_Tool_ImportPastedCSV');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_ImportPastedCSV_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn bg-green dbtools-button" id="btnPiaBackupDBtoArchive" onclick="askPiaBackupDBtoArchive()"><?= lang('Maintenance_Tool_backup');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_backup_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnPiaRestoreDBfromArchive" onclick="askPiaRestoreDBfromArchive()"><?= lang('Maintenance_Tool_restore');?><br><?php echo $latestbackup_date;?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_restore_text');?></div>
                    </div>
                    <div class="db_info_table_row">
                        <div class="db_tools_table_cell_a" >
                            <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red dbtools-button" id="btnPiaPurgeDBBackups" onclick="askPiaPurgeDBBackups()"><?= lang('Maintenance_Tool_purgebackup');?></button>
                        </div>
                        <div class="db_tools_table_cell_b"><?= lang('Maintenance_Tool_purgebackup_text');?></div>
                    </div>
                 </div>
        </div>
        <!-- ---------------------------Logging-------------------------------------------- -->
        <div class="tab-pane" id="tab_Logging">
          <div class="container">
            <div class="row actions">
              <div class="col-sm-2">
                <div class="form-check toggle">
                  <label class="form-check-label pointer" for="logsAutoRefresh">
                    <input class="form-check-input" type="checkbox" id="logsAutoRefresh" onchange="toggleAutoRefresh()" />
                    Auto-refresh
                  </label>
                </div>
              </div>
              <div class="col-sm-2">
                <div class="form-check  toggle">
                  <label class="form-check-label pointer" for="logsAutoScroll">
                    <input class="form-check-input" type="checkbox" checked id="logsAutoScroll" />
                    Auto-scroll
                  </label>
                </div>
              </div>
              <div class="col-sm-8">
                <div class="form-inline toggle">                  
                  <input class="form-control" type="text" id="logsFilter" oninput="applyFilter()" placeholder="Filter lines with text..." />
                </div>
              </div>
            </div>
          </div>
          <div class="db_info_table">
            
            <div id="logsPlc"></div>                                
          </div>
        </div>
        <!-- ---------------------------Bulk edit -------------------------------------------- -->
        <div class="tab-pane" id="tab_multiEdit">
            <div class="db_info_table">
                <div class="box box-solid">
                    <?php
                      require 'multiEditCore.php';
                    ?>

                </div>
            </div>
          </div>

        </div>
        <!-- ------------------------------------------------------------------------------ -->

      </div>

      <div class="box-body" style="text-align: center;">
        <h5 class="text-aqua" style="font-size: 16px;">
          <span id="lastCommit">
           
          </span>
          <span id="lastDockerUpdate">
           
          </span>          
      </h5>
  </div>
      
      
</div>

</section>

    <!-- /.content -->
    <?php
      require 'php/templates/footer.php';
    ?>
  </div>
  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->



<script>

var emptyArr = ['undefined', "", undefined, null];
var selectedTab                 = 'tab_DBTools_id';

initializeTabs();

// -----------------------------------------------------------
// delete devices with emty macs
function askDeleteDevicesWithEmptyMACs () {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_del_empty_macs_noti');?>', '<?= lang('Maintenance_Tool_del_empty_macs_noti_text');?>',
    'Cancel', 'Delete', 'deleteDevicesWithEmptyMACs');
}
// -----------------------------------------------------------
function deleteDevicesWithEmptyMACs()
{ 
  // Delete device
  $.get('php/server/devices.php?action=deleteAllWithEmptyMACs', function(msg) {
    showMessage (msg);
    write_notification(`[Maintenance] All devices witout a Mac manually deleted`, 'info')
  });
}

// -----------------------------------------------------------
// delete all devices 
function askDeleteAllDevices () {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_del_alldev_noti');?>', '<?= lang('Maintenance_Tool_del_alldev_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Delete');?>', 'deleteAllDevices');
}
// -----------------------------------------------------------
function deleteAllDevices()
{ 
  // Delete device
  $.get('php/server/devices.php?action=deleteAllDevices', function(msg) {
    showMessage (msg);
    write_notification(`[Maintenance] All devices manually deleted`, 'info')
  });
}

// -----------------------------------------------------------
// delete all (unknown) devices 
function askDeleteUnknown () {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_del_unknowndev_noti');?>', '<?= lang('Maintenance_Tool_del_unknowndev_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Delete');?>', 'deleteUnknownDevices');
}
// -----------------------------------------------------------
function deleteUnknownDevices()
{ 
  // Execute
  $.get('php/server/devices.php?action=deleteUnknownDevices', function(msg) {
    showMessage (msg);
    write_notification(`[Maintenance] Unknown devices manually deleted`, 'info')
  });
}

// -----------------------------------------------------------
// delete all Events 
function askDeleteEvents () {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_del_allevents_noti');?>', '<?= lang('Maintenance_Tool_del_allevents_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Delete');?>', 'deleteEvents');
}
// -----------------------------------------------------------
function deleteEvents()
{ 
  // Execute
  $.get('php/server/devices.php?action=deleteEvents', function(msg) {
    showMessage (msg);
    write_notification(`[Maintenance] Events manually deleted (all)`, 'info')
  });
}

// -----------------------------------------------------------
// delete all Events older than 30 days
function askDeleteEvents30 () {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_del_allevents30_noti');?>', '<?= lang('Maintenance_Tool_del_allevents30_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Delete');?>', 'deleteEvents30');
}
// -----------------------------------------------------------
function deleteEvents30()
{ 
  // Execute
  $.get('php/server/devices.php?action=deleteEvents30', function(msg) {
    showMessage (msg);
    write_notification(`[Maintenance] Events manually deleted (last 30 days kep)`, 'info')
  });
}

// -----------------------------------------------------------
// delete History 
function askDeleteActHistory () {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_del_ActHistory_noti');?>', '<?= lang('Maintenance_Tool_del_ActHistory_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Delete');?>', 'deleteActHistory');
}
function deleteActHistory()
{ 
  // Execute
  $.get('php/server/devices.php?action=deleteActHistory', function(msg) {
    showMessage (msg);
  });
}

// -----------------------------------------------------------
// Backup DB to Archive 
function askPiaBackupDBtoArchive () {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_backup_noti');?>', '<?= lang('Maintenance_Tool_backup_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Backup');?>', 'PiaBackupDBtoArchive');
}
function PiaBackupDBtoArchive()
{ 
  // Execute
  $.get('php/server/devices.php?action=PiaBackupDBtoArchive', function(msg) {
    showMessage (msg);
  });
}

// -----------------------------------------------------------
// Restore DB from Archive 
function askPiaRestoreDBfromArchive () {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_restore_noti');?>', '<?= lang('Maintenance_Tool_restore_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Restore');?>', 'PiaRestoreDBfromArchive');
}
function PiaRestoreDBfromArchive()
{ 
  // Execute
  $.get('php/server/devices.php?action=PiaRestoreDBfromArchive', function(msg) {
    showMessage (msg);
  });
}

// -----------------------------------------------------------
// Purge Backups 
function askPiaPurgeDBBackups() {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_purgebackup_noti');?>', '<?= lang('Maintenance_Tool_purgebackup_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Purge');?>', 'PiaPurgeDBBackups');
}
function PiaPurgeDBBackups()
{ 
  // Execute
  $.get('php/server/devices.php?action=PiaPurgeDBBackups', function(msg) {
    showMessage (msg);
  });
}

// -----------------------------------------------------------
// Restart Backend Python Server

function askRestartBackend() {
  // Ask 
  showModalWarning('<?= lang('Maint_RestartServer');?>', '<?= lang('Maint_Restart_Server_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Maint_RestartServer');?>', 'restartBackend');
}

// -----------------------------------------------------------
function restartBackend() {

  modalEventStatusId = 'modal-message-front-event'
  
  // Execute
  $.ajax({
      method: "POST",
      url: "php/server/util.php",
      data: { function: "addToExecutionQueue", action: `${getGuid()}|cron_restart_backend`  },
      success: function(data, textStatus) {
          // showModalOk ('Result', data );

          // show message
          showModalOk(getString("general_event_title"), `${getString("general_event_description")}  <br/> <br/> <code id='${modalEventStatusId}'></code>`);

          updateModalState()

          write_notification('[Maintenance] App manually restarted', 'info')
      }
    })
}

// -----------------------------------------------------------
// Export CSV
function ExportCSV()
{ 
  // Execute
  openInNewTab("php/server/devices.php?action=ExportCSV")
}

// -----------------------------------------------------------
// Import CSV
function askImportCSV() {
  // Ask 
  showModalWarning('<?= lang('Maintenance_Tool_ImportCSV_noti');?>', '<?= lang('Maintenance_Tool_ImportCSV_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Okay');?>', 'ImportCSV');
}
function ImportCSV()
{   
  // Execute
  $.get('php/server/devices.php?action=ImportCSV', function(msg) {
    showMessage (msg);
    write_notification(`[Maintenance] Devices imported from CSV file`, 'info')
  });
}

// -----------------------------------------------------------
// Import pasted CSV
function askImportPastedCSV() {

  // Add new icon as base64 string 
  showModalInput ('<i class="fa fa-square-plus pointer"></i> <?= lang('Maintenance_Tool_ImportCSV_noti');?>', '<?= lang('Maintenance_Tool_ImportPastedCSV_noti_text');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Okay');?>', 'ImportPastedCSV');
}

function ImportPastedCSV()
{   
  var csv = $('#modal-input-textarea').val();
  csvBase64 = btoa(csv)
  // Execute
  $.post('php/server/devices.php?action=ImportCSV', { content: csvBase64 }, function(msg) {
    showMessage(msg);
    write_notification(`[Maintenance] Devices imported from pasted content`, 'info');
  });
}


// --------------------------------------------------------

// Clean log file 
var targetLogFile = "";
var logFileAction = "";


// --------------------------------------------------------

function logManage(callback) {
  targetLogFile = arguments[0];  // target
  logFileAction = arguments[1];  // action
  // Ask 
  showModalWarning('<?= lang('Gen_Purge');?>' + ' ' + arguments[1], '<?= lang('Gen_AreYouSure');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Okay');?>', "performLogManage");
}

// --------------------------------------------------------
function performLogManage() { 
  // Execute
  console.log("targetLogFile:" + targetLogFile)
  console.log("logFileAction:" + logFileAction)
  
  $.ajax({
    method: "POST",
    url: "php/server/util.php",
    data: { function: logFileAction, settings: targetLogFile  },
    success: function(data, textStatus) {
        showModalOk ('Result', data );
        write_notification(`[Maintenance] Log file "${targetLogFile}" manually purged`, 'info')
    }
  })
}

// --------------------------------------------------------
// scroll down the log areas
function scrollDown() {
 
    var elementToCheck = $("#tab_Logging_id");

    // Check if the parent <li> is active
    if (elementToCheck.parent().hasClass("active")) {
      var textAreas = $("#logsPlc textarea");

      textAreas.each(function() {
        $(this).scrollTop(this.scrollHeight);
      });
    }
 
}


// --------------------------------------------------------
// General initialization
// --------------------------------------------------------
function initializeTabs() {  
  setTimeout(() => {
    const key = "activeMaintenanceTab";

    // default selection
    let selectedTab = "tab_DBTools_id";

    // the #target from the URL
    let target = window.location.hash.substr(1);

    console.log(selectedTab);

    // get only the part between #...?
    if (target.includes('?')) {
      target = target.split('?')[0];
    }

    // update cookie if target specified
    if (target) {    
      selectedTab = target.endsWith("_id") ? target : `${target}_id`;
      setCache(key, selectedTab); // _id is added so it doesn't conflict with AdminLTE tab behavior
    }

    // get the tab id from the cookie (already overridden by the target)
    const cachedTab = getCache(key);
    if (cachedTab && !emptyArr.includes(cachedTab)) {
      selectedTab = cachedTab;
    }

    // Activate panel
    $('.nav-tabs a[id='+ selectedTab +']').tab('show');

    // When changed save new current tab
    $('a[data-toggle="tab"]').on('shown.bs.tab', (e) => {
      const newTabId = $(e.target).attr('id');
      setCache(key, newTabId);
    });

    // events on tab change
    $('a[data-toggle="tab"]').on('shown.bs.tab', (e) => {
      const newTarget = $(e.target).attr("href"); // activated tab
    });

    hideSpinner();
  }, 50);
}

//------------------------------------------------------------------------------
//  Logs render functionality
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
// Manages the auto-refresh functionality for the logs
let intervalId;

function toggleAutoRefresh() {
  const checkbox = $('#logsAutoRefresh')[0];

  if (checkbox.checked) {
    intervalId = setInterval(renderLogs, 1000);
  } else {
    clearInterval(intervalId);
  }
}

//------------------------------------------------------------------------------
// Manages the filter application on the logs
function applyFilter() {
      const filterText = $("#logsFilter").val().toLowerCase();
      
      $(".logs").each(function() {
        const originalText = $(this).data('originalText') || $(this).val();
        
        if (!$(this).data('originalText')) {
          $(this).data('originalText', originalText);
        }

        const filteredLines = originalText.split('\n').filter(line => 
          line.toLowerCase().includes(filterText)
        );

        $(this).val(filteredLines.join('\n'));
      });
    }

//------------------------------------------------------------------------------
// Renders all the logs
function renderLogs(customData) {
    $.ajax({
      url: 'php/components/logs.php', // PHP script URL
      type: 'POST', // Use POST method to send data
      dataType: 'html', // Expect HTML response
      // data: { items: JSON.stringify(customData) }, // Send customData as JSON
      success: function(response) {
        $('#logsPlc').html(response); // Replace container content with fetched HTML

        applyFilter();

        if($('#logsAutoScroll')[0].checked)
        {
          scrollDown(); // scroll down the logs
        }
        
      },
      error: function(xhr, status, error) {
        console.error('Error fetching infoboxes:', error);
      }
    });
  }

//------------------------------------------------------------------------------
// Init
window.onload = function asyncFooter() {
  renderLogs();

  // initializeTabs();

  try {
    $("#lastCommit").append('<a href="https://github.com/jokob-sk/NetAlertX/commits" target="_blank"><img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/jokob-sk/netalertx/main?logo=github"></a>');

    $("#lastDockerUpdate").append(
      '<a href="https://github.com/jokob-sk/NetAlertX/releases" target="_blank"><img alt="Docker last pushed" src="https://img.shields.io/github/v/release/jokob-sk/NetAlertX?color=0aa8d2&logoColor=fff&logo=GitHub&label=Latest"></a>');
  } catch (error) {
    console.error('Failed to load GitHub badges:', error);
  }
};

</script>




