<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  devices.php - Front module. Devices list page
#-------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
#--------------------------------------------------------------------------- -->

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
    </section>

<!-- Main content ---------------------------------------------------------- -->
    <section class="content">

<!-- top small box 1 ------------------------------------------------------- -->
      <div class="row">

        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('all');">
            <div class="small-box bg-aqua pa-small-box-aqua">

              <div class="inner">
                <h4>Total Devices</h4>
                <h3 id="devicesAll"> -- </h3>
              </div>

              <div class="icon"> <i class="fa fa-laptop"></i> </div>
              <div class="small-box-footer"> Details <i class="fa fa-arrow-circle-right"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 2 ------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('connected');">
            <div class="small-box bg-green pa-small-box-green">

              <div class="inner">
                <h4>Connected</h4>
                <h3 id="devicesConnected"> -- </h3>
              </div>

              <div class="icon"> <i class="fa fa-plug"></i> </div>
              <div class="small-box-footer"> Details <i class="fa fa-arrow-circle-right"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 3 ------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('new');">
            <div  class="small-box bg-yellow pa-small-box-yellow">

              <div class="inner">
                <h4>New Devices</h4>
                <h3 id="devicesNew"> -- </h3>
              </div>

              <div class="icon"> <i class="ion ion-plus-round"></i> </div>
              <div class="small-box-footer"> Details <i class="fa fa-arrow-circle-right"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 4 ------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('down');">
            <div  class="small-box bg-red pa-small-box-red">

              <div class="inner">
                <h4>Down Alerts</h4>
                <h3 id="devicesDown"> -- </h3>
              </div>

              <div class="icon"> <i class="fa fa-warning"></i> </div>
              <div class="small-box-footer"> Details <i class="fa fa-arrow-circle-right"></i> </div>
            </div>
          </a>
        </div>

      </div>
      <!-- /.row -->

<!-- datatable ------------------------------------------------------------- -->
      <div class="row">
        <div class="col-xs-12">
          <div id="tableDevicesBox" class="box">

            <!-- box-header -->
            <div class="box-header">
              <h3 id="tableDevicesTitle" class="box-title text-gray">Devices</h3>
            </div>

            <!-- table -->
            <div class="box-body table-responsive">
              <table id="tableDevices" class="table table-bordered table-hover table-striped">
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
  var deviceStatus    = 'all';
  var parTableRows    = 'Front_Devices_Rows';
  var parTableOrder   = 'Front_Devices_Order';
  var tableRows       = 10;
  var tableOrder      = [[3,'desc'], [0,'asc']];

  // Read parameters & Initialize components
  main();


// -----------------------------------------------------------------------------
function main () {
  // get parameter value
  $.get('php/server/parameters.php?action=get&parameter='+ parTableRows, function(data) {
    var result = JSON.parse(data);
    if (Number.isInteger (result) ) {
        tableRows = result;
    }

    // get parameter value
    $.get('php/server/parameters.php?action=get&parameter='+ parTableOrder, function(data) {
      var result = JSON.parse(data);
      result = JSON.parse(result);
      if (Array.isArray (result) ) {
        tableOrder = result;
      }

      // Initialize components with parameters
      initializeDatatable();

      // query data
      getDevicesTotals();
      getDevicesList (deviceStatus);
    });
  });
}

// -----------------------------------------------------------------------------
function initializeDatatable () {
  var table=
  $('#tableDevices').DataTable({
    'paging'       : true,
    'lengthChange' : true,
    'lengthMenu'   : [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, 'All']],
    'searching'    : true,
    'ordering'     : true,
    'info'         : true,
    'autoWidth'    : false,

    // Parameters
    'pageLength'   : tableRows,
    'order'        : tableOrder,
    // 'order'       : [[3,'desc'], [0,'asc']],

    'columnDefs'   : [
      {visible:   false,         targets: [9, 10] },
      {className: 'text-center', targets: [3, 8] },
      {width:     '0px',         targets: 8 },
      {orderData: [10],          targets: 7 },

      // Device Name
      {targets: [0],
        'createdCell': function (td, cellData, rowData, row, col) {
            $(td).html ('<b><a href="deviceDetails.php?mac='+ rowData[9] +'" class="">'+ cellData +'</a></b>');
      } },

      // Favorite
      {targets: [3],
        'createdCell': function (td, cellData, rowData, row, col) {
          if (cellData == 1){
            $(td).html ('<i class="fa fa-star text-yellow" style="font-size:16px"></i>');
          } else {
            $(td).html ('');
          }
      } },
        
      // Dates
      {targets: [5, 6],
        'createdCell': function (td, cellData, rowData, row, col) {
          $(td).html (translateHTMLcodes (cellData));
      } },

      // Status color
      {targets: [8],
        'createdCell': function (td, cellData, rowData, row, col) {
          switch (cellData) {
            case 'Down':      color='red';              break;
            case 'New':       color='yellow';           break;
            case 'On-line':   color='green';            break;
            case 'Off-line':  color='gray text-white';  break;
            default:          color='aqua';             break;
          };
      
          $(td).html ('<a href="deviceDetails.php?mac='+ rowData[9] +'" class="badge bg-'+ color +'">'+ cellData +'</a>');
      } },
    ],
    
    // Processing
    'processing'  : true,
    'language'    : {
      processing: '<table> <td width="130px" align="middle">Loading...</td><td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw"></td> </table>',
      emptyTable: 'No data'
    }
  });

  // Save Parameters rows & order when changed
  $('#tableDevices').on( 'length.dt', function ( e, settings, len ) {
    setParameter (parTableRows, len);
  } );
    
  $('#tableDevices').on( 'order.dt', function () {
    setParameter (parTableOrder, JSON.stringify (table.order()) );
  } );
};


// -----------------------------------------------------------------------------
function getDevicesTotals () {
  // stop timer
  stopTimerRefreshData();

  // get totals and put in boxes
  $.get('php/server/devices.php?action=getDevicesTotals', function(data) {
    var totalsDevices = JSON.parse(data);

    $('#devicesAll').html        (totalsDevices[0].toLocaleString());
    $('#devicesConnected').html  (totalsDevices[1].toLocaleString());
    $('#devicesNew').html        (totalsDevices[2].toLocaleString());
    $('#devicesDown').html       (totalsDevices[3].toLocaleString());

    // Timer for refresh data
    newTimerRefreshData (getDevicesTotals);
  } );
}


// -----------------------------------------------------------------------------
function getDevicesList (status) {
  // Save status selected
  deviceStatus = status;

  // Define color & title for the status selected
  switch (deviceStatus) {
    case 'all':        tableTitle = 'Total Devices';      color = 'aqua';    break;
    case 'connected':  tableTitle = 'Connected Devices';  color = 'green';   break;
    case 'new':        tableTitle = 'New Devices';        color = 'yellow';  break;
    case 'down':       tableTitle = 'Down Alerts';        color = 'red';     break;
    case 'favorites':  tableTitle = 'Favorites';          color = 'yellow';  break;
    default:           tableTitle = 'Devices';            boxClass = '';     break;
  } 

  // Set title and color
  $('#tableDevicesTitle')[0].className = 'box-title text-'+ color;
  $('#tableDevicesBox')[0].className = 'box box-'+ color;
  $('#tableDevicesTitle').html (tableTitle);

  // Define new datasource URL and reload
  $('#tableDevices').DataTable().ajax.url(
    'php/server/devices.php?action=getDevicesList&status=' + deviceStatus).load();
};

</script>
