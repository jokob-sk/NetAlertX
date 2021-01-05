<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/header.php';
?>

<!-- Page ------------------------------------------------------------------ -->
  <div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
      <h1 id="pageTitle">
         Events
      </h1>

      <!-- period selector -->
      <span class="breadcrumb text-gray50">
        Events period:  
        <select id="period" onchange="javascript: periodChanged();">
          <option value="1 day">Today</option>
          <option value="7 days">Last Week</option>
          <option value="1 month" selected>Last Month</option>
          <option value="1 year">Last Year</option>
          <option value="100 years">All info</option>
        </select>
      </span>

    </section>

<!-- Main content ---------------------------------------------------------- -->
    <section class="content">
      <div class="row">

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: queryList('all');">
            <div class="small-box bg-aqua pa-small-box-aqua pa-small-box-2">
              <div class="inner">
  
                <h3 id="eventsAll"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="fa fa-bolt text-aqua-20"></i>
              </div>
              <div class="small-box-footer">
                All events <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: queryList('sessions');">
            <div class="small-box bg-green pa-small-box-green pa-small-box-2">
              <div class="inner">
  
                <h3 id="eventsSessions"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="fa fa-plug text-green-20"></i>
              </div>
              <div class="small-box-footer">
                Sessions <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: queryList('missing');">
            <div  class="small-box bg-yellow pa-small-box-yellow pa-small-box-2">
              <div class="inner">
  
                <h3 id="eventsMissing"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="fa fa-exchange text-yellow-20"></i>
              </div>
              <div class="small-box-footer">
                Missing Sessions <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>

        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: queryList('voided');">
            <div  class="small-box bg-yellow pa-small-box-yellow pa-small-box-2">
              <div class="inner">
  
                <h3 id="eventsVoided"> -- </h3>
  
              </div>
              <div class="icon text-aqua-20">
                <i class="fa fa-exclamation-circle text-yellow-20"></i>
              </div>
              <div class="small-box-footer">
                Voided Sessions <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>

        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: queryList('new');">
            <div  class="small-box bg-yellow pa-small-box-yellow pa-small-box-2">
              <div class="inner">
  
                <h3 id="eventsNewDevices"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="ion ion-plus-round text-yellow-20"></i>
              </div>
              <div class="small-box-footer">
                New Devices <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>

        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: queryList('down');">
            <div  class="small-box bg-red pa-small-box-red pa-small-box-2">
              <div class="inner">
  
                <h3 id="eventsDown"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="fa fa-warning text-red-20"></i>
              </div>
              <div class="small-box-footer">
                Down Alerts <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>
        </div>

      </div>
      <!-- /.row -->

<!-- datatable ------------------------------------------------------------- -->
      <div class="row">
        <div class="col-xs-12">
          <div id="tableEventsBox" class="box">
            <div class="box-header">
              <h3 id="tableEventsTitle" class="box-title text-gray">Events</h3>
            </div>
            <!-- /.box-header -->
            <div class="box-body table-responsive">
              <table id="tableEvents" class="table table-bordered table-hover table-striped ">
                <thead>
                <tr>
                  <th>Order</th>
                  <th>Device</th>
                  <th>Owner</th>
                  <th>Date</th>
                  <th>Event Type</th>
                  <th>Connection</th>
                  <th>Disconnection</th>
                  <th>Duration</th>
                  <th>Duration Order</th>
                  <th>IP</th>
                  <th>IP Order</th>
                  <th>Additional Info</th>
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


<!-- ----------------------------------------------------------------------- -->
<!-- Datatable -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/datatables.net-bs/css/dataTables.bootstrap.min.css">
  <script src="lib/AdminLTE/bower_components/datatables.net/js/jquery.dataTables.min.js"></script>
  <script src="lib/AdminLTE/bower_components/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>


<!-- page script ----------------------------------------------------------- -->
<script>

// -----------------------------------------------------------------------------
  var eventsType = '';
  var period = '';
  
  // Initialize MAC
  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has ('status') == true) {
    eventsType = urlParams.get ('type');
  } else {
    eventsType = 'all';
  }

  // Initialize components
  $(function () {
    initializeDatatable();
    periodChanged();
  });


