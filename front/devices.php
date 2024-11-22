<!--
#---------------------------------------------------------------------------------#
#  NetAlertX                                                                       #
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
  require 'php/components/graph_online_history.php';

  // check permissions
  $dbPath = "../db/app.db";
  $confPath = "../config/app.conf";

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

      <!-- Tile toggle cards ------------------------------------------------------- -->
      <div class="row" id="TileCards">
        <!-- Placeholder ------------------------------------------------------- -->

      </div>

<!-- Device presence / Activity Chart ------------------------------------------------------- -->

      <div class="row" id="DevicePresence">
          <div class="col-md-12">
          <div class="box" id="clients">
              <div class="box-header with-border">
                <h3 class="box-title"><?= lang('Device_Shortcut_OnlineChart');?> </h3> 
              </div>
              <div class="box-body">
                <div class="chart">
                  <script src="lib/AdminLTE/bower_components/chart.js/Chart.js?v=<?php include 'php/templates/version.php'; ?>"></script>
                  <!-- The online history chart is rendered here -->
                  <canvas id="OnlineChart" style="width:100%; height: 150px;  margin-bottom: 15px;"></canvas>
                </div>
              </div>
              <!-- /.box-body -->
            </div>
          </div>
      </div>

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
  var tableRows       = getCookie ("nax_parTableRows") == "" ? 10 : getCookie ("nax_parTableRows") ;
  var tableOrder      = getCookie ("nax_parTableOrder") == "" ? [[3,'desc'], [0,'asc']] : JSON.parse(getCookie ("nax_parTableOrder")) ;
  
  var tableColumnHide = [];
  var tableColumnOrder = [];
  var tableColumnVisible = [];
  headersDefaultOrder = [];
  missingNumbers = [];

  // Read parameters & Initialize components
  callAfterAppInitialized(main)
  showSpinner();

