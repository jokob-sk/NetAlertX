<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  deviceDetails.php - Front module. Device management page
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
      <?php require 'php/templates/notification.php'; ?>

      <h1 id="pageTitle">
        &nbsp<small>Quering device info...</small>
      </h1>

      <!-- period selector -->
      <span class="breadcrumb" style="top: 0px;">
        <select class="form-control" id="period" onchange="javascript: periodChanged();">
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

<!-- top small box 1 ------------------------------------------------------- -->
      <div class="row">

        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabDetails').trigger('click')">
            <div class="small-box bg-aqua pa-small-box-aqua">

              <div class="inner">
                <h4>Current Status</h4>
                <h3 id="deviceStatus" style="margin-left: 0em"> -- </h3>
              </div>

              <div class="icon"> <i id="deviceStatusIcon" class=""></i> </div>
              <div class="small-box-footer"> Details <i class="fa fa-arrow-circle-right"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 2 ------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabSessions').trigger('click');">
            <div class="small-box bg-green pa-small-box-green">

              <div class="inner">
                <h4>Sessions</h4>
                <h3 id="deviceSessions"> -- </h3>
              </div>

              <div class="icon"> <i class="fa fa-plug"></i> </div>
              <div class="small-box-footer"> Details <i class="fa fa-arrow-circle-right"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 3 ------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabPresence').trigger('click')">
            <div  class="small-box bg-yellow pa-small-box-yellow">

              <div class="inner">
                <h4 id="deviceEventsTitle"> Presence </h4> 
                <h3 id="deviceEvents" style="margin-left: 0em"> -- </h3>
              </div>

              <div id="deviceEventsIcon" class="icon"> <i class="fa fa-calendar"></i> </div>
              <div class="small-box-footer"> Details <i class="fa fa-arrow-circle-right"></i> </div>
            </div>
          </a>
        </div>

<!--  top small box 4 ------------------------------------------------------ -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabEvents').trigger('click');">
            <div  class="small-box bg-red pa-small-box-red">

              <div class="inner">
                <h4>Down Alerts</h4>
                <h3 id="deviceDownAlerts"> -- </h3>
              </div>

              <div class="icon"> <i class="fa fa-warning"></i> </div>
              <div class="small-box-footer"> Details <i class="fa fa-arrow-circle-right"></i> </div>
            </div>
          </a>
        </div>

      </div>
      <!-- /.row -->

<!-- tab control------------------------------------------------------------ -->
      <div class="row">
        <div class="col-lg-12 col-sm-12 col-xs-12">
        <!-- <div class="box-transparent"> -->

          <div id="navDevice" class="nav-tabs-custom">
            <ul class="nav nav-tabs" style="fon t-size:16px;">
              <li> <a id="tabDetails"  href="#panDetails"  data-toggle="tab"> Details  </a></li>
              <li> <a id="tabSessions" href="#panSessions" data-toggle="tab"> Sessions </a></li>
              <li> <a id="tabPresence" href="#panPresence" data-toggle="tab"> Presence </a></li>
              <li> <a id="tabEvents"   href="#panEvents"   data-toggle="tab"> Events   </a></li>
            </ul>
            <div class="tab-content" style="min-height: 430px">

<!-- tab page 1 ------------------------------------------------------------ -->
<!--
              <div class="tab-pane fade in active" id="panDetails">
