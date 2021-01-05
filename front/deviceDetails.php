<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/header.php';
?>

<!-- Page ------------------------------------------------------------------ -->
  <div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
      <h1 id="pageTitle">
        &nbsp<small>Quering device info...</small>
      </h1>

      <!-- period selector -->
      <span class="breadcrumb text-gray50">
        Sessions, Presence & Alerts period:  

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
          <a href="#" onclick="javascript: $('#tabDetails').trigger('click')">
            <div class="small-box bg-aqua pa-small-box-aqua">
              <div class="inner">
  
                <h4>Current Status</h4>
                <h3 id="deviceStatus" style="margin-left: 0em"> -- </h3>
  
              </div>
              <div class="icon">
                <i id="deviceStatusIcon" class=""></i>
              </div>
              <div class="small-box-footer">
                Details <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>
        </div>

<!-- top small box --------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabSessions').trigger('click');">
            <div class="small-box bg-green pa-small-box-green">
              <div class="inner">
  
                <h4>Sessions</h4>
                <h3 id="deviceSessions"> -- </h3>
  
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
          <a href="#" onclick="javascript: $('#tabPresence').trigger('click')">
            <div  class="small-box bg-yellow pa-small-box-yellow">
              <div class="inner">
  
                <h4 id="deviceEventsTitle">
                  <!-- Events / Presence -->Presence
                </h4> 
                <h3 id="deviceEvents" style="margin-left: 0em"> -- </h3>
  
              </div>
              <div id="deviceEventsIcon" class="icon">
                <i class="fa fa-calendar"></i>
              </div>
              <div class="small-box-footer">
                Details <i class="fa fa-arrow-circle-right"></i>
              </div>
            </div>
          </a>
        </div>

<!--  small box ------------------------------------------------------------ -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabEvents').trigger('click');">
            <div  class="small-box bg-red pa-small-box-red">
              <div class="inner">
  
                <h4>Down Alerts</h4>
                <h3 id="deviceDownAlerts"> -- </h3>
  
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


<!-- tab control------------------------------------------------------------ -->
      <div class="row">
        <div class="col-lg-12 col-sm-12 col-xs-12">
        <!--
        <div class="box-transparent">
        -->

          <div id="navDevice" class="nav-tabs-custom">
            <ul class="nav nav-tabs" style="font-size:16px;">
              <li><a id="tabDetails" href="#panDetails" data-toggle="tab">Details</a></li>
              <li><a id="tabSessions" href="#panSessions" data-toggle="tab">Sessions</a></li>
              <li class="active"><a id="tabPresence" href="#panPresence" data-toggle="tab">Presence</a></li>
              <li><a id="tabEvents"   href="#panEvents" data-toggle="tab">Events</a></li>
            </ul>
            <div class="tab-content" style="min-height: 430px">

