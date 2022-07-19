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
          <option value="1 day"><?php echo $pia_lang['DevDetail_Periodselect_today'];?></option>
          <option value="7 days"><?php echo $pia_lang['DevDetail_Periodselect_LastWeek'];?></option>
          <option value="1 month" selected><?php echo $pia_lang['DevDetail_Periodselect_LastMonth'];?></option>
          <option value="1 year"><?php echo $pia_lang['DevDetail_Periodselect_LastYear'];?></option>
          <option value="100 years"><?php echo $pia_lang['DevDetail_Periodselect_All'];?></option>
        </select>
      </span>
    </section>
    
<!-- Main content ---------------------------------------------------------- -->
    <section class="content">

<!-- top small box 1 ------------------------------------------------------- -->
      <div class="row">

        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabDetails').trigger('click')">
            <div class="small-box bg-aqua">
              <div class="inner"> <h3 id="deviceStatus" style="margin-left: 0em"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['DevDetail_Shortcut_CurrentStatus'];?></p>
              </div>
              <div class="icon"> <i id="deviceStatusIcon" class=""></i></div>
            </div>
          </a>
        </div>

<!-- top small box 2 ------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabSessions').trigger('click');">
            <div class="small-box bg-green">
              <div class="inner"> <h3 id="deviceSessions"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['DevDetail_Shortcut_Sessions'];?></p>
              </div>
              <div class="icon"> <i class="fa fa-plug"></i> </div>
            </div>
          </a>
        </div>

<!-- top small box 3 ------------------------------------------------------- -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabPresence').trigger('click')">
            <div  class="small-box bg-yellow">
              <div class="inner"> <h3 id="deviceEvents" style="margin-left: 0em"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['DevDetail_Shortcut_Presence'];?></p>
              </div>
              <div id="deviceEventsIcon" class="icon"> <i class="fa fa-calendar"></i> </div>
            </div>
          </a>
        </div>

<!--  top small box 4 ------------------------------------------------------ -->
        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabEvents').trigger('click');">
            <div  class="small-box bg-red">
              <div class="inner"> <h3 id="deviceDownAlerts"> -- </h3>
                <p class="infobox_label"><?php echo $pia_lang['DevDetail_Shortcut_DownAlerts'];?></p>
              </div>
              <div class="icon"> <i class="fa fa-warning"></i> </div>
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
              <li> <a id="tabDetails"  href="#panDetails"  data-toggle="tab"> <?php echo $pia_lang['DevDetail_Tab_Details'];?>  </a></li>
<?php
if ($_REQUEST['mac'] == 'Internet') { $DevDetail_Tap_temp = "Tools"; } else { $DevDetail_Tap_temp = $pia_lang['DevDetail_Tab_Nmap'];}
?>
              <li> <a id="tabNmap"     href="#panNmap"     data-toggle="tab"> <?php echo $DevDetail_Tap_temp;?>     </a></li>
              <li> <a id="tabSessions" href="#panSessions" data-toggle="tab"> <?php echo $pia_lang['DevDetail_Tab_Sessions'];?> </a></li>
              <li> <a id="tabPresence" href="#panPresence" data-toggle="tab"> <?php echo $pia_lang['DevDetail_Tab_Presence'];?> </a></li>
              <li> <a id="tabEvents"   href="#panEvents"   data-toggle="tab"> <?php echo $pia_lang['DevDetail_Tab_Events'];?>   </a></li>

              <div class="btn-group pull-right">
                <button type="button" class="btn btn-default"  style="padding: 10px; min-width: 30px;"
                  id="btnPrevious" onclick="previousRecord()"> <i class="fa fa-chevron-left"></i> </button>

                <div class="btn pa-btn-records"  style="padding: 10px; min-width: 30px; margin-left: 1px;"
                  id="txtRecord"     > 0 / 0 </div>

                <button type="button" class="btn btn-default"  style="padding: 10px; min-width: 30px; margin-left: 1px;"
                  id="btnNext"     onclick="nextRecord()"> <i class="fa fa-chevron-right"></i> </button>
              </div>
            </ul>



            <div class="tab-content" style="min-height: 430px;">

