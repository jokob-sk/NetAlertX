<!--
#---------------------------------------------------------------------------------#
#  NetAlertX                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #  
#                                                                                 #
#  deviceDetails.php - Front module. Device management page                       #
#---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
#---------------------------------------------------------------------------------#
-->

<?php
  require 'php/templates/header.php';
?>


<!-- Page ------------------------------------------------------------------ -->
  <div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
      <?php require 'php/templates/notification.php'; ?>

      <h1 id="pageTitle">
        &nbsp<small>Quering device info...</small>
      </h1>

      <!-- period selector -->
      <span class="breadcrumb" style="top: 0px;">
        <select class="form-control" id="period" onchange="javascript: periodChanged();">
          <option value="1 day"><?= lang('DevDetail_Periodselect_today');?></option>
          <option value="7 days"><?= lang('DevDetail_Periodselect_LastWeek');?></option>
          <option value="1 month" selected><?= lang('DevDetail_Periodselect_LastMonth');?></option>
          <option value="1 year"><?= lang('DevDetail_Periodselect_LastYear');?></option>
          <option value="100 years"><?= lang('DevDetail_Periodselect_All');?></option>
        </select>
      </span>
    </section>
    
<!-- Main content ---------------------------------------------------------- -->
    <section class="content">

      <div id="TopSmallBoxes"></div>

<!-- tab control------------------------------------------------------------ -->
      <div class="row">
        <div class="col-lg-12 col-sm-12 col-xs-12">
        <!-- <div class="box-transparent"> -->
          <div id="navDevice" class="nav-tabs-custom">
            <ul class="nav nav-tabs" style="font-size:16px;">
              <li> <a id="tabDetails"  href="#panDetails"  data-toggle="tab"> <?= lang('DevDetail_Tab_Details');?>  </a></li>
              <li> <a id="tabTools"    href="#panTools"    data-toggle="tab"> <?= lang('DevDetail_Tab_Tools');?>    </a></li>
              <li> <a id="tabSessions" href="#panSessions" data-toggle="tab"> <?= lang('DevDetail_Tab_Sessions');?> </a></li>
              <li> <a id="tabPresence" href="#panPresence" data-toggle="tab"> <?= lang('DevDetail_Tab_Presence');?> </a></li>
              <li> <a id="tabEvents"   href="#panEvents"   data-toggle="tab"> <?= lang('DevDetail_Tab_Events');?>   </a></li>              
              <li> <a id="tabPlugins"  href="#panPlugins"  data-toggle="tab"> <?= lang('DevDetail_Tab_Plugins');?>  </a></li>

              <div class="btn-group pull-right">
                <button type="button" class="btn btn-default"  style="padding: 10px; min-width: 30px;"
                  id="btnPrevious" onclick="recordSwitch('prev')"> <i class="fa fa-chevron-left"></i> </button>

                <div class="btn pa-btn-records"  style="padding: 10px; min-width: 30px; margin-left: 1px;"
                  id="txtRecord"     > 0 / 0 </div>

                <button type="button" class="btn btn-default"  style="padding: 10px; min-width: 30px; margin-left: 1px;"
                  id="btnNext"     onclick="recordSwitch('next')"> <i class="fa fa-chevron-right"></i> </button>
              </div>
            </ul>
            
            <div class="tab-content" style="min-height: 430px;">

<!-- tab page 1 ------------------------------------------------------------ -->
<!--
              <div class="tab-pane fade in active" id="panDetails">
-->
              <div class="tab-pane fade" id="panDetails">

                <?php  
                  require 'deviceDetailsEdit.php';
                ?>
                
              </div>                                                                         

