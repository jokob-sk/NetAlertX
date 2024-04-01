<!--
#---------------------------------------------------------------------------------#
#  Pi.Alert                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #  
#                                                                                 #
#  devices.php - Front module. Devices list page                                  #
#---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
#---------------------------------------------------------------------------------#
-->

<?php

  require 'php/templates/header.php';
  require 'php/templates/graph.php';
  

  // check permissions
  $dbPath = "../db/pialert.db";
  $confPath = "../config/pialert.conf";

  checkPermissions([$dbPath, $confPath]);
?>

<!-- Page ------------------------------------------------------------------ -->
  <div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
      <h1 id="pageTitle">
          <i class="fa fa-laptop"></i>
          <?= lang('Device_Title');?>
      </h1>
    </section>

<!-- Main content ---------------------------------------------------------- -->
    <section class="content">

<!-- top small box 1 ------------------------------------------------------- -->
      <div class="row">
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: initializeDatatable('my');">
          <div class="small-box bg-aqua">
            <div class="inner"><h3 id="devicesMy"> -- </h3>
                <p class="infobox_label"><?= lang('Device_Shortcut_AllDevices');?></p>
            </div>
            <div class="icon"><i class="fa fa-laptop text-aqua-40"></i></div>
          </div>
          </a>
        </div>
        
<!-- top small box 2 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: initializeDatatable('connected');">
          <div class="small-box bg-green">
            <div class="inner"><h3 id="devicesConnected"> -- </h3>
                <p class="infobox_label"><?= lang('Device_Shortcut_Connected');?></p>
            </div>
            <div class="icon"><i class="fa fa-plug text-green-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 3 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: initializeDatatable('favorites');">
          <div class="small-box bg-yellow">
            <div class="inner"><h3 id="devicesFavorites"> -- </h3>
                <p class="infobox_label"><?= lang('Device_Shortcut_Favorites');?></p>
            </div>
            <div class="icon"><i class="fa fa-star text-yellow-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 4 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: initializeDatatable('new');">
          <div class="small-box bg-yellow">
            <div class="inner"><h3 id="devicesNew"> -- </h3>
                <p class="infobox_label"><?= lang('Device_Shortcut_NewDevices');?></p>
            </div>
            <div class="icon"><i class="ion ion-plus-round text-yellow-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 5 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: initializeDatatable('down');">
          <div class="small-box bg-red">
            <div class="inner"><h3 id="devicesDown"> -- </h3>
                <p class="infobox_label"><?= lang('Device_Shortcut_DownAlerts');?></p>
            </div>
            <div class="icon"><i class="fa fa-warning text-red-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 6 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: initializeDatatable('archived');">
          <div class="small-box bg-gray top_small_box_gray_text">
            <div class="inner"><h3 id="devicesArchived"> -- </h3>
                <p class="infobox_label"><?= lang('Device_Shortcut_Archived');?></p>
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
                <h3 class="box-title"><?= lang('Device_Shortcut_OnlineChart');?> </h3> 
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
        
        setTimeout(() => {
          pia_draw_graph_online_history(
          pia_js_online_history_time, 
          pia_js_online_history_ondev, 
          pia_js_online_history_dodev, 
          pia_js_online_history_ardev);
        }, 500);

      </script>

<!-- datatable ------------------------------------------------------------- -->
      <div class="row">
        <div class="col-xs-12">
          <div id="tableDevicesBox" class="box">

            <!-- box-header -->
            <div class="box-header">
              <div class=" col-md-10 ">
                <h3 id="tableDevicesTitle" class="box-title text-gray "></h3>  
              </div>    
            </div>

            <!-- table -->
            <div class="box-body table-responsive">
              <table id="tableDevices" class="table table-bordered table-hover table-striped">
                <thead>
                <tr>                
                  
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
    <div id="multiEditPlc" class="col-md-2"></div>
  </div>
  <!-- /.content-wrapper -->


<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>


<!-- ----------------------------------------------------------------------- -->
<!-- Datatable -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/datatables.net-bs/css/dataTables.bootstrap.min.css">
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/datatables.net/css/select.dataTables.min.css">
  <script src="lib/AdminLTE/bower_components/datatables.net/js/jquery.dataTables.min.js"></script>
  <script src="lib/AdminLTE/bower_components/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>
  <script src="lib/AdminLTE/bower_components/datatables.net/js/dataTables.select.min.js"></script>