<!-- tab page 1 ------------------------------------------------------------ -->
<!--
              <div class="tab-pane fade in active" id="panDetails">
-->
              <div class="tab-pane fade" id="panDetails">

                <div class="row">
    <!-- column 1 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua"><?php echo $pia_lang['DevDetail_MainInfo_Title'];?></h4>
                    <div class="box-body form-horizontal">

                      <!-- MAC -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_mac'];?></label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtMAC" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Name -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_Name'];?></label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtName" type="text" value="--">
                        </div>
                      </div>

                      <!-- Owner -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_Owner'];?></label>
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
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_Type'];?></label>
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
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_Vendor'];?></label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtVendor" type="text" value="--">
                        </div>
                      </div>

                      <!-- Favorite -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_Favorite'];?></label>
                        <div class="col-sm-9" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkFavorite" type="checkbox">
                        </div>
                      </div>

                      <!-- Group -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_Group'];?></label>
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
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_Location'];?></label>
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
                        <label class="col-sm-3 control-label"><?php echo $pia_lang['DevDetail_MainInfo_Comments'];?></label>
                        <div class="col-sm-9">
                          <textarea class="form-control" rows="3" id="txtComments"></textarea>
                        </div>
                      </div>

                    </div>          
                  </div>          

    <!-- column 2 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua"><?php echo $pia_lang['DevDetail_SessionInfo_Title'];?></h4>
                    <div class="box-body form-horizontal">

                      <!-- Status -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_SessionInfo_Status'];?></label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtStatus" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- First Session -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_SessionInfo_FirstSession'];?></label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtFirstConnection" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Last Session -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_SessionInfo_LastSession'];?></label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtLastConnection" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Last IP -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_SessionInfo_LastIP'];?></label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtLastIP" type="text" readonly value="--">
                        </div>
                      </div>

                      <!-- Static IP -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_SessionInfo_StaticIP'];?></label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkStaticIP" type="checkbox">
                        </div>
                      </div>
      
                    </div>
                  </div>

    <!-- column 3 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua"><?php echo $pia_lang['DevDetail_EveandAl_Title'];?></h4>
                    <div class="box-body form-horizontal">

                      <!-- Scan Cycle -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_EveandAl_ScanCycle'];?></label>
                        <div class="col-sm-7">
                          <div class="input-group">
                            <input class="form-control" id="txtScanCycle" type="text" value="--" readonly >
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false" id="dropdownButtonScanCycle">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownScanCycle" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtScanCycle','1 min')">   Scan 1 min every 5 min</a></li>
                                <!-- <li><a href="javascript:void(0)" onclick="setTextValue('txtScanCycle','15 min');"> Scan 12 min every 15 min</a></li> -->
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtScanCycle','0 min');">  Don't Scan</a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Alert events -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_EveandAl_AlertAllEvents'];?></label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkAlertEvents" type="checkbox">
                        </div>
                      </div>
      
                      <!-- Alert Down -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_EveandAl_AlertDown'];?></label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox red hidden" id="chkAlertDown" type="checkbox">
                        </div>
                      </div>

                      <!-- Skip Notifications -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label" style="padding-top: 0px; padding-left: 0px;"><?php echo $pia_lang['DevDetail_EveandAl_Skip'];?></label>
                        <div class="col-sm-7">
                          <div class="input-group">
                            <input class="form-control" id="txtSkipRepeated" type="text" value="--" readonly >
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
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_EveandAl_NewDevice'];?>:</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox orange hidden" id="chkNewDevice" type="checkbox">
                        </div>
                      </div>

                      <!-- Archived -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_EveandAl_Archived'];?>:</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkArchived" type="checkbox">
                        </div>
                      </div>

                      <!-- Randomized MAC -->
                      <div class="form-group" >
                        <label class="col-sm-5 control-label"><?php echo $pia_lang['DevDetail_EveandAl_RandomMAC'];?>:</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <span id="iconRandomMACinactive" data-toggle="tooltip" data-placement="right" title="Random MAC is Inactive">
                            <i style="font-size: 24px;" class="text-gray glyphicon glyphicon-random"></i> &nbsp &nbsp </span>

                          <span id="iconRandomMACactive"   data-toggle="tooltip" data-placement="right" title="Random MAC is Active" class="hidden">
                            <i style="font-size: 24px;" class="text-yellow glyphicon glyphicon-random"></i> &nbsp &nbsp </span>

                          <a href="https://github.com/leiweibau/Pi.Alert/blob/main/docs/RAMDOM_MAC.md" target="_blank" style="color: #777;"> 
                            <i class="fa fa-info-circle"></i> </a>
                        </div>
                      </div>

                    </div>
                  </div>

                  <!-- Buttons -->
                  <div class="col-xs-12">
                    <div class="pull-right">
                        <button type="button" class="btn btn-default pa-btn pa-btn-delete"  style="margin-left:0px;"
                          id="btnDelete"   onclick="askDeleteDevice()">   <?php echo $pia_lang['DevDetail_button_Delete'];?> </button>
                        <button type="button" class="btn btn-default pa-btn" style="margin-left:6px;" 
                          id="btnRestore"  onclick="getDeviceData(true)"> <?php echo $pia_lang['DevDetail_button_Reset'];?> </button>
                        <button type="button" disabled class="btn btn-primary pa-btn" style="margin-left:6px; " 
                          id="btnSave"     onclick="setDeviceData()" >     <?php echo $pia_lang['DevDetail_button_Save'];?> </button>
                    </div>
                  </div>

                </div>
              </div>                                                                         