-->
              <div class="tab-pane fade" id="panDetails">

                <div class="row">
    <!-- column 1 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua">Main Info</h4>
                    <div class="box-body form-horizontal">

                      <!-- MAC -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">MAC</label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtMAC" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Name -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Name</label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtName" type="text" value="--">
                        </div>
                      </div>

                      <!-- Owner -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Owner</label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtOwner" type="text" value="--">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownOwner" class="dropdown-menu dropdown-menu-right">
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Type -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Type</label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtDeviceType" type="text" value="--">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false" >
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownDeviceType" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtDeviceType','Smartphone')"> Smartphone </a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtDeviceType','Laptop')">     Laptop     </a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtDeviceType','PC')">         PC         </a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtDeviceType','Others')">     Others     </a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Vendor -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Vendor</label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtVendor" type="text" value="--">
                        </div>
                      </div>

                      <!-- Favorite -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Favorite</label>
                        <div class="col-sm-9" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkFavorite" type="checkbox">
                        </div>
                      </div>

                      <!-- Group -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Group</label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtGroup" type="text" value="--">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownGroup" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtGroup','Always On')"> Always On </a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtGroup','Friends')">   Friends   </a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtGroup','Personal')">  Personal  </a></li>
                                <li class="divider"></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtGroup','Others')">    Others    </a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Location -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Location</label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtLocation" type="text" value="--">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownLocation" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtLocation','Bathroom')">    Bathroom</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtLocation','Bedroom')">     Bedroom</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtLocation','Hall')">        Hall</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtLocation','Kitchen')">     Kitchen</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtLocation','Living room')"> Living room</a></li>
                                <li class="divider"></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtLocation','Others')">      Others</a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Comments -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Comments</label>
                        <div class="col-sm-9">
                          <textarea class="form-control" rows="3" id="txtComments"></textarea>
                        </div>
                      </div>

                    </div>          
                  </div>          

    <!-- column 2 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua">Session Info</h4>
                    <div class="box-body form-horizontal">

                      <!-- Status -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Status</label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtStatus" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- First Session -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">First Session</label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtFirstConnection" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Last Session -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Last Session</label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtLastConnection" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Last IP -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Last IP</label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtLastIP" type="text" readonly value="--">
                        </div>
                      </div>

                      <!-- Static IP -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Static IP</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkStaticIP" type="checkbox">
                        </div>
                      </div>
      
                    </div>
                  </div>

    <!-- column 3 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua">Events & Alerts config</h4>
                    <div class="box-body form-horizontal">

                      <!-- Scan Cycle -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Scan Cycle</label>
                        <div class="col-sm-7">
                          <div class="input-group">
                            <input class="form-control" id="txtScanCycle" type="text" value="--" readonly style="background-color: #fff;">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false" id="dropdownButtonScanCycle">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownScanCycle" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtScanCycle','1 min')">   Scan 1' every 5'</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtScanCycle','15 min');"> Scan 12' every 15'</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtScanCycle','0 min');">  Don't Scan</a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Alert events -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Alert All Events</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkAlertEvents" type="checkbox">
                        </div>
                      </div>
      
                      <!-- Alert Down -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Alert Down</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox red hidden" id="chkAlertDown" type="checkbox">
                        </div>
                      </div>

                      <!-- Skip Notifications -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label" style="padding-top: 0px; padding-left: 0px;">Skip repeated notifications during</label>
                        <div class="col-sm-7">
                          <div class="input-group">
                            <input class="form-control" id="txtSkipRepeated" type="text" value="--" readonly style="background-color: #fff;">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false" id="dropdownButtonSkipRepeated">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownSkipRepeated" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtSkipRepeated','0 h (notify all events)');"> 0 h (notify all events)</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtSkipRepeated','1 h');">                     1 h</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtSkipRepeated','8 h');">                     8 h</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtSkipRepeated','24 h');">                    24 h</a></li>
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtSkipRepeated','168 h (one week)');">        168 h (one week)</a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- New Device -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label">New Device:</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox orange hidden" id="chkNewDevice" type="checkbox">
                        </div>
                      </div>

                    </div>
                  </div>

                  <!-- Buttons -->
                  <div class="col-xs-12">
                    <button type="button" class="btn btn-primary pull-right" style="padding: 10px; min-width: 90px;"                                              id="btnSave"    onclick="setDeviceData()">     Save </button>
                    <button type="button" class="btn btn-default pull-right" style="padding: 10px; min-width: 90px; margin-right:10px;"                           id="btnRestore" onclick="getDeviceData(true)"> Reset Changes </button>
                    <button type="button" class="btn bg-default pull-right"  style="padding: 10px; min-width: 90px; margin-right:10px; background-color:#ffd080;" id="btnDelete"  onclick="askDeleteDevice()">   Delete Device </button>
                  </div>

                </div>
              </div>                                                                         

<!-- tab page 2 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panSessions">

                <!-- Datatable Session -->
                <table id="tableSessions" class="table table-bordered table-hover table-striped ">
                  <thead>
                  <tr>
                    <th>Order</th>
                    <th>Connection</th>
                    <th>Disconnection</th>
                    <th>Duration</th>
                    <th>IP</th>
                    <th>Additional info</th>
                  </tr>
                  </thead>
                </table>
              </div>

