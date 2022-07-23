<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  presence.php - Front module. Device Presence calendar page
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
         <?php echo $pia_lang['Presence_Title'];?>
      </h1>
    </section>

<!-- Main content ---------------------------------------------------------- -->
    <section class="content">

<!-- top small box 1 ------------------------------------------------------- -->
      <div class="row">

        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesPresence('all');">
          <div class="small-box bg-aqua">
            <div class="inner"><h3 id="devicesAll"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Presence_Shortcut_AllDevices'];?></p>
            </div>
            <div class="icon"><i class="fa fa-laptop text-aqua-40"></i></div>
          </div>
          </a>
        </div>

<!-- top small box 2 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesPresence('connected');">
            <div class="small-box bg-green">
              <div class="inner"> <h3 id="devicesConnected"> -- </h3> 
                  <p class="infobox_label"><?php echo $pia_lang['Presence_Shortcut_Connected'];?></p>
              </div>
              <div class="icon"> <i class="fa fa-plug text-green-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 3 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesPresence('favorites');">
            <div  class="small-box bg-yellow">
              <div class="inner"> <h3 id="devicesFavorites"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Presence_Shortcut_Favorites'];?></p>
              </div>
              <div class="icon"> <i class="fa fa-star text-yellow-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 4 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesPresence('new');">
            <div  class="small-box bg-yellow">
              <div class="inner"> <h3 id="devicesNew"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Presence_Shortcut_NewDevices'];?></p>
              </div>
              <div class="icon"> <i class="ion ion-plus-round text-yellow-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 5 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesPresence('down');">
            <div  class="small-box bg-red">
              <div class="inner"> <h3 id="devicesDown"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Presence_Shortcut_DownAlerts'];?></p>
              </div>
              <div class="icon"> <i class="fa fa-warning text-red-40"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 6 ------------------------------------------------------- -->
        <div class="col-lg-2 col-sm-4 col-xs-6">
          <a href="#" onclick="javascript: getDevicesPresence('archived');">
            <div  class="small-box bg-gray top_small_box_gray_text">
              <div class="inner"> <h3 id="devicesHidden"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['Presence_Shortcut_Archived'];?></p>
              </div>
              <div class="icon"> <i class="fa fa-eye-slash text-gray-40"></i> </div>
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
                  <!-- <canvas id="clientsChart" width="800" height="140" class="extratooltipcanvas no-user-select"></canvas> -->
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
  
      <!-- /.row -->

<!-- Calendar -------------------------------------------------------------- -->
      <div class="row">
        <div class="col-lg-12 col-sm-12 col-xs-12">
          <div id="tableDevicesBox" class="box" style="min-height: 500px">

            <!-- box-header -->
            <div class="box-header">
              <h3 id="tableDevicesTitle" class="box-title text-gray">Devices</h3>
            </div>

            <!-- box-body -->
            <div class="box-body table-responsive">

              <!-- spinner -->
              <div id="loading" style="display: none">
                <div class="pa_semitransparent-panel"></div>
                <div class="panel panel-default pa_spinner">
                  <table>
                    <td width="130px" align="middle">Loading...</td>
                    <td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw"></td>
                  </table>
                </div>
              </div>

              <!-- Calendar -->
              <div id="calendar"></div>
            </div>

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
<!-- fullCalendar -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/fullcalendar/dist/fullcalendar.min.css">
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/fullcalendar/dist/fullcalendar.print.min.css" media="print">
  <script src="lib/AdminLTE/bower_components/moment/moment.js"></script>
  <script src="lib/AdminLTE/bower_components/fullcalendar/dist/fullcalendar.min.js"></script>
  <script src="lib/AdminLTE/bower_components/fullcalendar/dist/locale-all.js"></script>

<!-- fullCalendar Scheduler -->
  <link href="lib/fullcalendar-scheduler/scheduler.min.css" rel="stylesheet">
  <script src="lib/fullcalendar-scheduler/scheduler.min.js"></script>




<!-- Dark-Mode Patch -->
<?php
if ($ENABLED_DARKMODE === True) {
   echo '<link rel="stylesheet" href="css/dark-patch-cal.css">';
}
?>

<!-- page script ----------------------------------------------------------- -->
<script>

  var deviceStatus = 'all';

  // Read parameters & Initialize components
  main();


// -----------------------------------------------------------------------------
function main () {
  // Initialize components
  $(function () {
    initializeCalendar();
    getDevicesTotals();
    getDevicesPresence(deviceStatus);
  });

  // Force re-render calendar on tab change (bugfix for render error at left panel)
  $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function (nav) {
    if ($(nav.target).attr('href') == '#panPresence') {
      $('#calendar').fullCalendar('rerenderEvents');
    }
  });
}