<!-- tab page 2 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panSessions">

                <!-- Datatable Session -->
                <table id="tableSessions" class="table table-bordered table-hover table-striped ">
                  <thead>
                  <tr>
                    <th><?php echo $pia_lang['DevDetail_SessionTable_Order'];?></th>
                    <th><?php echo $pia_lang['DevDetail_SessionTable_Connection'];?></th>
                    <th><?php echo $pia_lang['DevDetail_SessionTable_Disconnection'];?></th>
                    <th><?php echo $pia_lang['DevDetail_SessionTable_Duration'];?></th>
                    <th><?php echo $pia_lang['DevDetail_SessionTable_IP'];?></th>
                    <th><?php echo $pia_lang['DevDetail_SessionTable_Additionalinfo'];?></th>
                  </tr>
                  </thead>
                </table>
              </div>


<!-- tab page 5 ------------------------------------------------------------ -->


              <div class="tab-pane fade" id="panNmap">

<?php
if ($_REQUEST['mac'] == 'Internet') {
?>
                <h4 class="">Online Speedtest</h4>
                <div style="width:100%; text-align: center; margin-bottom: 50px;">
                  <button type="button" id="speedtestcli" class="btn btn-default pa-btn" style="margin: auto;" onclick="speedtestcli()">Start Speedtest</button>
                </div>
                   
                  <script>
                  function speedtestcli() {
                    $( "#scanoutput" ).empty();
                    $.ajax({
                      method: "POST",
                      url: "./php/server/speedtestcli.php",
                      beforeSend: function() { $('#scanoutput').addClass("ajax_scripts_loading"); },
                      complete: function() { $('#scanoutput').removeClass("ajax_scripts_loading"); },
                      success: function(data, textStatus) {
                          $("#scanoutput").html(data);    
                      }
                    })
                  }
                  </script>
<?php  
}
?>
                <h4 class="">Nmap Scans</h4>
                <div style="width:100%; text-align: center;">
                  <script>
                      setTimeout(function(){
                        document.getElementById('piamanualnmap_fast').innerHTML='<?php echo $pia_lang['DevDetail_Nmap_buttonFast'];?> (' + document.getElementById('txtLastIP').value +')';
                        document.getElementById('piamanualnmap_normal').innerHTML='<?php echo $pia_lang['DevDetail_Nmap_buttonDefault'];?> (' + document.getElementById('txtLastIP').value +')';
                        document.getElementById('piamanualnmap_detail').innerHTML='<?php echo $pia_lang['DevDetail_Nmap_buttonDetail'];?> (' + document.getElementById('txtLastIP').value +')';
                      }, 2000);
                  </script>

                  <button type="button" id="piamanualnmap_fast" class="btn btn-default pa-btn" style="margin: auto;" onclick="manualnmapscan(document.getElementById('txtLastIP').value, 'fast')">Loading...</button>
                  <button type="button" id="piamanualnmap_normal" class="btn btn-default pa-btn" style="margin: auto;" onclick="manualnmapscan(document.getElementById('txtLastIP').value, 'normal')">Loading...</button>
                  <button type="button" id="piamanualnmap_detail" class="btn btn-default pa-btn" style="margin: auto;" onclick="manualnmapscan(document.getElementById('txtLastIP').value, 'detail')">Loading...</button>
                
                  <div style="margin-top: 20px; text-align: left;">
                    <ul style="padding:20px;">
                      <li><?php echo $pia_lang['DevDetail_Nmap_buttonFast_text'];?></li>
                      <li><?php echo $pia_lang['DevDetail_Nmap_buttonDefault_text'];?></li>
                      <li><?php echo $pia_lang['DevDetail_Nmap_buttonDetail_text'];?></li>
                    </ul>
                  </div>
                </div>

                <div id="scanoutput" style="margin-top: 30px;"></div>
                   
                  <script>
                  function manualnmapscan(targetip, mode) {
                    $( "#scanoutput" ).empty();
                    $.ajax({
                      method: "POST",
                      url: "./php/server/nmap_scan.php",
                      data: { scan: targetip, mode: mode },
                      beforeSend: function() { $('#scanoutput').addClass("ajax_scripts_loading"); },
                      complete: function() { $('#scanoutput').removeClass("ajax_scripts_loading"); },
                      success: function(data, textStatus) {
                          $("#scanoutput").html(data);    
                      }
                    })
                  }
                  </script>
              
              </div>




