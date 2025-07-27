<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>
<!-- ----------------------------------------------------------------------- -->
 

<!-- Hide Connections -->
<div class="col-sm-12 col-xs-12">
    <label class="col-sm-3 col-xs-10">      
      <?= lang('DevDetail_Events_CheckBox');?>
    </label>
    <input class="checkbox blue col-sm-1 col-xs-2" id="chkHideConnectionEvents" type="checkbox" onChange="loadEventsData()">
</div>

<!-- Datatable Events -->
<table id="tableEvents" class="table table-bordered table-hover table-striped ">
    <thead>
    <tr>
    <th><?= lang("DevDetail_Tab_EventsTableDate");?></th>
    <th><?= lang("DevDetail_Tab_EventsTableDate");?></th>
    <th><?= lang("DevDetail_Tab_EventsTableEvent");?></th>
    <th><?= lang("DevDetail_Tab_EventsTableIP");?></th>
    <th><?= lang("DevDetail_Tab_EventsTableInfo");?></th>
    </tr>
    </thead>
</table>


<script>





// -----------------------------------------------------------------------------
function loadEventsData() {
  const hideConnections = $('#chkHideConnectionEvents')[0].checked;
  const hideConnectionsStr = hideConnections ? 'true' : 'false';

  mac = getMac()

  const rawSql = `
    SELECT eve_DateTime, eve_DateTime, eve_EventType, eve_IP, eve_AdditionalInfo
    FROM Events 
    WHERE eve_MAC = "${mac}" 
      AND (
        (eve_EventType NOT IN ("Connected", "Disconnected", "VOIDED - Connected", "VOIDED - Disconnected"))
        OR "${hideConnectionsStr}" = "false"
      )
  `;

  const apiUrl = `php/server/dbHelper.php?action=read&rawSql=${btoa(encodeURIComponent(rawSql))}`;

  // Manually load the data first
  $.get(apiUrl, function (data) {
    const parsed = JSON.parse(data);
    
    const rows = parsed.map(row => {
      const rawDate = row.eve_DateTime;
      const formattedDate = rawDate ? localizeTimestamp(rawDate) : '-';
      return [
        formattedDate,
        row.eve_DateTime,
        row.eve_EventType,
        row.eve_IP,
        row.eve_AdditionalInfo
      ];
    });

    // Fill the table manually
    const table = $('#tableEvents').DataTable();
    table.clear();
    table.rows.add(rows); // assuming each row is an array
    table.draw();

    hideSpinner();
  });
}

function initializeEventsDatatable (eventsRows) {

  if ($.fn.dataTable.isDataTable('#tableEvents')) {
      $('#tableEvents').DataTable().clear().destroy();
  }

  $('#tableEvents').DataTable({
      'paging'      : true,
      'lengthChange': true,
      'lengthMenu'  : [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, 'All']],
      'searching'   : true,
      'ordering'    : true,
      'info'        : true,
      'autoWidth'   : false,
      'order'       : [[0,'desc']],
      'pageLength'  : eventsRows,

      'columnDefs'  : [
          {   orderData: [1], targets:  [0]   },
          {   visible:   false, targets: [1]  }, 
          {
              targets: [0],
              'createdCell': function (td, cellData, rowData, row, col) {
                  $(td).html(translateHTMLcodes(localizeTimestamp(cellData)));
              }
          }
      ],

      'processing'  : true,
      'language'    : {
          processing: '<table><td width="130px" align="middle"><?= lang("DevDetail_Loading");?></td>'+
                      '<td><i class="fa-solid fa-spinner fa-spin-pulse"></i></td></table>',
          emptyTable: 'No data',
          "lengthMenu": "<?= lang('Events_Tablelenght');?>",
          "search":     "<?= lang('Events_Searchbox');?>: ",
          "paginate": {
              "next":     "<?= lang('Events_Table_nav_next');?>",
              "previous": "<?= lang('Events_Table_nav_prev');?>"
          },
          "info": "<?= lang('Events_Table_info');?>",
      }
  });
}

// -----------------------------------------------
// INIT with polling for panel element visibility
// -----------------------------------------------

var eventsPageInitialized = false; 

function initDeviceEventsPage()
{
  // Only proceed if .plugin-content is visible
  if (!$('#panEvents:visible').length) {
    return; // exit early if nothing is visible
  }

  // init page once
  if (eventsPageInitialized) return; //  ENSURE ONCE
  eventsPageInitialized = true;

  showSpinner();

  var eventsRows          = 10;
  var eventsHide          = true;

  initializeEventsDatatable(eventsRows);
  loadEventsData();
}

// -----------------------------------------------------------------------------
// Recurring function to monitor the URL and reinitialize if needed
function deviceEventsPageUpdater() {
  initDeviceEventsPage();

  // Run updater again after delay
  setTimeout(deviceEventsPageUpdater, 200);
}

deviceEventsPageUpdater();


</script>