<!-- tab page -------------------------------------------------------------- -->
              <div class="tab-pane fade" id="panDetails">

                <div class="row">
                  <!-- Column 1 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua">Main Info</h4>
                    <div class="box-body form-horizontal">

                      <div class="form-group">
                        <label class="col-sm-3 control-label">MAC</label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtMAC" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Name</label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtName" type="text" value="--"'>
                        </div>
                      </div>

      
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Owner</label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtOwner" type="text" value="--">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown"
                                aria-expanded="false">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownOwner" class="dropdown-menu dropdown-menu-right">
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>


                      <div class="form-group">
                        <label class="col-sm-3 control-label">Type</label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtDeviceType" type="text" value="--">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown"
                                aria-expanded="false" >
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownDeviceType" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtDeviceType','Smartphone')">Smartphone</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtDeviceType','Laptop')">Laptop</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtDeviceType','PC')">PC</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtDeviceType','Others')">Others</a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

      
                      <div class="form-group">
                        <label class="col-sm-3 control-label">Vendor</label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtVendor" type="text" value="--">
                        </div>
                      </div>

                      <div class="form-group">
                        <label class="col-sm-3 control-label">Favorite</label>
                        <div class="col-sm-9" style="padding-top:6px;">
                          <input class="checkbox" id="chkFavorite" type="checkbox">
                        </div>
                      </div>


                      <div class="form-group">
                        <label class="col-sm-3 control-label">Group</label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtGroup" type="text" value="--">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown"
                                aria-expanded="false">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownGroup" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtGroup','Always On')">Always On</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtGroup','Friends')">Friends</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtGroup','Personal')">Personal</a></li>
                                <li class="divider"></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtGroup','Others')">Others</a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>


                      <div class="form-group">
                        <label class="col-sm-3 control-label">Comments</label>
                        <div class="col-sm-9">
                          <textarea class="form-control" rows="3" id="txtComments"></textarea>
                        </div>
                      </div>

                    </div>          
                  </div>          

                  <!-- Column 2 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua">Session Info</h4>

                    <div class="box-body form-horizontal">
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Status</label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtStatus" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <div class="form-group">
                        <label class="col-sm-5 control-label">First Session</label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtFirstConnection" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Last Session</label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtLastConnection" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Last IP</label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtLastIP" type="text" readonly value="--">
                        </div>
                      </div>

                      <div class="form-group">
                        <label class="col-sm-5 control-label">Static IP</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox" id="chkStaticIP" type="checkbox" readonly>
                        </div>
                      </div>
      
                    </div>
                  </div>

                  <!-- Column 3 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua">Events & Alerts config</h4>
                    <div class="box-body form-horizontal">

                      <div class="form-group">
                        <label class="col-sm-5 control-label">Scan Cycle</label>
                        <div class="col-sm-7">
                          <div class="input-group">
                            <input class="form-control" id="txtScanCycle" type="text" value="--"
                              readonly style="background-color: #fff;">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown"
                                aria-expanded="false" id="dropdownButtonScanCycle">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownScanCycle" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtScanCycle','1 min')">Scan 1' every 5'</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtScanCycle','15 min');">Scan 12' every 15'</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtScanCycle','0 min');">Don't Scan</a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div class="form-group">
                        <label class="col-sm-5 control-label">Alert All Events</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox" id="chkAlertEvents" type="checkbox" readonly>
                        </div>
                      </div>
      
                      <div class="form-group">
                        <label class="col-sm-5 control-label">Alert Down</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox" id="chkAlertDown" type="checkbox" readonly>
                        </div>
                      </div>


                      <div class="form-group">
                        <label class="col-sm-5 control-label" style="padding-top: 0px; padding-left: 0px;"> 
                          Skip repeated notifications during</label>
                        <div class="col-sm-7">
                          <div class="input-group">
                            <input class="form-control" id="txtSkipRepeated" type="text" value="--"
                              readonly style="background-color: #fff;">
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown"
                                aria-expanded="false" id="dropdownButtonSkipRepeated">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownSkipRepeated" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtSkipRepeated','0 h (notify all events)');">
                                    0 h (notify all events)</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtSkipRepeated','1 h');">1 h</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtSkipRepeated','8 h');">8 h</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtSkipRepeated','24 h');">24 h</a></li>
                                <li><a href="javascript:void(0)"
                                    onclick="setTextValue('txtSkipRepeated','168 h (one week)');">
                                    168 h (one week)</a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                    </div>
                  </div>

                  <div class="col-xs-12">
                    <button class="btn btn-primary pull-right" style="min-width: 100px; margin-left:20px;" id="btnSave" onclick="saveDeviceData()"> Save </button>
                    <button type="button" class="btn btn-default pull-right" style="min-width: 100px;" id="btnRestore" onclick="queryDeviceData(true)"> Restore </button>
                  </div>

                </div>

              </div>

<!-- tab page -------------------------------------------------------------- -->
              <div class="tab-pane fade table-responsive" id="panSessions">
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

<!-- tab page -------------------------------------------------------------- -->
              <div class="tab-pane fade table-responsive in active" id="panPresence" style="position: relative;">
                  <!-- spinner -->
                  <div id="loading" style="display: none">
                    <div class="pa_semitransparent-panel"></div>
                    <div class="panel panel-default pa_spinner">
                      <table><td width="130px" align="middle">Loading...</td><td><i class="ion ion-ios-loop-strong fa-spin fa-2x fa-fw"></td></table>
                    </div>
                  </div>

                  <div id="calendar">
                  </div>
              </div>