<!-- ----------------------------------------------------------------------- -->


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
                    <?php echo $pia_lang['DevDetail_Events_CheckBox'];?>
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
  <script src="lib/AdminLTE/bower_components/fullcalendar/dist/locale-all.js"></script>

<!-- Dark-Mode Patch -->
<?php
if ($ENABLED_DARKMODE === True) {
   echo '<link rel="stylesheet" href="css/dark-patch-cal.css">';
}
?>

<!-- page script ----------------------------------------------------------- -->
<script>

  var mac                 = '';
  var devicesList         = [];
  var pos                 = -1;
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
      
            // Read Cookies
            devicesList = getCookie('devicesList');
            deleteCookie ('devicesList');
            if (devicesList != '') {
                devicesList = JSON.parse (devicesList);
            } else {
                devicesList = [];
            }


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
  
            // Ask before exit without saving data
            window.onbeforeunload = function(){
              if ( ! document.getElementById('btnSave').hasAttribute('disabled') ) {
                return 'Are you sure you want to discard unsaved changes?';
              }
            };

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

      // Ask skip notifications
      // if (event.currentTarget.id == 'chkArchived' ) {
      //   askSkipNotifications();
      // }
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
      emptyTable: 'No data',
      "lengthMenu": "<?php echo $pia_lang['Events_Tablelenght'];?>",
      "search":     "<?php echo $pia_lang['Events_Searchbox'];?>: ",
      "paginate": {
          "next":       "<?php echo $pia_lang['Events_Table_nav_next'];?>",
          "previous":   "<?php echo $pia_lang['Events_Table_nav_prev'];?>"
      },
      "info":           "<?php echo $pia_lang['Events_Table_info'];?>",
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
      emptyTable: 'No data',
      "lengthMenu": "<?php echo $pia_lang['Events_Tablelenght'];?>",
      "search":     "<?php echo $pia_lang['Events_Searchbox'];?>: ",
      "paginate": {
          "next":       "<?php echo $pia_lang['Events_Table_nav_next'];?>",
          "previous":   "<?php echo $pia_lang['Events_Table_nav_prev'];?>"
      },
      "info":           "<?php echo $pia_lang['Events_Table_info'];?>",
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
    locale            : '<?php echo $pia_lang['Presence_CalHead_lang'];?>',
    header: {
      left            : 'prev,next today',
      center          : 'title',
      right           : 'agendaYear,agendaMonth,agendaWeek'
    },

    views: {
      agendaYear: {
        type               : 'agenda',
        duration           : { year: 1 },
        buttonText         : '<?php echo $pia_lang['Presence_CalHead_year'];?>',
        columnHeaderFormat : ''
      },

      agendaMonth: {
        type               : 'agenda',
        duration           : { month: 1 },
        buttonText         : '<?php echo $pia_lang['Presence_CalHead_month'];?>',
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
function getDeviceData (readAllData=false) {
  // stop timer
  stopTimerRefreshData();

  // Check MAC
  if (mac == '') {
    return;
  }

  // Deactivate next previous buttons
  if (readAllData) {
    $('#btnPrevious').attr        ('disabled','');
    $('#btnPrevious').addClass    ('text-gray50');
    $('#btnNext').attr            ('disabled','');
    $('#btnNext').addClass        ('text-gray50');
    $("body").css                 ("cursor", "progress");
  }

  // get data from server
  $.get('php/server/devices.php?action=getDeviceData&mac='+ mac + '&period='+ period, function(data) {

    var deviceData = JSON.parse(data);

    // check device exists
    if (deviceData['dev_MAC'] == null) {
      // Status
      $('#deviceStatus').html ('--');
      $('#deviceStatus')[0].className = 'text-gray';
      $('#deviceStatusIcon')[0].className = '';
  
      $('#deviceSessions').html   ('--');
      $('#deviceDownAlerts').html ('--');
      $('#deviceEvents').html     ('--');
 
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
      $('#chkNewDevice').iCheck    ('uncheck'); 
      $('#chkArchived').iCheck     ('uncheck'); 

      $('#iconRandomMACactive').addClass ('hidden');
      $('#iconRandomMACinactive').removeClass ('hidden');

      // Deactivate controls
      $('#panDetails :input').attr('disabled', true);

      // Check if device is deleted o no exists in this session
      if (pos == -1) {
        devicesList = [];
        $('#pageTitle').html ('Device not found: <small>'+ mac +'</small>');
      } else {
        $('#pageTitle').html ('Device deleted');
      }

    } else {

      // Name
      if (deviceData['dev_Owner'] == null || deviceData['dev_Owner'] == '' ||
      (deviceData['dev_Name']).indexOf (deviceData['dev_Owner']) != -1 )  {
        $('#pageTitle').html (deviceData['dev_Name']);
      } else {
        $('#pageTitle').html (deviceData['dev_Name'] + ' ('+ deviceData['dev_Owner'] +')');
      }

      // Status
      $('#deviceStatus').html (deviceData['dev_Status'].replace('-', ''));
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
      if (readAllData) {
        // Activate controls
        $('#panDetails :input').attr('disabled', false);

        mac                                          =deviceData['dev_MAC'];

        $('#txtMAC').val                             (deviceData['dev_MAC']);
        $('#txtName').val                            (deviceData['dev_Name']);
        $('#txtOwner').val                           (deviceData['dev_Owner']);
        $('#txtDeviceType').val                      (deviceData['dev_DeviceType']);
        $('#txtVendor').val                          (deviceData['dev_Vendor']);
  
        if (deviceData['dev_Favorite'] == 1)         {$('#chkFavorite').iCheck('check');}    else {$('#chkFavorite').iCheck('uncheck');}
        $('#txtGroup').val                           (deviceData['dev_Group']);
        $('#txtLocation').val                        (deviceData['dev_Location']);
        $('#txtComments').val                        (deviceData['dev_Comments']);
  
        $('#txtFirstConnection').val                 (deviceData['dev_FirstConnection']);
        $('#txtLastConnection').val                  (deviceData['dev_LastConnection']);
        $('#txtLastIP').val                          (deviceData['dev_LastIP']);
        $('#txtStatus').val                          (deviceData['dev_Status'].replace('-', ''));
        if (deviceData['dev_StaticIP'] == 1)         {$('#chkStaticIP').iCheck('check');}    else {$('#chkStaticIP').iCheck('uncheck');}
    
        $('#txtScanCycle').val                       (deviceData['dev_ScanCycle'] +' min');
        if (deviceData['dev_AlertEvents'] == 1)      {$('#chkAlertEvents').iCheck('check');} else {$('#chkAlertEvents').iCheck('uncheck');}
        if (deviceData['dev_AlertDeviceDown'] == 1)  {$('#chkAlertDown').iCheck('check');}   else {$('#chkAlertDown').iCheck('uncheck');}
        $('#txtSkipRepeated').val                    (findSkipRepeated (deviceData['dev_SkipRepeated']));
        if (deviceData['dev_NewDevice'] == 1)        {$('#chkNewDevice').iCheck('check');}   else {$('#chkNewDevice').iCheck('uncheck');}
        if (deviceData['dev_Archived'] == 1)         {$('#chkArchived').iCheck('check');}    else {$('#chkArchived').iCheck('uncheck');}

        if (deviceData['dev_RandomMAC'] == 1)        {$('#iconRandomMACactive').removeClass   ('hidden');
                                                      $('#iconRandomMACinactive').addClass    ('hidden'); }
        else                                         {$('#iconRandomMACactive').addClass      ('hidden');
                                                      $('#iconRandomMACinactive').removeClass ('hidden'); };
        deactivateSaveRestoreData ();
      }

      // Check if device is part of the devicesList
      pos = devicesList.indexOf (deviceData['rowid']);
      if (pos == -1) {
        devicesList =[deviceData['rowid']];
        pos=0;
      }
    }

    // Record number
    $('#txtRecord').html (pos+1 +' / '+ devicesList.length);

    // Deactivate previous button
    if (pos <= 0) {
      $('#btnPrevious').attr        ('disabled','');
      $('#btnPrevious').addClass    ('text-gray50');
    } else {
      $('#btnPrevious').removeAttr  ('disabled');
      $('#btnPrevious').removeClass ('text-gray50');
    }
  
    // Deactivate next button
    if (pos >= (devicesList.length-1)) {
      $('#btnNext').attr        ('disabled','');
      $('#btnNext').addClass    ('text-gray50');
    } else {
      $('#btnNext').removeAttr  ('disabled');
      $('#btnNext').removeClass ('text-gray50');
    }

    // Timer for refresh data
    $("body").css("cursor", "default");
    newTimerRefreshData (getDeviceData);
  });

}


// -----------------------------------------------------------------------------
function previousRecord () {
  // Save Changes
  if ( ! document.getElementById('btnSave').hasAttribute('disabled') ) {
    setDeviceData (previousRecord);
    return;
  }

  // Previous Record
  if (pos > 0) {
    pos--;
    mac = devicesList[pos].toString();
    getDeviceData (true);
  }
}

// -----------------------------------------------------------------------------
function nextRecord () {
  // Save Changes
  if ( ! document.getElementById('btnSave').hasAttribute('disabled') ) {
    setDeviceData (nextRecord);
    return;
  }

  // Next Record
  if (pos < (devicesList.length-1) ) {
    pos++;
    mac = devicesList[pos].toString();
    getDeviceData (true);
  }
}


// -----------------------------------------------------------------------------
function setDeviceData (refreshCallback='') {
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
    + '&archived='       + ($('#chkArchived')[0].checked * 1)
    , function(msg) {

    // deactivate button 
    deactivateSaveRestoreData ();
    showMessage (msg);

    // Callback fuction
    if (typeof refreshCallback == 'function') {
      refreshCallback();
    }
  });
}


// -----------------------------------------------------------------------------
function askSkipNotifications () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // When Archived
  if ($('#chkArchived')[0].checked && $('#txtScanCycle').val().split(' ')[0] != "0") {
    // Ask skip notifications
    showModalDefault ('Device Archived', 'Do you want to skip all notifications for this device?',
      'Cancel', 'Ok', 'skipNotifications');
  }
}

// -----------------------------------------------------------------------------
function skipNotifications () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Set cycle 0
  $('#txtScanCycle').val ('0 min');
  activateSaveRestoreData();
}

// -----------------------------------------------------------------------------
function askDeleteDevice () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Ask delete device
  showModalWarning ('Delete Device', 'Are you sure you want to delete this device?<br>(maybe you prefer to archive it)',
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
