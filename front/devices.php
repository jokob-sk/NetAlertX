<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  devices.php - Front module. Devices list page
#-------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
#--------------------------------------------------------------------------- -->

<?php
session_start();

if ($_SESSION["login"] != 1)
  {
      header('Location: /pialert/index.php');
      exit;
  }

  require 'php/templates/header.php';
  require 'php/templates/graph.php';
?>

<!-- Page ------------------------------------------------------------------ -->
  <div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
      <h1 id="pageTitle">
           <?php echo $pia_lang['Device_Title'];?>
      </h1>
    </section>

<!-- Main content ---------------------------------------------------------- -->
    <section class="content">

<!-- top small box 1 ------------------------------------------------------- -->
      <div class="row">
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('all');">
          <div class="small-box bg-aqua">
            <div class="inner"><h3 id="devicesAll"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Device_Shortcut_AllDevices'];?></p>
            </div>
            <div class="icon"><i class="fa fa-laptop text-aqua-40"></i></div>
          </div>
          </a>
        </div>
        
<!-- top small box 2 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('connected');">
          <div class="small-box bg-green">
            <div class="inner"><h3 id="devicesConnected"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Device_Shortcut_Connected'];?></p>
            </div>
            <div class="icon"><i class="fa fa-plug text-green-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 3 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('favorites');">
          <div class="small-box bg-yellow">
            <div class="inner"><h3 id="devicesFavorites"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Device_Shortcut_Favorites'];?></p>
            </div>
            <div class="icon"><i class="fa fa-star text-yellow-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 4 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('new');">
          <div class="small-box bg-yellow">
            <div class="inner"><h3 id="devicesNew"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Device_Shortcut_NewDevices'];?></p>
            </div>
            <div class="icon"><i class="ion ion-plus-round text-yellow-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 5 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('down');">
          <div class="small-box bg-red">
            <div class="inner"><h3 id="devicesDown"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Device_Shortcut_DownAlerts'];?></p>
            </div>
            <div class="icon"><i class="fa fa-warning text-red-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 6 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesList('archived');">
          <div class="small-box bg-gray top_small_box_gray_text">
            <div class="inner"><h3 id="devicesArchived"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Device_Shortcut_Archived'];?></p>
            </div>
            <div class="icon"><i class="fa fa-eye-slash text-gray-40"></i></div>
          </div>
          </a>
        </div>

      </div>