<!-- tab page -------------------------------------------------------------- -->
              <div class="tab-pane fade table-responsive" id="panEvents">

                <div class="text-center">
                  <label>
                    <input class="checkbox" id="chkHideConnectionEvents" type="checkbox" checked>
                    Hide Connection Events
                  </label>
                </div>
                
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
          <!-- nav-tabs-custom -->

        <!--
        </div>
        -->
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

// -----------------------------------------------------------------------------
  var period = '';
  var mac = '';
  var skipRepeatedItems = ["0 h (notify all events)", "1 h", "8 h", "24 h", "168 h (one week)"];

  // Initialize MAC
  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has ('mac') == true) {
    mac = urlParams.get ('mac');
  } else {
    $('#pageTitle').html ('Device not found');
  }

  // Initialize period
  if (urlParams.has ('period') == true) {
    document.getElementById('period').value = urlParams.get ('period');
  }

  // Initialize components
  $(function () {
    initializeiCheck();
    initializeAllCombos();
    initializeDatatable();
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
  $('input').on('ifToggled', function(event){
    if (event.currentTarget.id == 'chkHideConnectionEvents') {
      queryEvents();
    } else {
      activateSaveRestoreData();
    }
  });


// -----------------------------------------------------------------------------
  $(document).on('input', 'input:text', function() {
    activateSaveRestoreData();
  });

  $(document).on('input', 'textarea', function() {
    activateSaveRestoreData();
  });


// -----------------------------------------------------------------------------
function periodChanged () {
  // Requery Device data
  queryDeviceData(true);
  querySessionsPresenceEvents();
}

// -----------------------------------------------------------------------------
function initializeiCheck () {
  // Default
  $('input').iCheck({
    checkboxClass: 'icheckbox_flat-blue',
    radioClass:    'iradio_flat-blue',
    increaseArea:  '20%'
  });

//  // readonly
//  $('#panDetails input').iCheck({
//    checkboxClass: 'icheckbox_flat-blue',
//    radioClass:    'iradio_flat-blue',
//    increaseArea:  '-100%'
//  });
}


// -----------------------------------------------------------------------------
function initializeAllCombos () {
  initializeCombo (document.getElementById("dropdownOwner"),      'queryOwners',      'txtOwner');
  initializeCombo (document.getElementById("dropdownDeviceType"), 'queryDeviceTypes', 'txtDeviceType');
  initializeCombo (document.getElementById("dropdownGroup"),      'queryGroups',      'txtGroup');
  initializeComboSkipRepeated ();
}

function initializeCombo (HTMLelement, queryAction, txtDataField) {
  // get data from server
  $.get('php/server/devices.php?action='+queryAction, function(data) {
    var listData = JSON.parse(data);
    var order = 1;

    HTMLelement.innerHTML = ""
    // for each item
    listData.forEach(function (item, index) {
      // insert line divisor
      if (order != item['order']) {
        HTMLelement.innerHTML += "<li class=\"divider\"></li>";
        order = item['order'];
      }

      // add dropdown item
      HTMLelement.innerHTML +=
        "    <li><a href=\"javascript:void(0)\" onclick=\"setTextValue('"+ txtDataField +"','"+ item['name'] +"')\">"
        + item['name'] + "</a></li>"
    });
  });
}


function initializeComboSkipRepeated () {
  // find dropdown menu element
  HTMLelement = document.getElementById("dropdownSkipRepeated");
  HTMLelement.innerHTML = ""

  // for each item
  skipRepeatedItems.forEach(function (item, index) {
    // add dropdown item
    HTMLelement.innerHTML += " <li><a href=\"javascript:void(0)\" " +
      " onclick=\"setTextValue('txtSkipRepeated','" + item + "');\">"+ item +"</a></li>";
  });
}

function findSkipRepeated (value='0') {
  var itemSelected = skipRepeatedItems[0];

  // for each item
  skipRepeatedItems.forEach(function (item, index) {
    if (item.split(" ")[0] == value) {
      itemSelected = item;
    }
  });
  return itemSelected;
}


// -----------------------------------------------------------------------------
function initializeDatatable () {
  $('#tableSessions').DataTable({
    'paging'      : true,
    'lengthChange': true,
    'searching'   : true,
    'ordering'    : true,
    'info'        : true,
    'autoWidth'   : false,
 
    'order'       : [[0,"desc"], [1,"desc"]],

    'columnDefs'  : [
        {visible:   false,  targets: [0]},

        // Replace HTML codes
        {targets: [1,2,3,5],
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

  $('#tableEvents').DataTable({
    'paging'      : true,
    'lengthChange': true,
    'searching'   : true,
    'ordering'    : true,
    'info'        : true,
    'autoWidth'   : false,

    'order'       : [[0,"desc"]],

    'columnDefs'  : [
        // Replace HTML codes
        {targets: [0],
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
        var listHeader  = document.getElementsByClassName('fc-day-header');
        var listContent = document.getElementsByClassName('fc-widget-content');

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
function queryDeviceData (updatePanelData=false) {
  //debugTimer();

  // Check MAC
  if (mac == '') {
    return;
  }

  // period
  period = document.getElementById('period').value;

  // get data from server
  $.get('php/server/devices.php?action=queryDeviceData&mac='+ mac +'&period='+ period, function(data) {
    var deviceData = JSON.parse(data);
    // check device exists
    if (deviceData['dev_MAC'] == null) {
      $('#pageTitle').html ('Device not found: <small>'+ mac +'</small>');
      return;
    }

    // Name
    if (deviceData['dev_Owner'] == null || deviceData['dev_Owner'] == '' || (deviceData['dev_Name']).indexOf (deviceData['dev_Owner']) != -1 )  {
      $('#pageTitle').html (deviceData['dev_Name']);
    } else {
      $('#pageTitle').html (deviceData['dev_Name'] +' ('+ deviceData['dev_Owner'] +')');
    }

    // Status
    $('#deviceStatus').html (deviceData['dev_Status']);
    switch (deviceData['dev_Status']) {
      case 'On-line':
        icon='fa fa-check';
        color='text-green';
        break;
      case 'Off-line':
        icon='fa fa-close';
        color='text-gray';
        break;
      case 'Down':
        icon='fa fa-warning';
        color='text-red';
        break;
      case null:
        $('#deviceStatus').html ('???');
        icon='fa fa-warning';
        color='text-red';
        break;
      default:
        icon='';
        color='';
        break;
    };
    document.getElementById('deviceStatus').className = color;
    document.getElementById('deviceStatusIcon').className = icon +' '+ color;

    // Totals
    $('#deviceSessions').html   (deviceData['dev_Sessions'].toLocaleString());
    $('#deviceDownAlerts').html (deviceData['dev_DownAlerts'].toLocaleString());

    // Events - Presence (alwais presence)
    if (true) {
      $('#deviceEventsTitle').html ('Presence');
      $('#deviceEventsIcon').html  ('<i class="fa fa-calendar">');
      if (deviceData['dev_PresenceHours'] == null) {
        $('#deviceEvents').html ('0 h.');
      } else {
        $('#deviceEvents').html (deviceData['dev_PresenceHours'].toLocaleString() +' h.');
      }
    } else {
      $('#deviceEventsTitle').html ('Events');
      $('#deviceEventsIcon').html  ('<i class="fa fa-info-circle">');
      $('#deviceEvents').html      (deviceData['dev_Events'].toLocaleString());
    };

    // Device info
    if (updatePanelData) {
      document.getElementById('txtMAC').value             = deviceData['dev_MAC'];
      document.getElementById('txtName').value            = deviceData['dev_Name'];
      document.getElementById('txtOwner').value           = deviceData['dev_Owner'];
      document.getElementById('txtDeviceType').value      = deviceData['dev_DeviceType'];
      document.getElementById('txtVendor').value          = deviceData['dev_Vendor'];
      if (deviceData['dev_Favorite'] == 1)                {$('#chkFavorite').iCheck('check');} 
      document.getElementById('txtGroup').value           = deviceData['dev_Group'];
      document.getElementById('txtComments').value        = deviceData['dev_Comments'];

      document.getElementById('txtFirstConnection').value = deviceData['dev_FirstConnection'];
      document.getElementById('txtLastConnection').value  = deviceData['dev_LastConnection'];
      document.getElementById('txtLastIP').value          = deviceData['dev_LastIP'];
      document.getElementById('txtStatus').value          = deviceData['dev_Status'];
      if (deviceData['dev_StaticIP'] == 1)               {$('#chkStaticIP').iCheck('check');} 
  
      document.getElementById('txtScanCycle').value       = deviceData['dev_ScanCycle'] +' min';
      // document.getElementById('chkAlertEvents').checked   = deviceData['dev_AlertEvents'];
      // document.getElementById('chkAlertDown').checked     = deviceData['dev_AlertDeviceDown'];
      if (deviceData['dev_AlertEvents'] == 1)             {$('#chkAlertEvents').iCheck('check');} 
      if (deviceData['dev_AlertDeviceDown'] == 1)         {$('#chkAlertDown').iCheck('check');} 

      document.getElementById('txtSkipRepeated').value    = findSkipRepeated (deviceData['dev_SkipRepeated']);
      deactivateSaveRestoreData ();
    }

    // Timer for refresh data
    newTimerRefreshData (queryDeviceData);
  });
}


// -----------------------------------------------------------------------------
function querySessionsPresenceEvents () {
//$.get('php/server/events.php?action=devicePresence&end=2019-06-30&start=2019-06-01&mac='+ mac +'&period='+ period, function(data) {
//alert (data)
//});


  // Define new datasource URL and reload
  $('#tableSessions').DataTable().ajax.url('php/server/events.php?action=deviceSessions&mac=' + mac +'&period='+ period).load();
  
  $('#calendar').fullCalendar('removeEventSources');
  $('#calendar').fullCalendar('addEventSource', { url: 'php/server/events.php?action=devicePresence&mac=' + mac +'&period='+ period });

  queryEvents();
}

function queryEvents () {
  hideConnections = document.getElementById('chkHideConnectionEvents').checked;
  $('#tableEvents').DataTable().ajax.url('php/server/events.php?action=deviceEvents&mac=' + mac +'&period='+ period +'&hideConnections='+ hideConnections).load();
}


// -----------------------------------------------------------------------------
function activateSaveRestoreData () {
  document.getElementById("btnRestore").removeAttribute ('disabled');
  document.getElementById("btnSave").removeAttribute ('disabled');
}


function deactivateSaveRestoreData () {
//  document.getElementById("btnRestore").setAttribute ('disabled','');
  document.getElementById("btnSave").setAttribute ('disabled','');
//  document.getElementById("btnRestore").classList.add ('disabled');
//  document.getElementById("btnSave").classList.add ('disabled');
}


// -----------------------------------------------------------------------------
function setTextValue (textElement, textValue) {
  document.getElementById(textElement).value = textValue;
  activateSaveRestoreData ();
}


// -----------------------------------------------------------------------------
function saveDeviceData () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // update data to server
  $.get('php/server/devices.php?action=updateData&mac='+ mac
    + '&name='           + document.getElementById('txtName').value
    + '&owner='          + document.getElementById('txtOwner').value
    + '&type='           + document.getElementById('txtDeviceType').value
    + '&vendor='         + document.getElementById('txtVendor').value
    + '&favorite='       + (document.getElementById('chkFavorite').checked * 1)
    + '&group='          + document.getElementById('txtGroup').value
    + '&comments='       + document.getElementById('txtComments').value
    + '&staticIP='       + (document.getElementById('chkStaticIP').checked * 1)
    + '&scancycle='      + document.getElementById('txtScanCycle').value.split(" ")[0]
    + '&alertevents='    + (document.getElementById('chkAlertEvents').checked * 1)
    + '&alertdown='      + (document.getElementById('chkAlertDown').checked * 1)
    + '&skiprepeated='   + document.getElementById('txtSkipRepeated').value.split(" ")[0]
    , function(data) {

  deactivateSaveRestoreData ();

  // show return message
  alert (data)
  });
}


</script>