<!-- page script ----------------------------------------------------------- -->
<script>
  var deviceStatus    = 'all';
  var parTableRows    = 'Front_Devices_Rows';
  var parTableOrder   = 'Front_Devices_Order';
  var tableRows       = 10;
  var tableOrder      = [[3,'desc'], [0,'asc']];
  
  var tableColumnHide = [];
  var columnsStr = '[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]';
  var tableColumnOrder = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]; 
  var tableColumnVisible = tableColumnOrder;
  //initialize the table headers in the correct order
  var headersDefaultOrder = [ 
                              getString('Device_TableHead_Name'),
                              getString('Device_TableHead_Owner'),
                              getString('Device_TableHead_Type'),   
                              getString('Device_TableHead_Icon'),
                              getString('Device_TableHead_Favorite'),
                              getString('Device_TableHead_Group'),
                              getString('Device_TableHead_FirstSession'),
                              getString('Device_TableHead_LastSession'),
                              getString('Device_TableHead_LastIP'),
                              getString('Device_TableHead_MAC'),
                              getString('Device_TableHead_Status'),
                              getString('Device_TableHead_MAC_full'),
                              getString('Device_TableHead_LastIPOrder'),
                              getString('Device_TableHead_Rowid'),
                              getString('Device_TableHead_Parent_MAC'),
                              getString('Device_TableHead_Connected_Devices'),
                              getString('Device_TableHead_Location'),
                              getString('Device_TableHead_Vendor'),
                              getString('Device_TableHead_Port')
                            ];

  // Read parameters & Initialize components
  showSpinner();
  main();


// -----------------------------------------------------------------------------
function main () {

  handleLoadingDialog()

  // get from cookie if available (need to use decodeURI as saved as part of URI in PHP)
  cookieColumnsVisibleStr = decodeURI(getCookie("Front_Devices_Columns_Visible")).replaceAll('%2C',',')  

  defaultValue = cookieColumnsVisibleStr == "" ? columnsStr : cookieColumnsVisibleStr;

  // get visible columns
  $.get('php/server/parameters.php?action=get&expireMinutes=525600&defaultValue='+defaultValue+'&parameter=Front_Devices_Columns_Visible&skipcache', function(data) {

    handle_locked_DB(data)
    
    // save which columns are in the Devices page visible
    tableColumnVisible = numberArrayFromString(data);

    // get from cookie if available (need to use decodeURI as saved as part of URI in PHP)
    cookieColumnsOrderStr = decodeURI(getCookie("Front_Devices_Columns_Order")).replaceAll('%2C',',')

    defaultValue = cookieColumnsOrderStr == "" ? columnsStr : cookieColumnsOrderStr;    

    // get the custom order specified by the user
    $.get('php/server/parameters.php?action=get&expireMinutes=525600&defaultValue='+defaultValue+'&parameter=Front_Devices_Columns_Order&skipcache', function(data) {

      handle_locked_DB(data)
    
      // save the columns order in the Devices page 
      tableColumnOrder = numberArrayFromString(data);

      html = '';
                                  
      for(index = 0; index < tableColumnOrder.length; index++)
      {
        html += '<th>' + headersDefaultOrder[tableColumnOrder[index]] + '</th>';
      }

      $('#tableDevices tr').html(html);   

      // get parameter value
      $.get('php/server/parameters.php?action=get&defaultValue=50&parameter='+ parTableRows, function(data) {
        var result = JSON.parse(data);

        result = parseInt(result, 10)

        if (Number.isInteger (result) ) {
            tableRows = result;  
        }

        // get parameter value
        $.get('php/server/parameters.php?action=get&defaultValue=[[3,"desc"],[0,"asc"]]&parameter='+ parTableOrder, function(data) {
          var result = JSON.parse(data);
          result = JSON.parse(result);

          

          if (Array.isArray (result) ) {
            tableOrder = result;
          }

          // Initialize components with parameters

          initializeDatatable(getUrlAnchor('my'));


          
          // check if data outdated and show spinner if so
          handleLoadingDialog()


        });
      });
    });
   });
}