<!-- Activity Chart ------------------------------------------------------- -->

      <div class="row">
          <div class="col-md-12">
          <div class="box" id="clients">
              <div class="box-header with-border">
                <h3 class="box-title"><?php echo $pia_lang['Device_Shortcut_OnlineChart_a'];?>  <span class="maxlogage-interval">12</span> <?php echo $pia_lang['Device_Shortcut_OnlineChart_b'];?></h3>
              </div>
              <div class="box-body">
                <div class="chart">
                  <script src="lib/AdminLTE/bower_components/chart.js/Chart.js"></script>
                  <canvas id="OnlineChart" style="width:100%; height: 150px;  margin-bottom: 15px;"></canvas>
                </div>
              </div>
              <!-- /.box-body -->
            </div>
          </div>
      </div>
      <script src="js/graph_online_history.js"></script>
      <script>
        var pia_js_online_history_time = [<?php pia_graph_devices_data($Pia_Graph_Device_Time); ?>];
        var pia_js_online_history_ondev = [<?php pia_graph_devices_data($Pia_Graph_Device_Online); ?>];
        var pia_js_online_history_dodev = [<?php pia_graph_devices_data($Pia_Graph_Device_Down); ?>];
        var pia_js_online_history_ardev = [<?php pia_graph_devices_data($Pia_Graph_Device_Arch); ?>];
        pia_draw_graph_online_history(pia_js_online_history_time, pia_js_online_history_ondev, pia_js_online_history_dodev, pia_js_online_history_ardev);
      </script>

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
                  <th><?php echo $pia_lang['Device_TableHead_Name'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_Owner'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_Type'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_Favorite'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_Group'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_FirstSession'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_LastSession'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_LastIP'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_MAC'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_Status'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_MAC'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_LastIPOrder'];?></th>
                  <th><?php echo $pia_lang['Device_TableHead_Rowid'];?></th>
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
    'lengthMenu'   : [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, '<?php echo $pia_lang['Device_Tablelenght_all'];?>']],
    'searching'    : true,

    'ordering'     : true,
    'info'         : true,
    'autoWidth'    : false,

    // Parameters
    'pageLength'   : tableRows,
    'order'        : tableOrder,
    // 'order'       : [[3,'desc'], [0,'asc']],

    'columnDefs'   : [
      {visible:   false,         targets: [10, 11, 12] },
      {className: 'text-center', targets: [3, 8, 9] },
      {width:     '80px',        targets: [5, 6] },
      {width:     '0px',         targets: 9 },
      {orderData: [11],          targets: 7 },

      // Device Name
      {targets: [0],
        'createdCell': function (td, cellData, rowData, row, col) {
            $(td).html ('<b><a href="deviceDetails.php?mac='+ rowData[10] +'" class="">'+ cellData +'</a></b>');
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

      // Random MAC
      {targets: [8],
        'createdCell': function (td, cellData, rowData, row, col) {
          if (cellData == 1){
            $(td).html ('<i data-toggle="tooltip" data-placement="right" title="Random MAC" style="font-size: 16px;" class="text-yellow glyphicon glyphicon-random"></i>');
          } else {
            $(td).html ('');
          }
      } },

      // Status color
      {targets: [9],
        'createdCell': function (td, cellData, rowData, row, col) {
          switch (cellData) {
            case 'Down':      color='red';              break;
            case 'New':       color='yellow';           break;
            case 'On-line':   color='green';            break;
            case 'Off-line':  color='gray text-white';  break;
            case 'Archived':  color='gray text-white';  break;
            default:          color='aqua';             break;
          };
      
          $(td).html ('<a href="deviceDetails.php?mac='+ rowData[10] +'" class="badge bg-'+ color +'">'+ cellData.replace('-', '') +'</a>');
      } },
    ],
    
    // Processing
    'processing'  : true,
    'language'    : {
      processing: '<table> <td width="130px" align="middle">Loading...</td><td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw"></td> </table>',
      emptyTable: 'No data',
      "lengthMenu": "<?php echo $pia_lang['Device_Tablelenght'];?>",
      "search":     "<?php echo $pia_lang['Device_Searchbox'];?>: ",
      "paginate": {
          "next":       "<?php echo $pia_lang['Device_Table_nav_next'];?>",
          "previous":   "<?php echo $pia_lang['Device_Table_nav_prev'];?>"
      },
      "info":           "<?php echo $pia_lang['Device_Table_info'];?>",
    }
  });

  // Save cookie Rows displayed, and Parameters rows & order
  $('#tableDevices').on( 'length.dt', function ( e, settings, len ) {
    setParameter (parTableRows, len);
  } );
    
  $('#tableDevices').on( 'order.dt', function () {
    setParameter (parTableOrder, JSON.stringify (table.order()) );
    setCookie ('devicesList',JSON.stringify (table.column(12, { 'search': 'applied' }).data().toArray()) );
  } );

  $('#tableDevices').on( 'search.dt', function () {
    setCookie ('devicesList', JSON.stringify (table.column(12, { 'search': 'applied' }).data().toArray()) );
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
    $('#devicesFavorites').html  (totalsDevices[2].toLocaleString());
    $('#devicesNew').html        (totalsDevices[3].toLocaleString());
    $('#devicesDown').html       (totalsDevices[4].toLocaleString());
    $('#devicesArchived').html   (totalsDevices[5].toLocaleString());

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
    case 'all':        tableTitle = '<?php echo $pia_lang['Device_Shortcut_AllDevices']?>';  color = 'aqua';    break;
    case 'connected':  tableTitle = '<?php echo $pia_lang['Device_Shortcut_Connected']?>';   color = 'green';   break;
    case 'favorites':  tableTitle = '<?php echo $pia_lang['Device_Shortcut_Favorites']?>';   color = 'yellow';  break;
    case 'new':        tableTitle = '<?php echo $pia_lang['Device_Shortcut_NewDevices']?>';  color = 'yellow';  break;
    case 'down':       tableTitle = '<?php echo $pia_lang['Device_Shortcut_DownAlerts']?>';  color = 'red';     break;
    case 'archived':   tableTitle = '<?php echo $pia_lang['Device_Shortcut_Archived']?>';    color = 'gray';    break;
    default:           tableTitle = '<?php echo $pia_lang['Device_Shortcut_Devices']?>';     color = 'gray';    break;
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