// -----------------------------------------------------------------------------
function periodChanged () {
  // Requery totals and list
  queryTotals();
  queryList (eventsType);
}


// -----------------------------------------------------------------------------
function initializeDatatable () {
  $('#tableEvents').DataTable({
    'paging'      : true,
    'lengthChange': true,
    'searching'   : true,
    'ordering'    : true,
    'info'        : true,
    'autoWidth'   : false,

    'order'       : [[0,"desc"], [3,"desc"], [5,"desc"]],

    'columnDefs'  : [
        {visible:   false,         targets: [0,5,6,7,8,10] },
        {className: 'text-center', targets: [] },
        {orderData: [8],           targets: 7 },
        {orderData: [10],          targets: 9 },

        // Device Name
        {targets: [1],
          "createdCell": function (td, cellData, rowData, row, col) {
            $(td).html ('<b><a href="deviceDetails.php?mac='+ rowData[13]+ '&period='+ period +'" class="">'+ cellData +'</a></b>');
        } },

        // Replace HTML codes
        {targets: [3,4,5,6,7],
          "createdCell": function (td, cellData, rowData, row, col) {
            $(td).html (translateHTMLcodes (cellData));
        } }
    ],

    'processing'  : true,
    'language'    : {
      processing: '<table><td width="130px" align="middle">Loading...</td><td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw"></td></table>',
      emptyTable: 'No data'
    }
        
  });
};


// -----------------------------------------------------------------------------
function queryTotals () {
  // debugTimer();
  // stop timer
  stopTimerRefreshData();

  // period
  period = document.getElementById('period').value;

  // get totals and put in boxes
  $.get('php/server/events.php?action=totals&period='+ period, function(data) {
    var totalsEvents = JSON.parse(data);

    $('#eventsAll').html        (totalsEvents[0].toLocaleString());
    $('#eventsSessions').html   (totalsEvents[1].toLocaleString());
    $('#eventsMissing').html    (totalsEvents[2].toLocaleString());
    $('#eventsVoided').html     (totalsEvents[3].toLocaleString());
    $('#eventsNewDevices').html (totalsEvents[4].toLocaleString());
    $('#eventsDown').html       (totalsEvents[5].toLocaleString());
    });

  // Timer for refresh data
  newTimerRefreshData (queryTotals);
}


// -----------------------------------------------------------------------------
function queryList (p_eventsType) {
  // Save status and period selected
  eventsType = p_eventsType;
  period = document.getElementById('period').value;

  // Define color & title for the status selected
  sesionCols = false;
  switch (eventsType) {
    case 'all':
      tableTitle = 'All Events';
      color = 'aqua';
      break;
    case 'sessions':
      tableTitle = 'Sessions';
      color = 'green';
      sesionCols = true;
      break;
    case 'missing':
      tableTitle = 'Missing Events';
      color = 'yellow';
      sesionCols = true;
      break;
    case 'voided':
      tableTitle = 'Voided Events';
      color = 'yellow';
      break;
    case 'new':
      tableTitle = 'New Devices Events';
      color = 'yellow';
      break;
    case 'down':
      tableTitle = 'Down Alerts';
      color = 'red';
      break;
    default:
      tableTitle = 'Events';
      boxClass = '';
      break;
  } 

  // Set title and color
  document.getElementById('tableEventsTitle').className = 'box-title text-' + color;
  document.getElementById('tableEventsBox').className = 'box box-' + color;
  $('#tableEventsTitle').html (tableTitle);

  // Coluumns Visibility
  $('#tableEvents').DataTable().column(3).visible (!sesionCols);
  $('#tableEvents').DataTable().column(4).visible (!sesionCols);
  $('#tableEvents').DataTable().column(5).visible (sesionCols);
  $('#tableEvents').DataTable().column(6).visible (sesionCols);
  $('#tableEvents').DataTable().column(7).visible (sesionCols);

  // Define new datasource URL and reload
  $('#tableEvents').DataTable().clear();
  $('#tableEvents').DataTable().draw();
  $('#tableEvents').DataTable().order ([0,"desc"], [3,"desc"], [5,"desc"]);
  $('#tableEvents').DataTable().ajax.url('php/server/events.php?action=list&type=' + eventsType +'&period='+ period ).load();
};

</script>