// -----------------------------------------------------------------------------
// mapping the default order to the user specified one
function mapIndx(oldIndex)
{
  for(i=0;i<tableColumnOrder.length;i++)
  {
    if(tableColumnOrder[i] == oldIndex)
    {
      return i;
    }
  }
}

//------------------------------------------------------------------------------
//  Query total numbers of Devices by status
//------------------------------------------------------------------------------
function getDevicesTotals(devicesData) {

  let resultJSON = "";

  if (getCache("getDevicesTotals") !== "") {
    resultJSON = getCache("getDevicesTotals");
  } else {
    // combined query
    const devices = filterDataByStatus(devicesData, 'my');
    const connectedDevices = filterDataByStatus(devicesData, 'connected');
    const favoritesDevices = filterDataByStatus(devicesData, 'favorites');
    const newDevices = filterDataByStatus(devicesData, 'new');
    const downDevices = filterDataByStatus(devicesData, 'down');
    const archivedDevices = filterDataByStatus(devicesData, 'archived');


    $('#devicesMy').html        (devices.length);
    $('#devicesConnected').html  (connectedDevices.length);
    $('#devicesFavorites').html  (favoritesDevices.length);
    $('#devicesNew').html        (newDevices.length);
    $('#devicesDown').html       (downDevices.length);
    $('#devicesArchived').html   (archivedDevices.length);

    // save to cache
    setCache("getDevicesTotals", resultJSON);
  }  

  // console.log(resultJSON);
}

// -----------------------------------------------------------------------------
// Define a function to filter data based on deviceStatus
function filterDataByStatus(data, status) {
  return data.filter(function(item) {
    switch (status) {
      case 'my':
        to_display = getSetting('UI_MY_DEVICES');
        
        let result = true;

        if (!to_display.includes('down') && item.dev_PresentLastScan === 0 && item.dev_AlertDeviceDown !== 0) {
            result = false;
        } else if (!to_display.includes('new') && item.dev_NewDevice === 1) {
            result = false;
        } else if (!to_display.includes('archived') && item.dev_Archived === 1) {
            result = false;
        } else if (!to_display.includes('offline') && item.dev_PresentLastScan === 0) {
            result = false;
        } else if (!to_display.includes('online') && item.dev_PresentLastScan === 1) {
            result = false;
        }  

        return result; // Include all items for 'my' status
      case 'connected':
        return item.dev_PresentLastScan === 1;
      case 'favorites':
        return item.dev_Favorite === 1;
      case 'new':
        return item.dev_NewDevice === 1;
      case 'down':
        return (item.dev_PresentLastScan === 0 && item.dev_AlertDeviceDown  !== 0) || item.dev_PresentLastScan === 0;
      case 'archived':
        return item.dev_Archived === 1;
      default:
        return true; // Include all items for unknown statuses
    }
  });
}

// -----------------------------------------------------------------------------
function getDeviceStatus(item)
{
  
  if(item.dev_NewDevice === 1)
  {
    return 'New';
  }
  else if(item.dev_PresentLastScan === 1)
  {
    return 'On-line';
  }
  else if(item.dev_PresentLastScan === 0 && item.dev_AlertDeviceDown  !== 0)
  {
    return 'Down';
  }
  else if(item.dev_Archived === 1)
  {
    return 'Archived';
  }
  else if(item.dev_PresentLastScan === 0)
  {
    return 'Off-line';
  }

  return "Unknown status"
}