<!-- tab page 3 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panPresence">

                  <!-- spinner -->
                  <div id="loading" style="display: none">
                    <div class="pa_semitransparent-panel"></div>
                    <div class="panel panel-default pa_spinner">
                      <table><td width="130px" align="middle">Loading...</td><td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw"></td></table>
                    </div>
                  </div>

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
                    Hide Connection Events
                  </label>
                </div>
                
                <!-- Datatable Events -->
                <table id="tableEvents" class="table table-bordered table-hover table-striped ">
                  <thead>
                  <tr>
                    <th>Date</th>
                    <th>Event type</th>
                    <th>IP</th>
                    <th>Additional info</th>
                  </tr>
                  </thead>
                </table>
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


<!-- page script ----------------------------------------------------------- -->
<script>

  var mac                 = '';
  var parPeriod           = 'Front_Details_Period';
  var parTab              = 'Front_Details_Tab';
  var parSessionsRows     = 'Front_Details_Sessions_Rows';
  var parEventsRows       = 'Front_Details_Events_Rows';
  var parEventsHide       = 'Front_Details_Events_Hide';
  var period              = '1 month';
  var tab                 = 'tabDetails'
  var sessionsRows        = 10;
  var eventsRows          = 10;
  var eventsHide          = true;
  var skipRepeatedItems   = ['0 h (notify all events)', '1 h', '8 h', '24 h', '168 h (one week)'];

  // Read parameters & Initialize components
  main();


// -----------------------------------------------------------------------------
function main () {
  // Initialize MAC
  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has ('mac') == true) {
    mac = urlParams.get ('mac');
  } else {
    $('#pageTitle').html ('Device not found');
  }

  // get parameter value
  $.get('php/server/parameters.php?action=get&parameter='+ parPeriod, function(data) {
    var result = JSON.parse(data);
    if (result) {
      period = result;
      $('#period').val(period);
    }

    // get parameter value
    $.get('php/server/parameters.php?action=get&parameter='+ parTab, function(data) {
      var result = JSON.parse(data);
      if (result) {
        tab = result;
      }
  
      // get parameter value
      $.get('php/server/parameters.php?action=get&parameter='+ parSessionsRows, function(data) {
        var result = JSON.parse(data);
        if (Number.isInteger (result) ) {
            sessionsRows = result;
        }
  
        // get parameter value
        $.get('php/server/parameters.php?action=get&parameter='+ parEventsRows, function(data) {
          var result = JSON.parse(data);
          if (Number.isInteger (result) ) {
              eventsRows = result;
          }
    
          // get parameter value
          $.get('php/server/parameters.php?action=get&parameter='+ parEventsHide, function(data) {
            var result = JSON.parse(data);
            if (result) {
                eventsHide = result;
                $('#chkHideConnectionEvents')[0].checked = eval(eventsHide == 'true');
            }
  
            // Initialize components with parameters
            initializeTabs();
            initializeiCheck();
            initializeCombos();
            initializeDatatables();
            initializeCalendar();
      
            // query data
            getDeviceData(true);
            getSessionsPresenceEvents();
  
            // Force re-render calendar on tab change
            // (bugfix for render error at left panel)
            $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function (nav) {
              if ($(nav.target).attr('href') == '#panPresence') {
                $('#calendar').fullCalendar('rerenderEvents');
              }
            });
  
          });
        });
      });
    });
  });
}


// -----------------------------------------------------------------------------
function initializeTabs () {
  // Activate panel
  $('.nav-tabs a[id='+ tab +']').tab('show');

  //   Not necessary if first panel is not active
  //   // Force show first panel
  //   var panel = $('.nav-tabs a[id='+ tab +']').attr('href');
  //   panel = panel.substring(1);
  //   var element = $('#'+panel)[0];
  //   element.classList.add('in');
  //   element.classList.add('active');

  // When changed save new current tab
  $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    setParameter (parTab, $(e.target).attr('id'));
  });
}

