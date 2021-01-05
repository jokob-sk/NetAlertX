<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/header.php';
?>

<!-- Page ------------------------------------------------------------------ -->
  <div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
      <h1 id="pageTitle">
         Presence by Devices
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
          <a href="#" onclick="javascript: queryPresence('all');">
            <div class="small-box bg-aqua pa-small-box-aqua">
              <div class="inner">
  
                <h4>All Devices</h4>
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
          <a href="#" onclick="javascript: queryPresence('connected');">
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
          <a href="#" onclick="javascript: queryPresence('new');">
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
          <a href="#" onclick="javascript: queryPresence('down');">
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

<!-- Calendar -------------------------------------------------------------- -->
      <div class="row">
        <div class="col-lg-12 col-sm-12 col-xs-12">
          <div id="tableDevicesBox" class="box" style="min-height: 500px">
            <div class="box-header">
              <h3 id="tableDevicesTitle" class="box-title text-gray">Devices</h3>
            </div>


            <div class="box-body table-responsive">
              <!-- spinner -->
              <div id="loading" style="display: none">
                <div class="pa_semitransparent-panel"></div>
                <div class="panel panel-default pa_spinner">
                  <table><td width="130px" align="middle">Loading...</td><td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw"></td></table>
                </div>
              </div>

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
<!-- iCkeck -->
  <link rel="stylesheet" href="lib/AdminLTE/plugins/iCheck/all.css">
  <script src="lib/AdminLTE/plugins/iCheck/icheck.min.js"></script>

<!-- Datatable -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/datatables.net-bs/css/dataTables.bootstrap.min.css">
  <script src="lib/AdminLTE/bower_components/datatables.net/js/jquery.dataTables.min.js"></script>
  <script src="lib/AdminLTE/bower_components/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>

<!-- fullCalendar -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/fullcalendar/dist/fullcalendar.min.css">
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/fullcalendar/dist/fullcalendar.print.min.css" media="print">
  <script src="lib/AdminLTE/bower_components/moment/moment.js"></script>
  <script src="lib/AdminLTE/bower_components/fullcalendar/dist/fullcalendar.min.js"></script>

<!-- fullCalendar Scheduler -->
  <link href="lib/fullcalendar-scheduler/scheduler.min.css" rel="stylesheet">
  <script src="lib/fullcalendar-scheduler/scheduler.min.js"></script>  

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
    initializeiCheck();
    initializeCalendar();
    periodChanged();
  });

  // Force re-render calendar on tab change (bugfix for render error at left panel)
  $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function (nav) {
    if ($(nav.target).attr('href') == '#panPresence') {
      $('#calendar').fullCalendar('rerenderEvents');
    }
  });


// -----------------------------------------------------------------------------
function periodChanged () {
  // Requery totals and list
  queryTotals();
  queryPresence(deviceStatus);
}


// -----------------------------------------------------------------------------
function initializeiCheck () {
  // Default
  $('input').iCheck({
    checkboxClass: 'icheckbox_flat-blue',
    radioClass:    'iradio_flat-blue',
    increaseArea:  '20%'
  });

  // readonly
  $('#readonlyblock input').iCheck({
    checkboxClass: 'icheckbox_flat-blue',
    radioClass:    'iradio_flat-blue',
    increaseArea:  '-100%'
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

    resourceLabelText : 'Devices',
    resourceAreaWidth : '160px',
    slotWidth         : '1px',

    resourceOrder     : '-favorite,title',

    schedulerLicenseKey: 'CC-Attribution-NonCommercial-NoDerivatives',
    // schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',

    views: {
      timelineYear: {
        type              : 'timeline',
        duration          : { year: 1 },
        buttonText        : 'year',
        slotLabelFormat   : 'MMM',
        // Hack to show partial day events not as fullday events
        slotDuration      : {minutes: 44641}
      },

      timelineQuarter: {
        type              : 'timeline',
        duration          : { month: 3 },
        buttonText        : 'quarter',
        slotLabelFormat   : 'MMM',
        // Hack to show partial day events not as fullday events
        slotDuration      : {minutes: 44641}
      },

      timelineMonth: {
        type              : 'timeline',
        duration          : { month: 1 },
        buttonText        : 'month',
        slotLabelFormat   : 'D',
        // Hack to show partial day events not as fullday events
        slotDuration      : '24:00:01'
      },

      timelineWeek: {
        type              : 'timeline',
        duration          : { week: 1 },
        buttonText        : 'week',
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
         } 

      if (date.day() == 0) {
        cell.addClass('fc-sun'); };
                        
      if (date.day() == 6) {
        cell.addClass('fc-sat'); };

      if (date.format('YYYY-MM-DD') == moment().format('YYYY-MM-DD')) {
          cell.addClass ('fc-today'); };
    },
    
    resourceRender: function (resourceObj, labelTds, bodyTds) {
      labelTds.find('span.fc-cell-text').html ('<b><a href="deviceDetails.php?mac='+ resourceObj.id+ '&period='+ period +'" class="">'+ resourceObj.title +'</a></b>');

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
function queryPresence (status) {
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

  $('#calendar').fullCalendar ('option', 'resources', 'php/server/devices.php?action=calendar&status='+ deviceStatus +'&period='+ period);
  $('#calendar').fullCalendar ('refetchResources');
  // Query calendar
//    resources         : 'https://fullcalendar.io/demo-resources.json',
//    events            : 'https://fullcalendar.io/demo-events.json?with-resources',

  $('#calendar').fullCalendar('removeEventSources');
  $('#calendar').fullCalendar('addEventSource', { url: 'php/server/events.php?action=calendarPresence&period='+ period });
};

</script>