// -----------------------------------------------------------------------------
function main () {

  showSpinner();

  // render tiles
  getDevicesTotals();

  //initialize the table headers in the correct order
  var availableColumns = getSettingOptions("UI_device_columns").split(",");
  headersDefaultOrder = availableColumns.map(val => getString(val));
  var selectedColumns = JSON.parse(getSetting("UI_device_columns").replace(/'/g, '"'));

  // generate default order lists of given length
  var columnsStr = JSON.stringify(Array.from({ length: headersDefaultOrder.length }, (_, i) => i));
  tableColumnOrder = Array.from({ length: headersDefaultOrder.length }, (_, i) => i);
  tableColumnVisible = [];

  // Initialize tableColumnVisible by including all columns from selectedColumns, preserving their order.
  tableColumnVisible = selectedColumns.map(column => availableColumns.indexOf(column)).filter(index => index !== -1);

  // Add any columns from availableColumns that are not in selectedColumns to the end.
  const remainingColumns = availableColumns.map((column, index) => index).filter(index => !tableColumnVisible.includes(index));

  // Combine both arrays.
  tableColumnOrder = tableColumnVisible.concat(remainingColumns);

  // Generate the full array of numbers from 0 to totalLength - 1 of tableColumnOrder
  const fullArray = Array.from({ length: tableColumnOrder.length }, (_, i) => i);

  // Filter out the elements already present in inputArray
  missingNumbers = fullArray.filter(num => !tableColumnVisible.includes(num));

  // Concatenate the inputArray with the missingNumbers
  tableColumnOrder = [...tableColumnVisible, ...missingNumbers];

  // Initialize components with parameters
  initializeDatatable(getUrlAnchor('my_devices'));
  
  // check if data outdated and show spinner if so
  handleLoadingDialog()
  
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
function getDevicesTotals() {
  // Check cache first
  let resultJSON = getCache("getDevicesTotals");

  if (resultJSON !== "") {
    resultJSON = JSON.parse(resultJSON);
    processDeviceTotals(resultJSON);
  } else {
    // Fetch data via AJAX
    $.ajax({
      url: "/api/table_devices_tiles.json",
      type: "GET",
      dataType: "json",
      success: function(response) {
        if (response && response.data) {
          resultJSON = response.data[0]; // Assuming the structure {"data": [ ... ]}
          
          // Save the result to cache
          setCache("getDevicesTotals", JSON.stringify(resultJSON));

          // Process the fetched data
          processDeviceTotals(resultJSON);
        } else {
          console.error("Invalid response format from API");
        }
      },
      error: function(xhr, status, error) {
        console.error("Failed to fetch devices data:", error);
      }
    });
  }
}

function processDeviceTotals(devicesData) {
  // Define filter conditions and corresponding objects
  const filters = [
    { status: 'my_devices', color: 'bg-aqua',   label: getString('Device_Shortcut_AllDevices'), icon: 'fa-laptop' },
    { status: 'all',        color: 'bg-aqua',   label: getString('Gen_All_Devices'),            icon: 'fa-laptop' },
    { status: 'connected',  color: 'bg-green',  label: getString('Device_Shortcut_Connected'),  icon: 'fa-plug' },
    { status: 'favorites',  color: 'bg-yellow', label: getString('Device_Shortcut_Favorites'),  icon: 'fa-star' },
    { status: 'new',        color: 'bg-yellow', label: getString('Device_Shortcut_NewDevices'), icon: 'fa-plus' },
    { status: 'down',       color: 'bg-red',    label: getString('Device_Shortcut_DownOnly'),   icon: 'fa-warning' },
    { status: 'archived',   color: 'bg-gray',   label: getString('Device_Shortcut_Archived'),   icon: 'fa-eye-slash' },
    { status: 'offline',    color: 'bg-gray',   label: getString('Gen_Offline'),                icon: 'fa-xmark' }
  ];

  // Initialize an empty array to store the final objects
  let dataArray = [];

  // Loop through each filter condition
  filters.forEach(filter => {
    // Get count directly from API response data
    let count = devicesData[filter.status] || 0;

    // Check any condition to skip adding the object to dataArray
    if (
      (['', 'False'].includes(getSetting('UI_hide_empty')) || (getSetting('UI_hide_empty') == "True" && count > 0)) &&
      (getSetting('UI_shown_cards') == "" || getSetting('UI_shown_cards').includes(filter.status))
    ) {
      dataArray.push({
        onclickEvent: `forceLoadUrl('devices.php#${filter.status}')`,
        color: filter.color,
        title: count,
        label: filter.label,
        icon: filter.icon
      });
    }
  });

  // Render info boxes/tile cards
  renderInfoboxes(dataArray);
}

//------------------------------------------------------------------------------
//  Render the info boxes/tiles on top
function renderInfoboxes(customData) {
    $.ajax({
      url: 'php/components/tile_cards.php', // PHP script URL
      type: 'POST', // Use POST method to send data
      dataType: 'html', // Expect HTML response
      data: { items: JSON.stringify(customData) }, // Send customData as JSON
      success: function(response) {
        $('#TileCards').html(response); // Replace container content with fetched HTML
      },
      error: function(xhr, status, error) {
        console.error('Error fetching infoboxes:', error);
      }
    });
  }

// -----------------------------------------------------------------------------
// Define a function to filter data based on deviceStatus
function filterDataByStatus(data, status) {
  return data.filter(function(item) {
    switch (status) {
      case 'my_devices':
        to_display = getSetting('UI_MY_DEVICES');
        
        let result = true;

        if (!to_display.includes('down') && item.devPresentLastScan === 0 && item.devAlertDown !== 0) {
            result = false;
        } else if (!to_display.includes('new') && item.devIsNew === 1) {
            result = false;
        } else if (!to_display.includes('archived') && item.devIsArchived === 1) {
            result = false;
        } else if (!to_display.includes('offline') && item.devPresentLastScan === 0) {
            result = false;
        } else if (!to_display.includes('online') && item.devPresentLastScan === 1) {
            result = false;
        }  

        return result; // Include all items for 'my_devices' status
      case 'connected':
        return item.devPresentLastScan === 1;
      case 'favorites':
        return item.devFavorite === 1;
      case 'new':
        return item.devIsNew === 1;
      case 'offline':
        return item.devPresentLastScan === 0;
      case 'down':
        return (item.devPresentLastScan === 0 && item.devAlertDown  !== 0);
      case 'archived':
        return item.devIsArchived === 1;
      default:
        return true; // Include all items for unknown statuses
    }
  });
}


// Map column index to column name for GraphQL query
function mapColumnIndexToFieldName(index, tableColumnVisible) {
  // the order is important, don't change it!
  const columnNames = [
    "devName", 
    "devOwner", 
    "devType", 
    "devIcon", 
    "devFavorite", 
    "devGroup", 
    "devFirstConnection", 
    "devLastConnection", 
    "devLastIP", 
    "devIsRandomMac",   // resolved on the fly
    "devStatus", // resolved on the fly
    "devMac", 
    "devIpLong", //formatIPlong(device.devLastIP) || "",  // IP orderable
    "rowid", 
    "devParentMAC", 
    "devParentChildrenCount",  // resolved on the fly
    "devLocation",
    "devVendor", 
    "devParentPort", 
    "devGUID", 
    "devSyncHubNode", 
    "devSite", 
    "devSSID", 
    "devSourcePlugin",
    "devPresentLastScan",
    "devAlertDown"
  ];

  // console.log("OrderBy: " + columnNames[tableColumnOrder[index]]);  

  return columnNames[tableColumnOrder[index]] || null;
}


// ---------------------------------------------------------
function initializeDatatable (status) {
  
  if(!status)
  {
    status = 'my_devices'
  }

  // Save status selected
  deviceStatus = status;

  // Define color & title for the status selected
  switch (deviceStatus) {
    case 'my_devices': tableTitle = getString('Device_Shortcut_AllDevices');  color = 'aqua';    break;
    case 'connected':  tableTitle = getString('Device_Shortcut_Connected');   color = 'green';   break;
    case 'all':        tableTitle = getString('Gen_All_Devices');             color = 'aqua';    break;
    case 'favorites':  tableTitle = getString('Device_Shortcut_Favorites');   color = 'yellow';  break;
    case 'new':        tableTitle = getString('Device_Shortcut_NewDevices');  color = 'yellow';  break;
    case 'down':       tableTitle = getString('Device_Shortcut_DownOnly');    color = 'red';     break;
    case 'archived':   tableTitle = getString('Device_Shortcut_Archived');    color = 'gray';    break;
    case 'offline':    tableTitle = getString('Gen_Offline');                 color = 'gray';    break;
    default:           tableTitle = getString('Device_Shortcut_Devices');     color = 'gray';    break;
  } 

  // Set title and color
  $('#tableDevicesTitle')[0].className = 'box-title text-'+ color;
  $('#tableDevicesBox')[0].className = 'box box-'+ color;
  $('#tableDevicesTitle').html (tableTitle);

  // render table headers
  html = '';
                                  
  for(index = 0; index < tableColumnOrder.length; index++)
  {
    html += '<th>' + headersDefaultOrder[tableColumnOrder[index]] + '</th>';
  }

  $('#tableDevices tr').html(html);  

  hideUIelements("UI_DEV_SECTIONS")

  for(i = 0; i < tableColumnOrder.length; i++)
  {    
    // hide this column if not in the tableColumnVisible variable (we need to keep the MAC address (index 11) for functionality reasons)    
    if(tableColumnVisible.includes(tableColumnOrder[i]) == false)
    {
      tableColumnHide.push(mapIndx(tableColumnOrder[i]));
    }    
  }

  // todo: dynamically filter based on status


  var table = $('#tableDevices').DataTable({
    "serverSide": true,
    "processing": true,
    "ajax": {
      "url": 'php/server/query_graphql.php',  // PHP endpoint that proxies to the GraphQL server
      "type": "POST",
      "contentType": "application/json",
      "data": function (d) {
        // Construct GraphQL query with pagination and sorting options
        let graphqlQuery = `
          query devices($options: PageQueryOptionsInput) {
            devices(options: $options) {
              devices {
                rowid
                devMac
                devName
                devOwner
                devType
                devVendor
                devFavorite
                devGroup
                devComments
                devFirstConnection
                devLastConnection
                devLastIP
                devStaticIP
                devScan
                devLogEvents
                devAlertEvents
                devAlertDown
                devSkipRepeated
                devLastNotification
                devPresentLastScan
                devIsNew
                devIsRandomMac
                devLocation
                devIsArchived
                devParentMAC
                devParentPort
                devIcon
                devGUID
                devSite
                devSSID
                devSyncHubNode
                devSourcePlugin
                devStatus
                devParentChildrenCount
                devIpLong
              }
              count
            }
          }
        `;

        console.log(d);
               

        // Prepare query variables for pagination, sorting, and search
        let query = {
          "operationName": null,
          "query": graphqlQuery,
          "variables": {
            "options": {
              "page": Math.floor(d.start / d.length) + 1,  // Page number (1-based)
              "limit": parseInt(d.length, 10),  // Page size (ensure it's an integer)
              "sort": d.order && d.order[0] ? [{
                "field": mapColumnIndexToFieldName(d.order[0].column, tableColumnVisible),  // Sort field from DataTable column
                "order": d.order[0].dir.toUpperCase()  // Sort direction (ASC/DESC)
              }] : [],  // Default to an empty array if no sorting is defined
              "search": d.search.value,  // Search query
              "status": deviceStatus
            }
            
          }
        };

        return JSON.stringify(query);  // Send the JSON request
      },
      "dataSrc": function (json) {
        console.log(json);

        // Set the total number of records for pagination
        json.recordsTotal = json.devices.count || 0;
        json.recordsFiltered = json.devices.count || 0;

        return json.devices.devices.map(device => {
            // Convert each device record into the required DataTable row format
            // Order has to be the same as in the UI_device_columns setting options
            const originalRow = [
                device.devName || "",
                device.devOwner || "",
                device.devType || "",
                device.devIcon || "",
                device.devFavorite || "",
                device.devGroup || "",
                device.devFirstConnection || "",
                device.devLastConnection || "",
                device.devLastIP || "",
                device.devIsRandomMac || "",  // Custom logic for randomized MAC
                device.devStatus || "",
                device.devMac || "",  // hidden
                device.devIpLong || "",  // IP orderable
                device.rowid || "",
                device.devParentMAC || "",
                device.devParentChildrenCount || 0,
                device.devLocation || "",
                device.devVendor || "",
                device.devParentPort || "",
                device.devGUID || "",
                device.devSyncHubNode || "",
                device.devSite || "",
                device.devSSID || "",
                device.devSourcePlugin || "",
                device.devPresentLastScan || "",
                device.devAlertDown || ""
            ];

            const newRow = [];
            // Reorder data based on user-defined columns order
            for (let index = 0; index < tableColumnOrder.length; index++) {
                newRow.push(originalRow[tableColumnOrder[index]]);
            }

            return newRow;
        });
      }
    },
    'paging'       : true,
    'lengthChange' : true,
    'lengthMenu'   : [[10, 25, 50, 100, 500, 100000], [10, 25, 50, 100, 500, getString('Device_Tablelenght_all')]],
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
            $(td).html (atob(cellData));
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
      {targets: [mapIndx(8)],
        'createdCell': function (td, cellData, rowData, row, col) {
            if (!emptyArr.includes(cellData)){
              $(td).html (`<span class="anonymizeIp">
                            <a href="http://${cellData}" class="pointer" target="_blank">
                                ${cellData}
                            </a>
                            <a href="https://${cellData}" class="pointer" target="_blank">
                                <i class="fa fa-lock "></i>
                            </a>
                          <span>`);
            } else {
              $(td).html ('');
            }
        } 
      },
      // IP address (ordeable)     
      {targets: [mapIndx(12)],
        'createdCell': function (td, cellData, rowData, row, col) {
            if (!emptyArr.includes(cellData)){
              $(td).html (`<span class="anonymizeIp">${cellData}<span>`);
            } else {
              $(td).html ('');
            }
        } 
      },
      
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
          var result = cellData.toString(); // Convert to string
          if (result.includes("+")) { // Check if timezone offset is present
              result = result.split('+')[0]; // Remove timezone offset
          }
          $(td).html (translateHTMLcodes (result));
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
          
          tmp_devPresentLastScan = rowData[mapIndx(24)]
          tmp_devAlertDown = rowData[mapIndx(25)]

          if (tmp_devPresentLastScan == 1)
          {
            css = "green text-white statusOnline"
            icon = '<i class="fa-solid fa-plug"></i>'
          } else if (tmp_devPresentLastScan != 1 && tmp_devAlertDown == 1)
          {
            css = "red text-white statusDown"
            icon = '<i class="fa-solid fa-triangle-exclamation"></i>'
          } else if(tmp_devPresentLastScan != 1)
          {
            css = "gray text-white statusOffline"
            icon = '<i class="fa-solid fa-xmark"></i>'
          } else
          {
            css = "gray text-white statusUnknown"
            icon = '<i class="fa-solid fa-question"></i>'
          }
      
          $(td).html (`<a href="deviceDetails.php?mac=${rowData[mapIndx(11)]}" class="badge bg-${css}">${icon} ${cellData.replace('-', '')}</a>`);
      } },
    ],
    
    // Processing
    'processing'  : true,
    'language'    : {
      emptyTable: 'No data',
      "lengthMenu": "<?= lang('Device_Tablelenght');?>",
      "search":     "<?= lang('Device_Searchbox');?>: ",
      "paginate": {
          "next":       "<?= lang('Device_Table_nav_next');?>",
          "previous":   "<?= lang('Device_Table_nav_prev');?>"
      },
      "info":           "<?= lang('Device_Table_info');?>",
    },
    initComplete: function (settings, devices) {
      // Handle any additional interactions or event listeners as required

      // Save cookie Rows displayed, and Parameters rows & order
      $('#tableDevices').on( 'length.dt', function ( e, settings, len ) {
            setCookie ("nax_parTableRows", len, 129600); // save for 90 days
          } );
            
          $('#tableDevices').on( 'order.dt', function () {
            setCookie ("nax_parTableOrder", JSON.stringify (table.order()), 129600); // save for 90 days
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

                // Toggle visibility of element with ID 'multiEdit'
                $('#multiEdit').toggle(anyRowSelected);
            }, 100);
            
          });

          
          hideSpinner();
          
    }
    
  });

  
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

  // console.log($('#tableDevices')[0].rows);
  
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
  // console.log(selectedDevices);

  macs = ""

  for (var i = 0; i < selectedDevices.length; i++) {
    macs += selectedDevices[i][mapIndx(11)] + ",";  // [11] == MAC    
  }

  // redirect to the Maintenance section
  window.location.href = window.location.origin + '/maintenance.php#tab_multiEdit?macs=' + macs.slice(0, -1);
}


// -----------------------------------------------------------------------------
// Function collects shown devices from the DataTable  
function getMacsOfShownDevices() {

  rows  = $('#tableDevices')[0].rows
  macs = []

  var devicesDataTableData = $('#tableDevices').dataTable().fnGetData();

  var selectedDevices = [];

  for (var i = 0; i < rows.length; i++) {
    selectedDevices.push(devicesDataTableData[rows[i]._DT_RowIndex]);    
  }

  for (var i = 1; i < selectedDevices.length; i++) {
    macs.push(selectedDevices[i][mapIndx(11)]);  // mapIndx(11) == MAC    
  }

  return macs;
  
}

// -----------------------------------------------------------------------------
// Update cahce with shown devices before navigating away    
window.addEventListener('beforeunload', function(event) {
    // Call your function here
    macs = getMacsOfShownDevices();

    setCache("ntx_visible_macs", macs)
  
});

</script>