// -----------------------------------------------------------------------------
function initializeDatatable (status) {

  if(!status)
  {
    status = 'my'
  }

  // Save status selected
  deviceStatus = status;

  // Define color & title for the status selected
  switch (deviceStatus) {
    case 'my':        tableTitle = getString('Device_Shortcut_AllDevices');  color = 'aqua';    break;
    case 'connected':  tableTitle = getString('Device_Shortcut_Connected');   color = 'green';   break;
    case 'favorites':  tableTitle = getString('Device_Shortcut_Favorites');   color = 'yellow';  break;
    case 'new':        tableTitle = getString('Device_Shortcut_NewDevices');  color = 'yellow';  break;
    case 'down':       tableTitle = getString('Device_Shortcut_DownAlerts');  color = 'red';     break;
    case 'archived':   tableTitle = getString('Device_Shortcut_Archived');    color = 'gray';    break;
    default:           tableTitle = getString('Device_Shortcut_Devices');     color = 'gray';    break;
  } 

  // Set title and color
  $('#tableDevicesTitle')[0].className = 'box-title text-'+ color;
  $('#tableDevicesBox')[0].className = 'box box-'+ color;
  $('#tableDevicesTitle').html (tableTitle);


  for(i = 0; i < tableColumnOrder.length; i++)
  {    
    // hide this column if not in the tableColumnVisible variable (we need to keep the MAC address (index 11) for functionality reasons)    
    if(tableColumnVisible.includes(tableColumnOrder[i]) == false)
    {
      tableColumnHide.push(mapIndx(tableColumnOrder[i]));
    }    
  }

  $.get('api/table_devices.json?nocache=' + Date.now(), function(result) {      
    
    // query data
    getDevicesTotals(result.data);      
    
    // Filter the data based on deviceStatus
    var filteredData = filterDataByStatus(result.data, deviceStatus);

    // Convert JSON data into the desired format
    var dataArray = {
        data: filteredData.map(function(item) {
            var originalRow = [
                item.dev_Name || "",
                item.dev_Owner || "",
                item.dev_DeviceType || "",
                item.dev_Icon || "",
                item.dev_Favorite || "",
                item.dev_Group || "",
                // ---
                item.dev_FirstConnection || "",
                item.dev_LastConnection || "",
                item.dev_LastIP || "",
                (isRandomMAC(item.dev_MAC)) || "", // Check if randomized MAC
                getDeviceStatus(item) || "",
                item.dev_MAC || "", // hidden
                formatIPlong(item.dev_LastIP) || "", // IP orderable
                item.rowid || "",
                item.dev_Network_Node_MAC_ADDR || "",
                getNumberOfChildren(item.dev_MAC, result.data) || 0,
                item.dev_Location || "",
                item.dev_Vendor || "",
                item.dev_Network_Node_port || 0
            ];

            var newRow = [];

            // reorder data based on user-defined columns order
            for (index = 0; index < tableColumnOrder.length; index++) {
                newRow.push(originalRow[tableColumnOrder[index]]);
            }

            return newRow;
        })
    };

    
    // TODO displayed columns


    // Check if the DataTable already exists
    if ($.fn.dataTable.isDataTable('#tableDevices')) {
      // The DataTable exists, so destroy it
      var table = $('#tableDevices').DataTable();
      table.clear().destroy();
    }

    var table=
    $('#tableDevices').DataTable({
      'data'         : dataArray["data"],
      'paging'       : true,
      'lengthChange' : true,
      'lengthMenu'   : [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, getString('Device_Tablelenght_all')]],
      'searching'    : true,

      'ordering'     : true,
      'info'         : true,
      'autoWidth'    : false,

      // Parameters
      'pageLength'   : tableRows,
      'order'        : tableOrder,   
      'select'       : true, // Enable selection   

      'columnDefs'   : [
        {visible:   false,         targets: tableColumnHide },      
        {className: 'text-center', targets: [mapIndx(3), mapIndx(4), mapIndx(9), mapIndx(10), mapIndx(15), mapIndx(18)] },      
        {width:     '80px',        targets: [mapIndx(6), mapIndx(7), mapIndx(15)] },      
        {width:     '30px',        targets: [mapIndx(10), mapIndx(13), mapIndx(18)] },      
        {orderData: [mapIndx(12)],          targets: mapIndx(8) },

        // Device Name
        {targets: [mapIndx(0)],
          'createdCell': function (td, cellData, rowData, row, col) {      
              
              // console.log(cellData)      
              $(td).html ('<b class="anonymizeDev"><a href="deviceDetails.php?mac='+ rowData[mapIndx(11)] +'" class="">'+ cellData +'</a></b>');
        } },

        // Connected Devices       
        {targets: [mapIndx(15)],
          'createdCell': function (td, cellData, rowData, row, col) {         
            // check if this is a network device
            if(getSetting("NETWORK_DEVICE_TYPES").includes(`'${rowData[mapIndx(2)]}'`)   )
            {
              $(td).html ('<b><a href="./network.php?mac='+ rowData[mapIndx(11)] +'" class="">'+ cellData +'</a></b>');
            }
            else
            {
              $(td).html (`<i class="fa-solid fa-xmark" title="${getString("Device_Table_Not_Network_Device")}"></i>`)
            }
              
        } },

        // Icon      
        {targets: [mapIndx(3)],
          'createdCell': function (td, cellData, rowData, row, col) {
            if (!emptyArr.includes(cellData)){
              $(td).html (cellData);
            } else {
              $(td).html ('');
            }
        } },

        // Full MAC      
        {targets: [mapIndx(11)],
          'createdCell': function (td, cellData, rowData, row, col) {
            if (!emptyArr.includes(cellData)){
              $(td).html ('<span class="anonymizeMac">'+cellData+'</span>');
            } else {
              $(td).html ('');
            }
        } },
        
        // IP address      
        {targets: [mapIndx(12)],
          'createdCell': function (td, cellData, rowData, row, col) {
            if (!emptyArr.includes(cellData)){
              $(td).html ('<span class="anonymizeIp">'+cellData+'</span>');
            } else {
              $(td).html ('');
            }
        } },
        
        // Favorite      
        {targets: [mapIndx(4)],
          'createdCell': function (td, cellData, rowData, row, col) {
            if (cellData == 1){
              $(td).html ('<i class="fa fa-star text-yellow" style="font-size:16px"></i>');
            } else {
              $(td).html ('');
            }
        } },
          
        // Dates      
        {targets: [mapIndx(6), mapIndx(7)],
          'createdCell': function (td, cellData, rowData, row, col) {
            $(td).html (translateHTMLcodes (cellData));
        } },

        // Random MAC      
        {targets: [mapIndx(9)],
          'createdCell': function (td, cellData, rowData, row, col) {
            // console.log(cellData)
            if (cellData == 1){
              $(td).html ('<i data-toggle="tooltip" data-placement="right" title="Random MAC" style="font-size: 16px;" class="text-yellow glyphicon glyphicon-random"></i>');
            } else {
              $(td).html ('');
            }
        } },

        // Status color      
        {targets: [mapIndx(10)],
          'createdCell': function (td, cellData, rowData, row, col) {

            // console.log(cellData)
            switch (cellData) {
              case 'Down':      color='red';              break;
              case 'New':       color='yellow';           break;
              case 'On-line':   color='green';            break;
              case 'Off-line':  color='gray text-white';  break;
              case 'Archived':  color='gray text-white';  break;
              default:          color='aqua';             break;
            };
        
            $(td).html ('<a href="deviceDetails.php?mac='+ rowData[mapIndx(11)] +'" class="badge bg-'+ color +'">'+ cellData.replace('-', '') +'</a>');
        } },
      ],
      
      // Processing
      'processing'  : true,
      'language'    : {
        processing: '<table> <td width="130px" align="middle">Loading...</td><td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw"></td> </table>',
        emptyTable: 'No data',
        "lengthMenu": "<?= lang('Device_Tablelenght');?>",
        "search":     "<?= lang('Device_Searchbox');?>: ",
        "paginate": {
            "next":       "<?= lang('Device_Table_nav_next');?>",
            "previous":   "<?= lang('Device_Table_nav_prev');?>"
        },
        "info":           "<?= lang('Device_Table_info');?>",
      }
    });

    // Save cookie Rows displayed, and Parameters rows & order
    $('#tableDevices').on( 'length.dt', function ( e, settings, len ) {
      setParameter (parTableRows, len);
    } );
      
    $('#tableDevices').on( 'order.dt', function () {
      setParameter (parTableOrder, JSON.stringify (table.order()) );
      setCache ('devicesList', getDevicesFromTable(table) );
    } );

    $('#tableDevices').on( 'search.dt', function () {
      setCache ('devicesList', getDevicesFromTable(table) ); 
    } );

    // add multi-edit button
    $('#multiEditPlc').append(
        `<button type="submit" id="multiEdit" class="btn btn-primary" style="display:none" onclick="multiEditDevices();">
          <i class="fa fa-pencil pointer" ></i>  ${getString("Device_MultiEdit")}
        </button>`)

    // Event listener for row selection in DataTable
    $('#tableDevices').on('click', 'tr', function (e) {
      setTimeout(function(){
          // Check if any row is selected
          var anyRowSelected = $('#tableDevices tr.selected').length > 0;

          console.log(anyRowSelected);

          // Toggle visibility of element with ID 'multiEdit'
          $('#multiEdit').toggle(anyRowSelected);
      }, 200);


      
    });

    hideSpinner();

  });  
};