<!-- tab page 2 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panSessions">

                <!-- Datatable Session -->
                <table id="tableSessions" class="table table-bordered table-hover table-striped ">
                  <thead>
                  <tr>
                    <th><?= lang('DevDetail_SessionTable_Order');?></th>
                    <th><?= lang('DevDetail_SessionTable_Connection');?></th>
                    <th><?= lang('DevDetail_SessionTable_Disconnection');?></th>
                    <th><?= lang('DevDetail_SessionTable_Duration');?></th>
                    <th><?= lang('DevDetail_SessionTable_IP');?></th>
                    <th><?= lang('DevDetail_SessionTable_Additionalinfo');?></th>
                  </tr>
                  </thead>
                </table>
              </div>

        
<!-- tab page "Tools" ------------------------------------------------------------ -->

              <div class="tab-pane fade" id="panTools">

                <?php  
                  require 'deviceDetailsTools.php';
                ?>
              
		      
              </div>

<!-- tab page 3 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panPresence">                 

                  <!-- Calendar -->
                  <div id="calendar">
                  </div>
              </div>

<!-- tab page 4 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panEvents">

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
              </div>

<!-- tab page 7 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panPlugins">
              

                <?php
                  // Include the other page
                  include 'pluginsCore.php';
                ?>

              </div>

            </div>
            <!-- /.tab-content -->
          </div>
          <!-- /.nav-tabs-custom -->

          <!-- </div> -->
        </div>
        <!-- /.col -->
      </div>
      <!-- /.row -->

    </section>
    <!-- /.content -->
  </div>
  <!-- /.content-wrapper -->


<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>


<!-- ----------------------------------------------------------------------- -->
<!-- iCkeck -->
  <link rel="stylesheet" href="lib/iCheck/all.css">
  <script src="lib/iCheck/icheck.min.js"></script>

<!-- Datatable -->
  <link rel="stylesheet" href="lib/datatables.net-bs/css/dataTables.bootstrap.min.css">
  <script src="lib/datatables.net/js/jquery.dataTables.min.js"></script>
  <script src="lib/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>

<!-- fullCalendar -->
  <link rel="stylesheet" href="lib/fullcalendar/fullcalendar.min.css">
  <link rel="stylesheet" href="lib/fullcalendar/fullcalendar.print.min.css" media="print">
  <script src="lib/moment/moment.js"></script>
  <script src="lib/fullcalendar/fullcalendar.min.js"></script>
  <script src="lib/fullcalendar/locale-all.js"></script>
  <!-- ----------------------------------------------------------------------- -->

  
  <!-- ----------------------------------------------------------------------- -->

<!-- Dark-Mode Patch -->
<?php
switch ($UI_THEME) {
  case "Dark":
    echo '<link rel="stylesheet" href="css/dark-patch-cal.css">';
    break;
  case "System":
    echo '<link rel="stylesheet" href="css/system-dark-patch-cal.css">';
    break;

}
?>

<!-- page script ----------------------------------------------------------- -->
<script >

  // ------------------------------------------------------------

  mac                     = getMac()  // can also be rowID!! not only mac 
  var devicesList         = [];   // this will contain a list the database row IDs of the devices ordered by the position displayed in the UI  


  var pos                 = -1;  
  var parPeriod           = 'Front_Details_Period';
  var parSessionsRows     = 'Front_Details_Sessions_Rows';
  var parEventsRows       = 'Front_Details_Events_Rows';
  var parEventsHide       = 'Front_Details_Events_Hide';
  var period              = '1 month';
  var tab                 = 'tabDetails'
  var sessionsRows        = 10;
  var eventsRows          = 10;
  var eventsHide          = true;
  var skipRepeatedItems   = ['0 h (notify all events)', '1 h', '8 h', '24 h', '168 h (one week)'];
  var selectedTab         = 'tabDetails';
  var emptyArr            = ['undefined', "", undefined, null];


// Call renderSmallBoxes, then main
(async () => {
    await renderSmallBoxes();
    main();
})();