// -----------------------------------------------------------------------------
function initializeiCheck () {
   // Blue
   $('input[type="checkbox"].blue').iCheck({
     checkboxClass: 'icheckbox_flat-blue',
     radioClass:    'iradio_flat-blue',
     increaseArea:  '20%'
   });

  // Orange
  $('input[type="checkbox"].orange').iCheck({
    checkboxClass: 'icheckbox_flat-orange',
    radioClass:    'iradio_flat-orange',
    increaseArea:  '20%'
  });

  // Red
  $('input[type="checkbox"].red').iCheck({
    checkboxClass: 'icheckbox_flat-red',
    radioClass:    'iradio_flat-red',
    increaseArea:  '20%'
  });

  // When toggle iCheck
  $('input').on('ifToggled', function(event){
    // Hide / Show Events
    if (event.currentTarget.id == 'chkHideConnectionEvents') {
      getDeviceEvents();
      setParameter (parEventsHide, event.currentTarget.checked);
    } else {
      // Activate save & restore
      activateSaveRestoreData();
    }
  });
}


// -----------------------------------------------------------------------------
function initializeCombos () {
  // Initialize combos with queries
  initializeCombo ( $('#dropdownOwner')[0],       'getOwners',       'txtOwner');
  initializeCombo ( $('#dropdownDeviceType')[0],  'getDeviceTypes',  'txtDeviceType');
  initializeCombo ( $('#dropdownGroup')[0],       'getGroups',       'txtGroup');
  initializeCombo ( $('#dropdownLocation')[0],    'getLocations',    'txtLocation');

  // Initialize static combos
  initializeComboSkipRepeated ();
}

function initializeCombo (HTMLelement, queryAction, txtDataField) {
  // get data from server
  $.get('php/server/devices.php?action='+queryAction, function(data) {
    var listData = JSON.parse(data);
    var order = 1;

    HTMLelement.innerHTML = ''
    // for each item
    listData.forEach(function (item, index) {
      // insert line divisor
      if (order != item['order']) {
        HTMLelement.innerHTML += '<li class="divider"></li>';
        order = item['order'];
      }

      // add dropdown item
      HTMLelement.innerHTML +=
        '<li><a href="javascript:void(0)" onclick="setTextValue(\''+
        txtDataField +'\',\''+ item['name'] +'\')">'+ item['name'] + '</a></li>'
    });
  });
}


function initializeComboSkipRepeated () {
  // find dropdown menu element
  HTMLelement = $('#dropdownSkipRepeated')[0];
  HTMLelement.innerHTML = ''

  // for each item
  skipRepeatedItems.forEach(function (item, index) {
    // add dropdown item
    HTMLelement.innerHTML += ' <li><a href="javascript:void(0)" ' +
      'onclick="setTextValue(\'txtSkipRepeated\',\'' + item + '\');">'+
      item +'</a></li>';
  });
}

function findSkipRepeated (value='0') {
  var itemSelected = skipRepeatedItems[0];

  // for each item
  skipRepeatedItems.forEach(function (item, index) {
    if (item.split(' ')[0] == value) {
      itemSelected = item;
    }
  });
  return itemSelected;
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
      processing: '<table><td width="130px" align="middle">Loading...</td>'+
                  '<td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw">'+
                  '</td></table>',
      emptyTable: 'No data'
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
      processing: '<table><td width="130px" align="middle">Loading...</td>'+
                  '<td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw">'+
                  '</td></table>',
      emptyTable: 'No data'
    }
  });

  // Save Parameters rows & order when changed
  $('#tableSessions').on( 'length.dt', function ( e, settings, len ) {
    setParameter (parSessionsRows, len);

    // Sync Rows in both datatables
    // if ( $('#tableEvents').DataTable().page.len() != len) {
    //   $('#tableEvents').DataTable().page.len( len ).draw();
    // }
  } );
  
  $('#tableEvents').on( 'length.dt', function ( e, settings, len ) {
    setParameter (parEventsRows, len);

    // Sync Rows in both datatables
    // if ( $('#tableSessions').DataTable().page.len() != len) {
    //   $('#tableSessions').DataTable().page.len( len ).draw();
    // }
  } );
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

    header: {
      left            : 'prev,next today',
      center          : 'title',
      right           : 'agendaYear,agendaMonth,agendaWeek'
    },

    views: {
      agendaYear: {
        type               : 'agenda',
        duration           : { year: 1 },
        buttonText         : 'year',
        columnHeaderFormat : ''
      },

      agendaMonth: {
        type               : 'agenda',
        duration           : { month: 1 },
        buttonText         : 'month',
        columnHeaderFormat : 'D'
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
      $(element).tooltip({container: 'body', placement: 'right',
                          title: event.tooltip});
      // element.attr ('title', event.tooltip);  // Alternative tooltip
    },
      
    loading: function( isLoading, view ) {
        if (isLoading) {
          $('#loading').show();
        } else {
          $('#loading').hide();
        }
    }

  })
}