// -----------------------------------------------------------------------------
// Gets a JSON list of rowID and mac from the displayed table in the UI
function getDevicesFromTable(table)
{  
  rowIDs = table.column(mapIndx(13), { 'search': 'applied' }).data().toArray()  //   
  rowMACs = table.column(mapIndx(11), { 'search': 'applied' }).data().toArray() // 
  rowNames = table.column(mapIndx(0), { 'search': 'applied' }).data().toArray() // 
  rowTypes = table.column(mapIndx(2), { 'search': 'applied' }).data().toArray() // 
  rowIcons = table.column(mapIndx(3), { 'search': 'applied' }).data().toArray() // 
  rowParentMAC = table.column(mapIndx(14), { 'search': 'applied' }).data().toArray() // 
  rowStatus = table.column(mapIndx(10), { 'search': 'applied' }).data().toArray() // 

  result = []

  rowIDs.map(function(rowID, index){
    result.push({
                  "rowid": rowID, 
                  "mac"  : rowMACs[index], 
                  "name" : rowNames[index],
                  "type" : rowTypes[index],
                  "icon" : rowIcons[index],
                  "parentMac" : rowParentMAC[index],
                  "status" : rowStatus[index] })
  })

  return JSON.stringify (result)
}


// -----------------------------------------------------------------------------
function getNumberOfChildren(mac, devices)
{
  childrenCount = 0;

  $.each(devices, function(index, dev) {

    if(dev.dev_Network_Node_MAC_ADDR != null && dev.dev_Network_Node_MAC_ADDR.trim() == mac.trim())
    {
      childrenCount++;        
    }    
    
  });

  return childrenCount;
}

