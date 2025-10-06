<?php
  require 'php/templates/header.php';  
?>

<script>
  showSpinner();
</script>

<!-- ----------------------------------------------------------------------- -->
 
<!-- Page ------------------------------------------------------------------ -->
  <div class="content-wrapper eventsPage">

<!-- Main content ---------------------------------------------------------- -->
    <section class="content">

<!-- top small box --------------------------------------------------------- -->
      <div class="row">

        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getEvents('all');">
            <div class="small-box bg-aqua">
              <div class="inner"> <h3 id="eventsAll"> -- </h3>
                <p class="infobox_label"><?= lang('Events_Shortcut_AllEvents');?></p>
              </div>
              <div class="icon"> <i class="fa fa-bolt text-aqua-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getEvents('sessions');">
            <div class="small-box bg-green">
              <div class="inner"> <h3 id="eventsSessions"> -- </h3>
                <p class="infobox_label"><?= lang('Events_Shortcut_Sessions');?></p>
              </div>
              <div class="icon"> <i class="fa fa-plug text-green-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getEvents('missing');">
            <div  class="small-box bg-yellow">
              <div class="inner"> <h3 id="eventsMissing"> -- </h3>
                <p class="infobox_label"><?= lang('Events_Shortcut_MissSessions');?></p>
              </div>
              <div class="icon"> <i class="fa fa-exchange text-yellow-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getEvents('voided');">
            <div  class="small-box bg-yellow">
              <div class="inner"> <h3 id="eventsVoided"> -- </h3>
                <p class="infobox_label"><?= lang('Events_Shortcut_VoidSessions');?></p>
              </div>
              <div class="icon"> <i class="fa fa-exclamation-circle text-yellow-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getEvents('new');">
            <div  class="small-box bg-yellow">
              <div class="inner"> <h3 id="eventsNewDevices"> -- </h3>
                <p class="infobox_label"><?= lang('Events_Shortcut_NewDevices');?></p>
              </div>
              <div class="icon"> <i class="fa-solid fa-circle-plus text-yellow-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getEvents('down');">
            <div  class="small-box bg-red">
              <div class="inner"> <h3 id="eventsDown"> -- </h3>
                <p class="infobox_label"><?= lang('Events_Shortcut_DownAlerts');?></p>
              </div>
              <div class="icon"> <i class="fa fa-warning text-red-40"></i> </div>
            </div>
          </a>
        </div>

      </div>
      <!-- /.row -->

<!-- datatable ------------------------------------------------------------- -->
      <div class="row">
        <div class="col-xs-12">

          <div id="tableEventsBox" class="box">

            <!-- box-header -->
            <div class="box-header col-xs-12">
              <h3 id="tableEventsTitle" class="box-title text-gray col-xs-10">Events</h3>
              <div class="eventsPeriodSelectWrap col-xs-2">
                <select class="form-control" id="period" onchange="javascript: periodChanged();">
                  <option value="1 day"><?= lang('Events_Periodselect_today');?></option>
                  <option value="7 days"><?= lang('Events_Periodselect_LastWeek');?></option>
                  <option value="1 month" selected><?= lang('Events_Periodselect_LastMonth');?></option>
                  <option value="1 year"><?= lang('Events_Periodselect_LastYear');?></option>
                  <option value="100 years"><?= lang('Events_Periodselect_All');?></option>
                </select>
              </div>
              
            </div>

            

            <!-- table -->
            <div class="box-body table-responsive">

              

              <table id="tableEvents" class="table table-bordered table-hover table-striped ">
                <thead>
                <tr>
                  <th><?= lang('Events_TableHead_Order');?></th>
                  <th><?= lang('Events_TableHead_Device');?></th>
                  <th><?= lang('Events_TableHead_Owner');?></th>
                  <th><?= lang('Events_TableHead_Date');?></th>
                  <th><?= lang('Events_TableHead_EventType');?></th>
                  <th><?= lang('Events_TableHead_Connection');?></th>
                  <th><?= lang('Events_TableHead_Disconnection');?></th>
                  <th><?= lang('Events_TableHead_Duration');?></th>
                  <th><?= lang('Events_TableHead_DurationOrder');?></th>
                  <th><?= lang('Events_TableHead_IP');?></th>
                  <th><?= lang('Events_TableHead_IPOrder');?></th>
                  <th><?= lang('Events_TableHead_AdditionalInfo');?></th>
                  <th>N/A</th> 
                  <th>MAC</th>
                  <th><?= lang('Events_TableHead_PendingAlert');?></th>
                </tr>
                </thead>
              </table>
            </div>
            <!-- /.box-body -->

          </div>
          <!-- /.box -->
        </div>
        <!-- /.col -->
      </div>
      <!-- /.row -->