// -----------------------------------------------------------------------------
function main () {

  // Initialize MAC
  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has ('mac') == true) {
    mac = urlParams.get ('mac');
    setCache("naxDeviceDetailsMac", mac); // set cookie
  } else {
    $('#pageTitle').html ('Device not found');
  }

  key ="activeDevicesTab"

  // Activate panel
  if(!emptyArr.includes(getCache(key)))
  {
    selectedTab = getCache(key);
  }

  tab = selectedTab;

  period = '1 day';
  sessionsRows = 50;
  eventsRows = 50;
  $('#chkHideConnectionEvents')[0].checked = eval(eventsHide == 'true');  

  // Initialize components with parameters
  initializeTabs();
  initializeDatatables();
  initializeCalendar();    

  // query data

  getSessionsPresenceEvents();

  // Force re-render calendar on tab change
  // (bugfix for render error at left panel)
  $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function (nav) {
    if ($(nav.target).attr('href') == '#panPresence') {
      $('#calendar').fullCalendar('rerenderEvents');
    }
  });


  // Events tab toggle conenction events
  $('input').on('ifToggled', function(event){
    // Hide / Show Events
    if (event.currentTarget.id == 'chkHideConnectionEvents') {
      getDeviceEvents();
    } else {
      // Activate save & restore
      // activateSaveRestoreData();

      // Ask skip notifications
      // if (event.currentTarget.id == 'chkArchived' ) {
      //   askSkipNotifications();
      // }
    }
  });
       
}