// -----------------------------------------------------------------------------
function periodChanged () {
  // Save Parameter Period
  period = $('#period').val();
  setParameter (parPeriod, period);

  // Requery Device data
  getDeviceData(true);
  getSessionsPresenceEvents();
}


// -----------------------------------------------------------------------------
function getDeviceData (updatePanelData=false) {
  // stop timer
  stopTimerRefreshData();

  // Check MAC
  if (mac == '') {
    return;
  }

  // get data from server
  $.get('php/server/devices.php?action=getDeviceData&mac='+ mac + '&period='+ period, function(data) {

    var deviceData = JSON.parse(data);

    // check device exists
    if (deviceData['dev_MAC'] == null) {
      $('#pageTitle').html ('Device not found: <small>'+ mac +'</small>');

      $('#txtMAC').val             ('--');
      $('#txtName').val            ('--');
      $('#txtOwner').val           ('--');
      $('#txtDeviceType').val      ('--');
      $('#txtVendor').val          ('--');

      $('#chkFavorite').iCheck     ('uncheck'); 
      $('#txtGroup').val           ('--');
      $('#txtLocation').val        ('--');
      $('#txtComments').val        ('--');

      $('#txtFirstConnection').val ('--');
      $('#txtLastConnection').val  ('--');
      $('#txtLastIP').val          ('--');
      $('#txtStatus').val          ('--');
      $('#chkStaticIP').iCheck     ('uncheck'); 
  
      $('#txtScanCycle').val       ('--');
      $('#chkAlertEvents').iCheck  ('uncheck') 
      $('#chkAlertDown').iCheck    ('uncheck') 
      $('#txtSkipRepeated').val    ('--');
      $('#chkNewDevice').iCheck    ('uncheck') 

      // Deactivate controls
      $('#panDetails :input').attr('disabled', true);

    } else {

      // Name
      if (deviceData['dev_Owner'] == null || deviceData['dev_Owner'] == '' ||
      (deviceData['dev_Name']).indexOf (deviceData['dev_Owner']) != -1 )  {
        $('#pageTitle').html (deviceData['dev_Name']);
      } else {
        $('#pageTitle').html (deviceData['dev_Name'] + ' ('+ deviceData['dev_Owner'] +')');
      }
  
      // Status
      $('#deviceStatus').html (deviceData['dev_Status']);
      switch (deviceData['dev_Status']) {
        case 'On-line':   icon='fa fa-check';    color='text-green';   break;
        case 'Off-line':  icon='fa fa-close';    color='text-gray';    break;
        case 'Down':      icon='fa fa-warning';  color='text-red';     break;
        case null:        icon='fa fa-warning';  color='text-red';     $('#deviceStatus').html ('???');  break;
        default:          icon='';               color='';             break;
      };
      $('#deviceStatus')[0].className = color;
      $('#deviceStatusIcon')[0].className = icon +' '+ color;
  
      // Totals
      $('#deviceSessions').html   (deviceData['dev_Sessions'].toLocaleString());
      $('#deviceDownAlerts').html (deviceData['dev_DownAlerts'].toLocaleString());
  
      // Presence
      $('#deviceEventsTitle').html ('Presence');
      $('#deviceEventsIcon').html  ('<i class="fa fa-calendar">');
      if (deviceData['dev_PresenceHours'] == null || deviceData['dev_PresenceHours'] < 0) {
        $('#deviceEvents').html ('0 h.');
      } else {
        $('#deviceEvents').html (deviceData['dev_PresenceHours'].toLocaleString() +' h.');
      }
  
      // Device info
      if (updatePanelData) {
        $('#txtMAC').val                             (deviceData['dev_MAC']);
        $('#txtName').val                            (deviceData['dev_Name']);
        $('#txtOwner').val                           (deviceData['dev_Owner']);
        $('#txtDeviceType').val                      (deviceData['dev_DeviceType']);
        $('#txtVendor').val                          (deviceData['dev_Vendor']);
  
        if (deviceData['dev_Favorite'] == 1)         {$('#chkFavorite').iCheck('check');} 
        $('#txtGroup').val                           (deviceData['dev_Group']);
        $('#txtLocation').val                        (deviceData['dev_Location']);
        $('#txtComments').val                        (deviceData['dev_Comments']);
  
        $('#txtFirstConnection').val                 (deviceData['dev_FirstConnection']);
        $('#txtLastConnection').val                  (deviceData['dev_LastConnection']);
        $('#txtLastIP').val                          (deviceData['dev_LastIP']);
        $('#txtStatus').val                          (deviceData['dev_Status']);
        if (deviceData['dev_StaticIP'] == 1)         {$('#chkStaticIP').iCheck('check');} 
    
        $('#txtScanCycle').val                       (deviceData['dev_ScanCycle'] +' min');
        if (deviceData['dev_AlertEvents'] == 1)      {$('#chkAlertEvents').iCheck('check');} 
        if (deviceData['dev_AlertDeviceDown'] == 1)  {$('#chkAlertDown').iCheck('check');} 
        $('#txtSkipRepeated').val                    (findSkipRepeated (deviceData['dev_SkipRepeated']));
        if (deviceData['dev_NewDevice'] == 1)        {$('#chkNewDevice').iCheck('check');} 

        deactivateSaveRestoreData ();
      }

    }

    // Timer for refresh data
    newTimerRefreshData (getDeviceData);
  });
}