<!-- ----------------------------------------------------------------------- -->
    </section>
    <!-- /.content -->
  </div>
  <!-- /.content-wrapper -->


<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>

<!-- page script ----------------------------------------------------------- -->
<script>
  var parPeriod       = 'nax_parPeriod';
  var parTableRows    = 'nax_parTableRows';

  var eventsType      = 'all';
  var period          = '1 day';
  var tableRows       = parseInt(getSetting("UI_DEFAULT_PAGE_SIZE"));
  
  // Read parameters & Initialize components
  main();


// -----------------------------------------------------------------------------
function main() {
  // Get parameter value from cookies instead of server
  period = getCookie(parPeriod) === "" ? "1 day" : getCookie(parPeriod);
  $('#period').val(period);

  tableRows = getCookie(parTableRows) === "" ? parseInt(getSetting("UI_DEFAULT_PAGE_SIZE")) : parseInt(getCookie(parTableRows), 10);

  // Initialize components
  initializeDatatable();

  // Query data
  getEventsTotals();
  getEvents(eventsType);
}


// -----------------------------------------------------------------------------
function initializeDatatable () {
  $('#tableEvents').DataTable({
    'paging'       : true,
    'lengthChange' : true,
    'lengthMenu'   : getLengthMenu(parseInt(getSetting("UI_DEFAULT_PAGE_SIZE"))),
    'searching'    : true,
    'ordering'     : true,
    'info'         : true,
    'autoWidth'    : false,
    'order'       : [[0,"desc"], [3,"desc"], [5,"desc"]],

    // Parameters
    'pageLength'   : tableRows,

    'columnDefs'  : [
      {visible:   false,         targets: [0,5,6,7,8,10,11,12,13] },
      {className: 'text-center', targets: [] },
      {orderData: [8],           targets: 7 },
      {orderData: [10],          targets: 9 },

      // Device Name
      {targets: [1],
        "createdCell": function (td, cellData, rowData, row, col) {
          $(td).html ('<b><a href="deviceDetails.php?mac='+ rowData[13] +'" class="">'+ cellData +'</a></b>');
      } },

      // Replace HTML codes
      {targets: [4,5,6,7],
        "createdCell": function (td, cellData, rowData, row, col) {
          $(td).html (translateHTMLcodes (cellData));
      } },

      // PendingAlert
      {targets: [14],
        "createdCell": function (td, cellData, rowData, row, col) {
          // console.log(cellData);
          $(td).html (cellData);
      } },
      // Date
      {targets: [3],
        "createdCell": function (td, cellData, rowData, row, col) {
          // console.log(cellData);
          $(td).html (localizeTimestamp(cellData));
      } }
    ],

    // Processing
    'processing'  : true,
    'language'    : {
      processing: '<table><td width="130px" align="middle"><?= lang("Events_Loading");?></td><td><i class="fa-solid fa-spinner fa-spin-pulse"></i></td></table>',
      emptyTable: 'No data',
      "lengthMenu": "<?= lang('Events_Tablelenght');?>",
      "search":     "<?= lang('Events_Searchbox');?>: ",
      "paginate": {
          "next":       "<?= lang('Events_Table_nav_next');?>",
          "previous":   "<?= lang('Events_Table_nav_prev');?>"
      },
      "info":           "<?= lang('Events_Table_info');?>",
    },
    initComplete: function(settings, json) {
        hideSpinner(); // Called after the DataTable is fully initialized
    }
  });

  // Save Parameter rows when changed
  $('#tableEvents').on( 'length.dt', function ( e, settings, len ) {
    setCookie(parTableRows, len)
  } );
};


