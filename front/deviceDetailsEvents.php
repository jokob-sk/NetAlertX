<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>
<!-- ----------------------------------------------------------------------- -->
 

<!-- Hide Connections -->
<div class="text-center">
    <label>
    <input class="checkbox blue hidden" id="chkHideConnectionEvents" type="checkbox" checked>
    <?= lang('DevDetail_Events_CheckBox');?>
    </label>
</div>

<!-- Datatable Events -->
<table id="tableEvents" class="table table-bordered table-hover table-striped ">
    <thead>
    <tr>
    <th><?= lang("DevDetail_Tab_EventsTableDate");?></th>
    <th><?= lang("DevDetail_Tab_EventsTableEvent");?></th>
    <th><?= lang("DevDetail_Tab_EventsTableIP");?></th>
    <th><?= lang("DevDetail_Tab_EventsTableInfo");?></th>
    </tr>
    </thead>
</table>


<script>

  var eventsRows          = 10;
  var eventsHide          = true;
  var parEventsRows       = 'Front_Details_Events_Rows';
  var parEventsHide       = 'Front_Details_Events_Hide';



  // -----------------------------------------------------------------------------


  function loadEventsData() {
    // Define Events datasource and query dada
    hideConnections = $('#chkHideConnectionEvents')[0].checked;
    $('#tableEvents').DataTable().ajax.url('php/server/events.php?action=getDeviceEvents&mac=' + mac +'&period='+ period +'&hideConnections='+ hideConnections).load();
  }

function initializeSessionsDatatable () {

  // Events datatable
  $('#tableEvents').DataTable({
    'paging'      : true,
    'lengthChange': true,
    'lengthMenu'   : [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, 'All']],
    'searching'   : true,
    'ordering'    : true,
    'info'        : true,
    'autoWidth'   : false,
    'order'       : [[0,'desc']],

    // Parameters
    'pageLength'  : eventsRows,

    'columnDefs'  : [
        // Replace HTML codes
        {targets: [0],
          'createdCell': function (td, cellData, rowData, row, col) {
            $(td).html (translateHTMLcodes (localizeTimestamp(cellData)));
        } }
    ],

    // Processing
    'processing'  : true,
    'language'    : {
      processing: '<table><td width="130px" align="middle"><?= lang("DevDetail_Loading");?></td>'+
                  '<td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw">'+
                  '</td></table>',
      emptyTable: 'No data',
      "lengthMenu": "<?= lang('Events_Tablelenght');?>",
      "search":     "<?= lang('Events_Searchbox');?>: ",
      "paginate": {
          "next":       "<?= lang('Events_Table_nav_next');?>",
          "previous":   "<?= lang('Events_Table_nav_prev');?>"
      },
      "info":           "<?= lang('Events_Table_info');?>",
    }
});

}

initializeSessionsDatatable();
loadEventsData();

</script>