// -----------------------------------------------------------------------------
function initializeDatatables () {
  // Sessions datatable
  $('#tableSessions').DataTable({
    'paging'      : true,
    'lengthChange': true,
    'lengthMenu'   : [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, 'All']],
    'searching'   : true,
    'ordering'    : true,
    'info'        : true,
    'autoWidth'   : false,
    'order'       : [[0,'desc'], [1,'desc']],

    // Parameters
    'pageLength'  : sessionsRows,

    'columnDefs'  : [
        {visible:   false,  targets: [0]},

        // Replace HTML codes
        {targets: [1,2,3,5],
          'createdCell': function (td, cellData, rowData, row, col) {
            $(td).html (translateHTMLcodes (cellData));
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
            $(td).html (translateHTMLcodes (cellData));
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
};


// -----------------------------------------------------------------------------
function initializeCalendar () {
  $('#calendar').fullCalendar({
    editable          : false,
    droppable         : false,
    defaultView       : 'agendaMonth',

    height            : 'auto',
    firstDay          : 1,
    allDaySlot        : false,
    slotDuration      : '02:00:00',
    slotLabelInterval : '04:00:00',
    slotLabelFormat   : 'H:mm',
    timeFormat        : 'H:mm', 
    locale            : '<?= lang('Presence_CalHead_lang');?>',
    header: {
      left            : 'prev,next today',
      center          : 'title',
      right           : 'agendaYear,agendaMonth,agendaWeek'
    },

    views: {
      agendaYear: {
        type               : 'agenda',
        duration           : { year: 1 },
        buttonText         : '<?= lang('Presence_CalHead_year');?>',
        columnHeaderFormat : ''
      },

      agendaMonth: {
        type               : 'agenda',
        duration           : { month: 1 },
        buttonText         : '<?= lang('Presence_CalHead_month');?>',
        columnHeaderFormat : 'D'
      },
      agendaWeek: {
        buttonText         : '<?= lang('Presence_CalHead_week');?>',
      },
      agendaDay: {
        type              : 'agenda',
        duration          : { day: 1 },
        buttonText        : '<?= lang('Presence_CalHead_day');?>',
        slotLabelFormat   : 'H',
        slotDuration      : '01:00:00'
      }
    },

    viewRender: function(view) {
      if (view.name === 'agendaYear') {
        var listHeader  = $('.fc-day-header')[0];
        var listContent = $('.fc-widget-content')[0];

        for (i=0; i < listHeader.length-2 ; i++) {
          listHeader[i].style.borderColor = 'transparent';
          listContent[i+2].style.borderColor = 'transparent';

          if (listHeader[i].innerHTML != '<span></span>') {
            if (i==0) {
              listHeader[i].style.borderLeftColor = '#808080';
            } else {
              listHeader[i-1].style.borderRightColor = '#808080';
              listContent[i+1].style.borderRightColor = '#808080';
            }
            listHeader[i].style.paddingLeft = '10px';
          }   
        };    
      }
    },
 
    columnHeaderText: function(mom) {
      switch ($('#calendar').fullCalendar('getView').name) {
      case 'agendaYear':
        if (mom.date() == 1) {
          return mom.format('MMM');
        } else {
          return '';
        }
        break;
      case 'agendaMonth':
        return mom.date();
        break;
      case 'agendaWeek':
        return mom.format ('ddd D');
        break;
      default:
        return mom.date();
      }
    },

    eventRender: function (event, element) {
      $(element).tooltip({container: 'body', placement: 'bottom',
                          title: event.tooltip});
      // element.attr ('title', event.tooltip);  // Alternative tooltip
    },
      
    loading: function( isLoading, view ) {
        if (isLoading) {
          showSpinner()
        } else {
          // setTimeout(() => {
          //   updateIconPreview($('#txtIcon'))  
          // }, 500);
          
          hideSpinner()
        }
    }

  })
}


// -----------------------------------------------------------------------------
function periodChanged () {
  getSessionsPresenceEvents();
}


// -----------------------------------------------------------------------------
// Left (prev) < > (next) Right toggles at the top right of device details to 
// cycle between devices
function recordSwitch(direction) {

  if(somethingChanged)
  {
    showModalDefaultStrParam ('Unsaved changes', 'Do you want to discard your changes?',
      '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Okay');?>', performSwitch, direction);
  } else
  {    
    performSwitch(direction)
  }
}

// -----------------------------------------------------------------------------

function performSwitch(direction)
{
  somethingChanged = false;

  // Update the global position in the devices list variable 'pos'
  if (direction === "next") {
    if (pos < devicesList.length - 1) {
      pos++;
    }
  } else if (direction === "prev") {
    if (pos > 0) {
      pos--;
    }
  }

  // Get the new MAC address from devicesList
  mac = devicesList[pos].devMac.toString();

  console.log(mac);

  setCache("naxDeviceDetailsMac", mac);

  // Update the query string with the new MAC and refresh the page
  const baseUrl = window.location.href.split('?')[0];
  window.location.href = `${baseUrl}?mac=${encodeURIComponent(mac)}`;

}


// -----------------------------------------------------------------------------
function getSessionsPresenceEvents () {
  // Check MAC in url
  var urlParams = new URLSearchParams(window.location.search);
  mac = urlParams.get ('mac');
  // Define Sessions datasource and query dada
  $('#tableSessions').DataTable().ajax.url('php/server/events.php?action=getDeviceSessions&mac=' + mac +'&period='+ period).load();
  
  // Define Presence datasource and query data
  $('#calendar').fullCalendar('removeEventSources');
  $('#calendar').fullCalendar('addEventSource',
  { url: 'php/server/events.php?action=getDevicePresence&mac=' + mac});

  // Query events
  getDeviceEvents();
}


// -----------------------------------------------------------------------------
function getDeviceEvents () {
  // Define Events datasource and query dada
  hideConnections = $('#chkHideConnectionEvents')[0].checked;
  $('#tableEvents').DataTable().ajax.url(
    'php/server/events.php?action=getDeviceEvents&mac=' + mac +'&period='+ period +'&hideConnections='+ hideConnections).load();
}


// -----------------------------------------------------------------------------
// Activate save & restore on any value change
$(document).on('input', 'input:text', function() {  
  settingsChanged();
});



// -----------------------------------------------------------------------------

function initializeTabs () {  

  key ="activeDevicesTab"

  // Activate panel
  if(!emptyArr.includes(getCache(key)))
  {
    selectedTab = getCache(key);
  }
  $('.nav-tabs a[id='+ selectedTab +']').tab('show');

  // When changed save new current tab
  $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    setCache(key, $(e.target).attr('id'))
  });

  // events on tab change
  $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    var target = $(e.target).attr("href") // activated tab

    // if(target == "#panTools")
    // {
    //   // loadTools();
    // }
  });
}