// -----------------------------------------------------------------------------
function periodChanged () {
  // Save Parameter Period
  period = $('#period').val();

  setCookie(parTableRows, period)

  // Requery totals and events
  getEventsTotals();
  getEvents (eventsType);
}


// -----------------------------------------------------------------------------
function getEventsTotals () {
  // stop timer
  stopTimerRefreshData();

  // get totals and put in boxes
  $.get('php/server/events.php?action=getEventsTotals&period='+ period, function(data) {
    var totalsEvents = JSON.parse(data);

    $('#eventsAll').html        (totalsEvents[0].toLocaleString());
    $('#eventsSessions').html   (totalsEvents[1].toLocaleString());
    $('#eventsMissing').html    (totalsEvents[2].toLocaleString());
    $('#eventsVoided').html     (totalsEvents[3].toLocaleString());
    $('#eventsNewDevices').html (totalsEvents[4].toLocaleString());
    $('#eventsDown').html       (totalsEvents[5].toLocaleString());

    // Timer for refresh data
    newTimerRefreshData (getEventsTotals);
  });
}


// -----------------------------------------------------------------------------
function getEvents (p_eventsType) {
  // Save status selected
  eventsType = p_eventsType;

  // Define color & title for the status selected
  switch (eventsType) {
    case 'all':       tableTitle = '<?= lang('Events_Shortcut_AllEvents');?>';      color = 'aqua';    sesionCols = false;  break;
    case 'sessions':  tableTitle = '<?= lang('Events_Shortcut_Sessions');?>';       color = 'green';   sesionCols = true;   break;
    case 'missing':   tableTitle = '<?= lang('Events_Shortcut_MissSessions');?>';   color = 'yellow';  sesionCols = true;   break;
    case 'voided':    tableTitle = '<?= lang('Events_Shortcut_VoidSessions');?>';   color = 'yellow';  sesionCols = false;  break;
    case 'new':       tableTitle = '<?= lang('Events_Shortcut_NewDevices');?>';     color = 'yellow';  sesionCols = false;  break;
    case 'down':      tableTitle = '<?= lang('Events_Shortcut_DownAlerts');?>';     color = 'red';     sesionCols = false;  break;
    default:          tableTitle = '<?= lang('Events_Shortcut_Events');?>';         boxClass = '';     sesionCols = false;  break;
  } 

  // Set title and color
  $('#tableEventsTitle')[0].className = 'box-title text-' + color;
  $('#tableEventsBox')[0].className = 'box box-' + color;
  $('#tableEventsTitle').html (tableTitle);

  // Columns Visibility
  $('#tableEvents').DataTable().column(3).visible (!sesionCols);
  $('#tableEvents').DataTable().column(4).visible (!sesionCols);
  $('#tableEvents').DataTable().column(5).visible (sesionCols);
  $('#tableEvents').DataTable().column(6).visible (sesionCols);
  $('#tableEvents').DataTable().column(7).visible (sesionCols);

  // Define new datasource URL and reload
  $('#tableEvents').DataTable().clear();
  $('#tableEvents').DataTable().draw();
  $('#tableEvents').DataTable().order ([0,"desc"], [3,"desc"], [5,"desc"]);
  $('#tableEvents').DataTable().ajax.url('php/server/events.php?action=getEvents&type=' + eventsType +'&period='+ period ).load();
};

</script>