// -----------------------------------------------------------------------------
function setDeviceData () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // update data to server
  $.get('php/server/devices.php?action=setDeviceData&mac='+ mac
    + '&name='           + $('#txtName').val()
    + '&owner='          + $('#txtOwner').val()
    + '&type='           + $('#txtDeviceType').val()
    + '&vendor='         + $('#txtVendor').val()
    + '&favorite='       + ($('#chkFavorite')[0].checked * 1)
    + '&group='          + $('#txtGroup').val()
    + '&location='       + $('#txtLocation').val()
    + '&comments='       + $('#txtComments').val()
    + '&staticIP='       + ($('#chkStaticIP')[0].checked * 1)
    + '&scancycle='      + $('#txtScanCycle').val().split(' ')[0]
    + '&alertevents='    + ($('#chkAlertEvents')[0].checked * 1)
    + '&alertdown='      + ($('#chkAlertDown')[0].checked * 1)
    + '&skiprepeated='   + $('#txtSkipRepeated').val().split(' ')[0]
    + '&newdevice='      + ($('#chkNewDevice')[0].checked * 1)
    , function(msg) {

    deactivateSaveRestoreData ();
    showMessage (msg);
  });
}


// -----------------------------------------------------------------------------
function askDeleteDevice () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Ask delete device
  showModal ('Delete Device', 'Are you sure you want to delete this device?',
    'Cancel', 'Delete', 'deleteDevice');
}


// -----------------------------------------------------------------------------
function deleteDevice () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Delete device
  $.get('php/server/devices.php?action=deleteDevice&mac='+ mac, function(msg) {
    showMessage (msg);
  });

  // Deactivate controls
  $('#panDetails :input').attr('disabled', true);
}


// -----------------------------------------------------------------------------
function getSessionsPresenceEvents () {
  // Define Sessions datasource and query dada
  $('#tableSessions').DataTable().ajax.url('php/server/events.php?action=getDeviceSessions&mac=' + mac +'&period='+ period).load();
  
  // Define Presence datasource and query data
  $('#calendar').fullCalendar('removeEventSources');
  $('#calendar').fullCalendar('addEventSource',
    { url: 'php/server/events.php?action=getDevicePresence&mac=' + mac +'&period='+ period });

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
  activateSaveRestoreData();
});

$(document).on('input', 'textarea', function() {
  activateSaveRestoreData();
});


// -----------------------------------------------------------------------------
function activateSaveRestoreData () {
  $('#btnRestore').removeAttr ('disabled');
  $('#btnSave').removeAttr ('disabled');
}


function deactivateSaveRestoreData () {
  //$('#btnRestore').attr ('disabled','');
  $('#btnSave').attr ('disabled','');
}


// -----------------------------------------------------------------------------
function setTextValue (textElement, textValue) {
  $('#'+textElement).val (textValue);
  activateSaveRestoreData ();
}

</script>