//-----------------------------------------------------------------------------------

function initTable(tableId, mac){

  // clear table
  $("#"+tableId+" tbody").remove();

  // Events datatable
  $('#'+tableId).DataTable({
  'paging'      : true,
  'lengthChange': true,
  'lengthMenu'   : [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, 'All']],
  'searching'   : true,
  'ordering'    : true,
  'info'        : true,
  'autoWidth'   : false,
  'order'       : [[0,'desc']],

  // Parameters
  'pageLength'  : 50,

  'columnDefs'  : [
      // Replace HTML codes
      {targets: [0],
        'createdCell': function (td, cellData, rowData, row, col) {
          $(td).html (translateHTMLcodes (cellData));
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

  $("#"+tableId).attr("data-mac", mac)

}


//------------------------------------------------------------------------------
//  Render the small boxes on top
async function renderSmallBoxes() {
  
  
    try {
        // Show loading dialog
        showSpinner();

        // Get data from the server
        const response = await fetch(`php/server/devices.php?action=getServerDeviceData&mac=${getMac()}&period=${period}`);
        if (!response.ok) {
            throw new Error(`Error fetching device data: ${response.statusText}`);
        }

        const deviceData = await response.json();
        console.log(deviceData);

        // Prepare custom data
        const customData = [
            {
                "onclickEvent": "$('#tabDetails').trigger('click')",
                "color": "bg-aqua",
                "headerId": "deviceStatus",
                "headerStyle": "margin-left: 0em",
                "labelLang": "DevDetail_Shortcut_CurrentStatus",
                "iconId": "deviceStatusIcon",
                "iconClass": deviceData.devPresentLastScan == 1 ? "fa fa-check text-green" : "fa fa-xmark text-red",
                "dataValue": deviceData.devPresentLastScan == 1 ? getString("Gen_Online") : getString("Gen_Offline")
            },
            {
                "onclickEvent": "$('#tabSessions').trigger('click');",
                "color": "bg-green",
                "headerId": "deviceSessions",
                "headerStyle": "",
                "labelLang": "DevDetail_Shortcut_Sessions",
                "iconId": "",
                "iconClass": "fa fa-plug",
                "dataValue": deviceData.devSessions
            },
            {
                "onclickEvent": "$('#tabPresence').trigger('click')",
                "color": "bg-yellow",
                "headerId": "deviceEvents",
                "headerStyle": "margin-left: 0em",
                "labelLang": "DevDetail_Shortcut_Presence",
                "iconId": "deviceEventsIcon",
                "iconClass": "fa fa-calendar",
                "dataValue": `${deviceData.devPresenceHours}h`
            },
            {
                "onclickEvent": "$('#tabEvents').trigger('click');",
                "color": "bg-red",
                "headerId": "deviceDownAlerts",
                "headerStyle": "",
                "labelLang": "DevDetail_Shortcut_DownAlerts",
                "iconId": "",
                "iconClass": "fa fa-warning",
                "dataValue": deviceData.devDownAlerts
            }
        ];

        // Send data to render small boxes
        const cardResponse = await fetch('php/components/device_cards.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: customData })
        });

        if (!cardResponse.ok) {
            throw new Error(`Error rendering small boxes: ${cardResponse.statusText}`);
        }

        const html = await cardResponse.text();

        $('#TopSmallBoxes').html(html);

    } catch (error) {
        console.error('Error in renderSmallBoxes:', error);
    } finally {
        // Hide loading dialog
        hideSpinner();
    }
}


//-----------------------------------------------------------------------------------

window.onload = function async()
{
  initializeTabs();

}




</script>


