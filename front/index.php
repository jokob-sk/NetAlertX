<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/header.php';
?>

<!-- Page ------------------------------------------------------------------ -->
  <div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
      <h1 id="pageTitle">
         Devices
      </h1>

      <!-- period selector -->
      <span class="breadcrumb text-gray50">
        New Devices period:  
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
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: queryList('all');">
            <div class="small-box bg-aqua pa-small-box-aqua">
              <div class="inner">
  
                <h4>Total Devices</h4>
                <h3 id="devicesAll"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="fa fa-laptop"></i>
              </div>
              <div class="small-box-footer">
                Details <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: queryList('connected');">
            <div class="small-box bg-green pa-small-box-green">
              <div class="inner">
  
                <h4>Connected</h4>
                <h3 id="devicesConnected"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="fa fa-plug"></i>
              </div>
              <div class="small-box-footer">
                Details <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: queryList('new');">
            <div  class="small-box bg-yellow pa-small-box-yellow">
              <div class="inner">
  
                <h4>New Devices</h4>
                <h3 id="devicesNew"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="ion ion-plus-round"></i>
              </div>
              <div class="small-box-footer">
                Details <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>

        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: queryList('down');">
            <div  class="small-box bg-red pa-small-box-red">
              <div class="inner">
  
                <h4>Down Alerts</h4>
                <h3 id="devicesDown"> -- </h3>
  
              </div>
              <div class="icon">
                <i class="fa fa-warning"></i>
              </div>
              <div class="small-box-footer">
                Details <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>
        </div>

      </div>
      <!-- /.row -->

<!-- datatable ------------------------------------------------------------- -->
      <div class="row">
        <div class="col-xs-12">
          <div id="tableDevicesBox" class="box">
            <div class="box-header">
              <h3 id="tableDevicesTitle" class="box-title text-gray">Devices</h3>
            </div>
            <!-- /.box-header -->
            <div class="box-body table-responsive">
              <table id="tableDevices" class="table table-bordered table-hover table-striped ">
                <thead>
                <tr>
                  <th>Name</th>
                  <th>Owner</th>
                  <th>Device type</th>
                  <th>Favorite</th>
                  <th>Group</th>
                  <th>First Session</th>
                  <th>Last Session</th>
                  <th>Last IP</th>
                  <th>Status</th>
                  <th>MAC</th>
                  <th>Last IP Order</th>
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
  var deviceStatus = '';
  var period = '';

  // Initialize MAC
  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has ('status') == true) {
    deviceStatus = urlParams.get ('status');
  } else {
    deviceStatus = 'all';
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
  queryList (deviceStatus);
}


// -----------------------------------------------------------------------------
function initializeDatatable () {
  $('#tableDevices').DataTable({
    'paging'      : true,
    'lengthChange': true,
    'searching'   : true,
    'ordering'    : true,
    'info'        : true,
    'autoWidth'   : false,
    
    'order'       : [[3,"desc"], [0,"asc"]],

    'columnDefs'  : [
        {visible:   false,         targets: [9, 10] },
        {className: 'text-center', targets: [3, 8] },
        {width:     '0px',         targets: 8 },
        {orderData: [10],          targets: 7 },

        // Device Name
        {targets: [0],
          "createdCell": function (td, cellData, rowData, row, col) {
            $(td).html ('<b><a href="deviceDetails.php?mac='+ rowData[9]+ '&period='+ period +'" class="">'+ cellData +'</a></b>');
        } },

        // Favorite
        {targets: [3],
          "createdCell": function (td, cellData, rowData, row, col) {
            if (cellData == 1){
              $(td).html ('<i class="fa fa-star text-yellow" style="font-size:16px"></i>');
            } else {
              $(td).html ('');
            }
        } },
        
        // Dates
        {targets: [5, 6],
          "createdCell": function (td, cellData, rowData, row, col) {
            $(td).html (translateHTMLcodes (cellData));
        } },

        // Status color
        {targets: [8],
          "createdCell": function (td, cellData, rowData, row, col) {
            switch (cellData) {
              case 'Down':
                color='red';              break;
              case 'New':
                color='yellow';           break;
              case 'On-line':
                color='green';            break;
              case 'Off-line':
                color='gray text-white';  break;
              default:
                color='aqua';             break;
            };
      
            $(td).html ('<a href="deviceDetails.php?mac='+ rowData[9]+ '&period='+ period +'" class="badge bg-'+ color +'">'+ cellData +'</a>');
        } },
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
  $.get('php/server/devices.php?action=totals&period='+ period, function(data) {
    var totalsDevices = JSON.parse(data);

    $('#devicesAll').html       (totalsDevices[0].toLocaleString());
    $('#devicesConnected').html (totalsDevices[1].toLocaleString());
    $('#devicesNew').html       (totalsDevices[2].toLocaleString());
    $('#devicesDown').html      (totalsDevices[3].toLocaleString());
    });

  // Timer for refresh data
  newTimerRefreshData (queryTotals);
}


// -----------------------------------------------------------------------------
function queryList (status) {
  // Save status and period selected
  deviceStatus = status;
  period = document.getElementById('period').value;

  // Defini color & title for the status selected
  switch (deviceStatus) {
    case 'all':
      tableTitle = 'Total Devices';
      color = 'aqua';
      break;
    case 'connected':
      tableTitle = 'Connected Devices';
      color = 'green';
      break;
    case 'new':
      tableTitle = 'New Devices';
      color = 'yellow';
      break;
    case 'down':
      tableTitle = 'Down Alerts';
      color = 'red';
      break;
    case 'favorites':
      tableTitle = 'Favorites';
      color = 'yellow';
      break;
    default:
      tableTitle = 'Devices';
      boxClass = '';
      break;
  } 

  // Set title and color
  document.getElementById('tableDevicesTitle').className = 'box-title text-' + color;
  document.getElementById('tableDevicesBox').className = 'box box-' + color;
  $('#tableDevicesTitle').html (tableTitle);

  // Define new datasource URL and reload
  $('#tableDevices').DataTable().ajax.url('php/server/devices.php?action=list&status=' + deviceStatus +'&period='+ period ).load();
};

</script>