// -----------------------------------------------------------------------------
function initializeCalendar () {
  $('#calendar').fullCalendar({
    header: {
      left            : 'prev,next today',
      center          : 'title',
      right           : 'timelineYear,timelineMonth,timelineWeek'
    },
    defaultView       : 'timelineMonth',
    height            : 'auto',
    firstDay          : 1,
    allDaySlot        : false,
    timeFormat        : 'H:mm', 

    resourceLabelText : '<?php echo $pia_lang['Presence_CallHead_Devices'];?>',
    resourceAreaWidth : '160px',
    slotWidth         : '1px',

    resourceOrder     : '-favorite,title',
    locale            : '<?php echo $pia_lang['Presence_CalHead_lang'];?>',

    //schedulerLicenseKey: 'CC-Attribution-NonCommercial-NoDerivatives',
    schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',

    views: {
      timelineYear: {
        type              : 'timeline',
        duration          : { year: 1 },
        buttonText        : '<?php echo $pia_lang['Presence_CalHead_year'];?>',
        slotLabelFormat   : 'MMM',
        // Hack to show partial day events not as fullday events
        slotDuration      : {minutes: 44641}
      },

      timelineQuarter: {
        type              : 'timeline',
        duration          : { month: 3 },
        buttonText        : '<?php echo $pia_lang['Presence_CalHead_quarter'];?>',
        slotLabelFormat   : 'MMM',
        // Hack to show partial day events not as fullday events
        slotDuration      : {minutes: 44641}
      },

      timelineMonth: {
        type              : 'timeline',
        duration          : { month: 1 },
        buttonText        : '<?php echo $pia_lang['Presence_CalHead_month'];?>',
        slotLabelFormat   : 'D',
        // Hack to show partial day events not as fullday events
        slotDuration      : '24:00:01'
      },

      timelineWeek: {
        type              : 'timeline',
        duration          : { week: 1 },
        buttonText        : '<?php echo $pia_lang['Presence_CalHead_week'];?>',
        slotLabelFormat   : 'D',
        slotDuration      : '24:00:01'
      }
    },
     
    // Needed due hack partial day events 23:59:59
    dayRender: function (date, cell) {
      if ($('#calendar').fullCalendar('getView').name == 'timelineYear') {
        cell.removeClass('fc-sat'); 
        cell.removeClass('fc-sun'); 
        return;
      }; 

      if (date.day() == 0) {
        cell.addClass('fc-sun'); };
                        
      if (date.day() == 6) {
        cell.addClass('fc-sat'); };

      if (date.format('YYYY-MM-DD') == moment().format('YYYY-MM-DD')) {
          cell.addClass ('fc-today'); };
    },
    
    resourceRender: function (resourceObj, labelTds, bodyTds) {
      labelTds.find('span.fc-cell-text').html (
      '<b><a href="deviceDetails.php?mac='+ resourceObj.id+ '" class="">'+ resourceObj.title +'</a></b>');

      // Resize heihgt
      // $(".fc-content table tbody tr .fc-widget-content div").addClass('fc-resized-row');
    },
 
    eventRender: function (event, element, view) {
      $(element).tooltip({container: 'body', placement: 'right', title: event.tooltip});
      // element.attr ('title', event.tooltip);  // Alternative tooltip
    },

    loading: function( isLoading, view ) {
        if (isLoading) {
          $("#loading").show();
        } else {
          $("#loading").hide();
        }
    }

  })
}


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
    $('#devicesHidden').html     (totalsDevices[5].toLocaleString());

    // Timer for refresh data
    newTimerRefreshData (getDevicesTotals);
  } );
}


// -----------------------------------------------------------------------------
function getDevicesPresence (status) {
  // Save status selected
  deviceStatus = status;

  // Defini color & title for the status selected
  switch (deviceStatus) {
    case 'all':        tableTitle = '<?php echo $pia_lang['Presence_Shortcut_AllDevices'];?>';    color = 'aqua';    break;
    case 'connected':  tableTitle = '<?php echo $pia_lang['Presence_Shortcut_Connected'];?>';     color = 'green';   break;
    case 'favorites':  tableTitle = '<?php echo $pia_lang['Presence_Shortcut_Favorites'];?>';     color = 'yellow';  break;
    case 'new':        tableTitle = '<?php echo $pia_lang['Presence_Shortcut_NewDevices'];?>';    color = 'yellow';  break;
    case 'down':       tableTitle = '<?php echo $pia_lang['Presence_Shortcut_DownAlerts'];?>';    color = 'red';     break;
    case 'archived':   tableTitle = '<?php echo $pia_lang['Presence_Shortcut_Archived'];?>';      color = 'gray';    break;
    default:           tableTitle = '<?php echo $pia_lang['Presence_Shortcut_Devices'];?>';       color = 'gray';    break;
  } 

  // Set title and color
  $('#tableDevicesTitle')[0].className = 'box-title text-'+ color;
  $('#tableDevicesBox')[0].className = 'box box-'+ color;
  $('#tableDevicesTitle').html (tableTitle);

  // Define new datasource URL and reload
  $('#calendar').fullCalendar ('option', 'resources', 'php/server/devices.php?action=getDevicesListCalendar&status='+ deviceStatus);
  $('#calendar').fullCalendar ('refetchResources');

  $('#calendar').fullCalendar('removeEventSources');
  $('#calendar').fullCalendar('addEventSource', { url: 'php/server/events.php?action=getEventsCalendar' });
};

</script>