// -----------------------------------------------------------------------------
function handleLoadingDialog(needsReload = false)
{

  // console.log('needsReload:');
  // console.log(needsReload); 

  $.get('log/execution_queue.log?nocache=' + Date.now(), function(data) {     

    if(data.includes("update_api|devices"))
    {       
      showSpinner("devices_old")

      setTimeout(handleLoadingDialog(true), 1000);

    } else if (needsReload)
    {    
      location.reload();     
    }else
    {
      // hideSpinner();     
    }      

  })
  
}

// -----------------------------------------------------------------------------
// Function collects selected devices in the DataTable and redirects the user to 
// the Miantenance section with a 'macs' query string identifying selected devices 
function multiEditDevices()
{
  rows  = $('#tableDevices')[0].rows

  // Initialize an empty array to store selected rows
  var selectedRows = [];

  console.log($('#tableDevices')[0].rows);
  
  // Loop through each row in the HTML collection
  for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      // Check if the row has the 'selected' class
      if (row.classList.contains('selected')) {
          // If selected, push the row's data to the selectedRows array
          selectedRows.push(row);
      }
  }

  // Now, selectedRows contains all selected rows
  console.log(selectedRows);

  var devicesDataTableData = $('#tableDevices').dataTable().fnGetData();

  var selectedDevices = [];

  for (var i = 0; i < selectedRows.length; i++) {
    selectedDevices.push(devicesDataTableData[selectedRows[i]._DT_RowIndex]);    
  }

  // Now, selectedDevices contains all selected devices
  console.log(selectedDevices);

  macs = ""

  for (var i = 0; i < selectedDevices.length; i++) {
    macs += selectedDevices[i][mapIndx(11)] + ",";  // [11] == MAC    
  }

  // redirect to the Maintenance section
  window.location.href = window.location.origin + '/maintenance.php#tab_multiEdit?macs=' + macs.slice(0, -1);
}

</script>

