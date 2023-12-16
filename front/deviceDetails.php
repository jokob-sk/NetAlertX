<!--
#---------------------------------------------------------------------------------#
#  Pi.Alert                                                                       #
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

<!-- top small box 1 ------------------------------------------------------- -->
      <div class="row">

        <div class="col-lg-3 col-sm-6 col-xs-6">
          <a href="#" onclick="javascript: $('#tabDetails').trigger('click')">
            <div class="small-box bg-aqua">
              <div class="inner"> <h3 id="deviceStatus" style="margin-left: 0em"> -- </h3>
                <p class="infobox_label"><?= lang('DevDetail_Shortcut_CurrentStatus');?></p>
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
                <p class="infobox_label"><?= lang('DevDetail_Shortcut_Sessions');?></p>
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
                <p class="infobox_label"><?= lang('DevDetail_Shortcut_Presence');?></p>
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
                <p class="infobox_label"><?= lang('DevDetail_Shortcut_DownAlerts');?></p>
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

                <div class="row">
    <!-- column 1 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua"><?= lang('DevDetail_MainInfo_Title');?></h4>
                    <div class="box-body form-horizontal">

                      <!-- MAC -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_mac');?></label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtMAC" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Name -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Name');?></label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtName" type="text" value="--">
                            <span class="input-group-addon"><i class="fa fa-pencil pointer" onclick="editDrp('txtName');"></i></span>
                          </div>                          
                        </div>
                      </div>

                      <!-- Owner -->
                      <div class="form-group" title="<?= lang('DevDetail_Owner_hover');?>">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Owner');?></label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtOwner" type="text" value="--">
                            <span class="input-group-addon"><i class="fa fa-pencil pointer" onclick="editDrp('txtOwner');"></i></span>
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                <span class="fa fa-caret-down "></span></button>                                
                              <ul id="dropdownOwner" class="dropdown-menu dropdown-menu-right">
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Type -->
                      <div class="form-group" title="<?= lang('DevDetail_Type_hover');?>">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Type');?></label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtDeviceType" type="text" value="--">
                            <span class="input-group-addon"><i class="fa fa-pencil pointer" onclick="editDrp('txtDeviceType');"></i></span>
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false" >
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownDeviceType" class="dropdown-menu dropdown-menu-right">
                                
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Icon -->
                      <div class="form-group" title="<?= lang('DevDetail_Icon_Descr');?>">
                        <label class="col-sm-3 control-label">
                          <?= lang('DevDetail_Icon');?> 
                          <a href="https://github.com/jokob-sk/Pi.Alert/blob/main/docs/ICONS.md" target="_blank"> <span><i class="fa fa-circle-question"></i></a><span>
                        </label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <span class="input-group-addon"><i class="fa" id="txtIconFA" onclick="editDrp('txtIcon');"></i></span>
                            <input class="form-control" id="txtIcon" type="text" value="--">
                            <span class="input-group-addon" title='<?= lang('DevDetail_button_OverwriteIcons_Tooltip');?>'><i class="fa fa-copy pointer" onclick="askOverwriteIconType();"></i></span>
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                <span class="fa fa-caret-down"></span>
                              </button>
                              <ul id="dropdownIcon" class="dropdown-menu dropdown-menu-right">
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Vendor -->
                      <div class="form-group" title="<?= lang('DevDetail_Vendor_hover');?>">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Vendor');?></label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtVendor" type="text" value="--">
                        </div>
                      </div>

                      <!-- Favorite -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Favorite');?></label>
                        <div class="col-sm-9" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkFavorite" type="checkbox">
                        </div>
                      </div>

                      <!-- Group -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Group');?></label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtGroup" type="text" value="--">
                            <span class="input-group-addon"><i class="fa fa-pencil pointer" onclick="editDrp('txtGroup');"></i></span>
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                <span class="fa fa-caret-down"></span>
                              </button>
                              <ul id="dropdownGroup" class="dropdown-menu dropdown-menu-right">
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Location -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Location');?></label>
                        <div class="col-sm-9">
                          <div class="input-group">
                            <input class="form-control" id="txtLocation" type="text" value="--">
                            <span class="input-group-addon"><i class="fa fa-pencil pointer" onclick="editDrp('txtLocation');"></i></span>
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownLocation" class="dropdown-menu dropdown-menu-right">

                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Comments -->
                      <div class="form-group">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Comments');?></label>
                        <div class="col-sm-9">
                          <textarea class="form-control" rows="3" id="txtComments"></textarea>
                        </div>
                      </div>
                      


                    </div>          
                  </div>          

    <!-- column 2 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua"><?= lang('DevDetail_SessionInfo_Title');?></h4>
                    <div class="box-body form-horizontal">

                      <!-- Status -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_SessionInfo_Status');?></label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtStatus" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- First Session -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_SessionInfo_FirstSession');?></label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtFirstConnection" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Last Session -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_SessionInfo_LastSession');?></label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtLastConnection" type="text" readonly value="--">
                        </div>
                      </div>
      
                      <!-- Last IP -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_SessionInfo_LastIP');?></label>
                        <div class="col-sm-7">
                          <input class="form-control" id="txtLastIP" type="text" readonly value="--">
                        </div>
                      </div>

                      <!-- Static IP -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_SessionInfo_StaticIP');?></label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkStaticIP" type="checkbox">
                        </div>
                      </div>

                      <!-- Network -->
                      <h4 class="bottom-border-aqua"><?= lang('DevDetail_MainInfo_Network_Title');?><span class="networkPageHelp"> <a target="_blank" href="https://github.com/jokob-sk/Pi.Alert/blob/main/docs/NETWORK_TREE.md"><i class="fa fa-circle-question"></i></a><span></h4>                    
                      <div class="form-group" title="<?= lang('DevDetail_Network_Node_hover');?>">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Network');?></label>
                        <div class="col-sm-9">  
                          <div class="input-group parentNetworkNode"> 

                            <input class="form-control" id="txtNetworkNodeMac" type="text" value="--">
                            <span class="input-group-addon"><i title="<?= lang('DevDetail_GoToNetworkNode');?>" class="fa fa-square-up-right pointer" onclick="goToNetworkNode('txtNetworkNodeMac');"></i></span>
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-mynodemac="" data-toggle="dropdown" aria-expanded="false" id="buttonNetworkNodeMac">
                                    <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownNetworkNodeMac" class="dropdown-menu dropdown-menu-right">
                              </ul>
                            </div>

                          </div>
                        </div>
                      </div>
                      <div class="form-group" title="<?= lang('DevDetail_Network_Port_hover');?>">
                        <label class="col-sm-3 control-label"><?= lang('DevDetail_MainInfo_Network_Port');?></label>
                        <div class="col-sm-9">
                          <input class="form-control" id="txtNetworkPort" type="text" value="--">
                        </div>
                      </div>

                      
      
                    </div>
                  </div>

    <!-- column 3 -->
                  <div class="col-lg-4 col-sm-6 col-xs-12">
                    <h4 class="bottom-border-aqua"><?= lang('DevDetail_EveandAl_Title');?></h4>
                    <div class="box-body form-horizontal">

                      <!-- Scan Cycle -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_EveandAl_ScanCycle');?></label>
                        <div class="col-sm-7">
                          <div class="input-group">
                            <input class="form-control" id="txtScanCycle" type="text" value="--" readonly >
                            <div class="input-group-btn">
                              <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false" id="dropdownButtonScanCycle">
                                <span class="fa fa-caret-down"></span></button>
                              <ul id="dropdownScanCycle" class="dropdown-menu dropdown-menu-right">
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtScanCycle','yes')"><?= lang('DevDetail_EveandAl_ScanCycle_a');?></a></li>                                
                                <li><a href="javascript:void(0)" onclick="setTextValue('txtScanCycle','no');"><?= lang('DevDetail_EveandAl_ScanCycle_z');?></a></li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Alert events -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_EveandAl_AlertAllEvents');?></label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkAlertEvents" type="checkbox">
                        </div>
                      </div>
      
                      <!-- Alert Down -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_EveandAl_AlertDown');?></label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox red hidden" id="chkAlertDown" type="checkbox">
                        </div>
                      </div>

                      <!-- Skip Notifications -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label" style="padding-top: 0px; padding-left: 0px;"><?= lang('DevDetail_EveandAl_Skip');?></label>
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
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_EveandAl_NewDevice');?>:</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox orange hidden" id="chkNewDevice" type="checkbox">
                        </div>
                      </div>

                      <!-- Archived -->
                      <div class="form-group">
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_EveandAl_Archived');?>:</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <input class="checkbox blue hidden" id="chkArchived" type="checkbox">
                        </div>
                      </div>

                      <!-- Randomized MAC -->
                      <div class="form-group" title="<?= lang('RandomMAC_hover');?>" >
                        <label class="col-sm-5 control-label"><?= lang('DevDetail_EveandAl_RandomMAC');?>:</label>
                        <div class="col-sm-7" style="padding-top:6px;">
                          <span id="iconRandomMACinactive" data-toggle="tooltip" data-placement="right" title="Random MAC is Inactive">
                            <i style="font-size: 24px;" class="text-gray glyphicon glyphicon-random"></i> &nbsp &nbsp </span>

                          <span id="iconRandomMACactive"   data-toggle="tooltip" data-placement="right" title="Random MAC is Active" class="hidden">
                            <i style="font-size: 24px;" class="text-yellow glyphicon glyphicon-random"></i> &nbsp &nbsp </span>

                          <a href="https://github.com/jokob-sk/Pi.Alert/blob/main/docs/RANDOM_MAC.md" target="_blank" style="color: #777;"> 
                            <i class="fa fa-info-circle"></i> </a>
                        </div>
                      </div>
                    </div>
                </div>

                <div class="col-lg-4 col-sm-6 col-xs-12">
                  <h4 class="bottom-border-aqua"><?= lang('DevDetail_Run_Actions_Title');?></h4>
                  <div class="box-body form-horizontal">
                  <label class="col-sm-3 control-label">
                    <?= lang('Gen_Action');?>                   
                  </label>
                  <div class="col-sm-9">
                    <div class="input-group">
                      <input class="form-control" title="<?= lang('DevDetail_Run_Actions_Tooltip');?>" id="txtAction" type="text" value="--">
                      <span class="input-group-addon" title='<?= lang('Gen_Run');?>'><i class="fa fa-play pointer" onclick="askRunAction();"></i></span>
                      
                      <div class="input-group-btn">
                        <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                          <span class="fa fa-caret-down"></span>
                        </button>
                        <ul id="dropdownAction" class="dropdown-menu dropdown-menu-right">
                        </ul>
                      </div>
                    </div>
                  </div> 
                  </div>

                  <h4 class="bottom-border-aqua"><?= lang('DevDetail_Copy_Device_Title');?></h4>
                      <div class="box-body form-horizontal">
                      <label class="col-sm-3 control-label">
                        <?= lang('Navigation_Devices');?>                   
                      </label>
                      <div class="col-sm-9">
                        <div class="input-group">
                          <input class="form-control" title="<?= lang('DevDetail_Copy_Device_Tooltip');?>" id="txtFromDevice" type="text" value="--">
                          <span class="input-group-addon" title='<?= lang('Gen_Copy');?>'><i class="fa fa-copy pointer" onclick="askCopyFromDevice();"></i></span>
                          
                          <div class="input-group-btn">
                            <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
                              <span class="fa fa-caret-down"></span>
                            </button>
                            <ul id="dropdownDevices" class="dropdown-menu dropdown-menu-right">
                            </ul>
                          </div>
                        </div>
                      </div> 
                      </div> 

                  
                </div>

                

                  <!-- Buttons -->
                  <div class="col-xs-12">
                    <div class="pull-right">
                        <button type="button" class="btn btn-default pa-btn pa-btn-delete"  style="margin-left:0px;"
                          id="btnDeleteEvents"   onclick="askDeleteDeviceEvents()">   <?= lang('DevDetail_button_DeleteEvents');?> </button>
                        <button type="button" class="btn btn-default pa-btn pa-btn-delete"  style="margin-left:0px;"
                          id="btnDelete"   onclick="askDeleteDevice()">   <?= lang('DevDetail_button_Delete');?> </button>
                        <button type="button" class="btn btn-default pa-btn" style="margin-left:6px;" 
                          id="btnRestore"  onclick="getDeviceData(true)"> <?= lang('DevDetail_button_Reset');?> </button>
                        <button type="button" disabled class="btn btn-primary pa-btn" style="margin-left:6px; " 
                          id="btnSave"     onclick="setDeviceData()" >     <?= lang('DevDetail_button_Save');?> </button>
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
<script defer>

  // ------------------------------------------------------------
  function getMac(){
    params = new Proxy(new URLSearchParams(window.location.search), {
      get: (searchParams, prop) => searchParams.get(prop),
    });

    return params.mac
  }  

  // ------------------------------------------------------------
  function getDevicesList()
  {
    // Read cache (skip cookie expiry check)
    devicesList = getCache('devicesListAll_JSON', true);
    
    if (devicesList != '') {
        devicesList = JSON.parse (devicesList);
    } else {
        devicesList = [];
    }

    return devicesList;
  }

  // ------------------------------------------------------------

  mac                     = getMac()  // can also be rowID!! not only mac 
  var devicesList         = [];   // this will contain a list the database row IDs of the devices ordered by the position displayed in the UI  

  main();

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
  var selectedTab         = 'tabDetails';
  var emptyArr            = ['undefined', "", undefined, null];



// -----------------------------------------------------------------------------
function main () {
  // Initialize MAC
  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has ('mac') == true) {
    mac = urlParams.get ('mac');
    setCache("piaDeviceDetailsMac", mac); // set cookie
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

  // get parameter value
  $.get('php/server/parameters.php?action=get&defaultValue=1 day&parameter='+ parPeriod, function(data) {
    var result = JSON.parse(data);
    if (result) {
      period = result;
      $('#period').val(period);
    }

    // get parameter value
    $.get('php/server/parameters.php?action=get&defaultValue=50&parameter='+ parSessionsRows, function(data) {
      var result = JSON.parse(data);
      if (Number.isInteger (result) ) {
          sessionsRows = result;
      }

      // get parameter value
      $.get('php/server/parameters.php?action=get&defaultValue=50&parameter='+ parEventsRows, function(data) {
        var result = JSON.parse(data);
        if (Number.isInteger (result) ) {
            eventsRows = result;
        }
  
        // get parameter value
        $.get('php/server/parameters.php?action=get&defaultValue=true&parameter='+ parEventsHide, function(data) {
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

          // Show device icon as it changes
          $('#txtIcon').on('change input', function() {
            $('#txtIconFA').removeClass().addClass(`fa fa-${$(this).val()} pointer`)
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
      // activateSaveRestoreData();

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
  initializeCombo ( '#dropdownOwner',          'getOwners',       'txtOwner', true);
  initializeCombo ( '#dropdownDeviceType',     'getDeviceTypes',  'txtDeviceType', true);
  initializeCombo ( '#dropdownGroup',          'getGroups',       'txtGroup', true);
  initializeCombo ( '#dropdownLocation',       'getLocations',    'txtLocation', true);
  initializeCombo ( '#dropdownNetworkNodeMac', 'getNetworkNodes', 'txtNetworkNodeMac', false);
  initializeCombo ( '#dropdownIcon',           'getIcons',        'txtIcon', false);  
  initializeCombo ( '#dropdownAction',         'getActions',      'txtAction', false);  
  initializeCombo ( '#dropdownDevices',        'getDevices',      'txtFromDevice', false);  

  // Initialize static combos
  initializeComboSkipRepeated ();
}
// -----------------------------------------------------------------------------
function initializeCombo (dropdownId, queryAction, txtDataField, useCache) {

  // check if we have the value cached already
  var dropdownHtmlContent = useCache ? getCache(dropdownId) : ""; 

  if(dropdownHtmlContent == "")
  {
    // get data from server
    $.get('php/server/devices.php?action='+queryAction, function(data) {
      var listData = JSON.parse(data);
      var order = 1;
      

      // for each item
      listData.forEach(function (item, index) {
        // insert line divisor
        if (order != item['order']) {
          dropdownHtmlContent += '<li class="divider"></li>';
          order = item['order'];
        }

        id = item['name'];
        // use explicitly specified id (value) if avaliable
        if(item['id'])
        {
          id = item['id'];
        }

        // add dropdown item
        dropdownHtmlContent +=
          '<li><a href="javascript:void(0)" onclick="setTextValue(\''+
          txtDataField +'\',\''+ id +'\')">'+ item['name'] + '</a></li>'
      });

      writeDropdownHtml(dropdownId, dropdownHtmlContent)
    });
  } else
  {
    writeDropdownHtml(dropdownId, dropdownHtmlContent)
  }
}
// -----------------------------------------------------------------------------
// Edit dropdown value
function editDrp(dropdownId)
{
  $('#'+dropdownId).focus();
}

// -----------------------------------------------------------------------------
// Go to the correct network node in the Network section
function goToNetworkNode(dropdownId)
{  
  setCache('activeNetworkTab', $('#'+dropdownId).attr('data-mynodemac').replaceAll(":","_")+'_id');
  window.location.href = './network.php';
  
}

// -----------------------------------------------------------------------------
// write out the HTML for the dropdown
function writeDropdownHtml(dropdownId, dropdownHtmlContent)
{
  // cache
  setCache(dropdownId, dropdownHtmlContent);

  // write HTML for the dropdown
  var HTMLelement = $(dropdownId)[0];
  HTMLelement.innerHTML = ''
  HTMLelement.innerHTML += dropdownHtmlContent;
}
// -----------------------------------------------------------------------------


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

// -----------------------------------------------------------------------------

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
          hideSpinner()
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

  // console.log("getDeviceData mac: ", mac)

  // Check MAC
  if (mac == '') {
    // console.log("getDeviceData mac AA: ", mac)
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
  
      $('#deviceSessions').html        ('--');
      $('#deviceDownAlerts').html      ('--');
      $('#deviceEvents').html          ('--');
 
      $('#txtMAC').val                 ('--');
      $('#txtName').val                ('--');
      $('#txtOwner').val               ('--');
      $('#txtDeviceType').val          ('--');
      $('#txtVendor').val              ('--');
      $('#txtIcon').val                ('--');

      $('#chkFavorite').iCheck         ('uncheck'); 
      $('#txtGroup').val               ('--');
      $('#txtLocation').val            ('--');
      $('#txtComments').val            ('--');
      $('#txtNetworkNodeMac').val      ('--');
      $('#txtNetworkPort').val         ('--');

      $('#txtFirstConnection').val     ('--');
      $('#txtLastConnection').val      ('--');
      $('#txtLastIP').val              ('--');
      $('#txtStatus').val              ('--');
      $('#chkStaticIP').iCheck         ('uncheck'); 
  
      $('#txtScanCycle').val           ('--');
      $('#chkAlertEvents').iCheck      ('uncheck') 
      $('#chkAlertDown').iCheck        ('uncheck') 
      $('#txtSkipRepeated').val        ('--');
      $('#chkNewDevice').iCheck        ('uncheck'); 
      $('#chkArchived').iCheck         ('uncheck'); 

      $('#iconRandomMACactive').addClass ('hidden');
      $('#iconRandomMACinactive').removeClass ('hidden');

      // Deactivate controls
      $('#panDetails :input').attr('disabled', true);

      // Check if device is deleted or don't exist in this session
      if (pos == -1) {
        devicesList = [];
        $('#pageTitle').html ('Device not found: <small>'+ mac +'</small>');
      } else {
        $('#pageTitle').html ('Device deleted');
      }

    } else {

      // Name
      if (deviceData['dev_Owner'] == null || deviceData['dev_Owner'] == '' ||
      (deviceData['dev_Name'].toString()).indexOf (deviceData['dev_Owner']) != -1 )  {
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

        mac                                          = deviceData['dev_MAC'];

        // update the mac parameter in the URL, this makes the selected device persistent when the page is reloaded
        var searchParams = new URLSearchParams(window.location.search);
        searchParams.set("mac", mac);
        var newRelativePathQuery = window.location.pathname + '?' + searchParams.toString();
        history.pushState(null, '', newRelativePathQuery);
        getSessionsPresenceEvents();
        
        devicesList = getDevicesList();        

        $('#txtMAC').val                             (deviceData['dev_MAC']);
        $('#txtName').val                            (deviceData['dev_Name']);
        $('#txtOwner').val                           (deviceData['dev_Owner']);
        $('#txtDeviceType').val                      (deviceData['dev_DeviceType']);
        $('#txtVendor').val                          (deviceData['dev_Vendor']);
        $('#txtIcon').val                            (initDefault(deviceData['dev_Icon'], 'laptop'));
        $('#txtIcon').trigger('change')
  
        if (deviceData['dev_Favorite'] == 1)         {$('#chkFavorite').iCheck('check');}    else {$('#chkFavorite').iCheck('uncheck');}
        $('#txtGroup').val                           (deviceData['dev_Group']);
        $('#txtLocation').val                        (deviceData['dev_Location']);
        $('#txtComments').val                        (deviceData['dev_Comments']);        
        $('#txtNetworkNodeMac').val                  ( getDeviceDataByMacAddress(deviceData['dev_Network_Node_MAC_ADDR'], "dev_Name")) ;
        $('#txtNetworkNodeMac').attr                 ('data-mynodemac', deviceData['dev_Network_Node_MAC_ADDR']);        
        $('#txtNetworkPort').val                     (deviceData['dev_Network_Node_port']);
        // disabling network node configuration if root Internet node
        toggleNetworkConfiguration(mac == 'Internet')         
        
  
        $('#txtFirstConnection').val                 (deviceData['dev_FirstConnection']);
        $('#txtLastConnection').val                  (deviceData['dev_LastConnection']);
        $('#txtLastIP').val                          (deviceData['dev_LastIP']);
        $('#txtStatus').val                          (deviceData['dev_Status'].replace('-', ''));
        if (deviceData['dev_StaticIP'] == 1)         {$('#chkStaticIP').iCheck('check');}    else {$('#chkStaticIP').iCheck('uncheck');}
    
        $('#txtScanCycle').val                       (deviceData['dev_ScanCycle'] == "1" ? "yes" : "no");
        if (deviceData['dev_AlertEvents'] == 1)      {$('#chkAlertEvents').iCheck('check');} else {$('#chkAlertEvents').iCheck('uncheck');}
        if (deviceData['dev_AlertDeviceDown'] == 1)  {$('#chkAlertDown').iCheck('check');}   else {$('#chkAlertDown').iCheck('uncheck');}
        $('#txtSkipRepeated').val                    (findSkipRepeated (deviceData['dev_SkipRepeated']));
        if (deviceData['dev_NewDevice'] == 1)        {$('#chkNewDevice').iCheck('check');}   else {$('#chkNewDevice').iCheck('uncheck');}
        if (deviceData['dev_Archived'] == 1)         {$('#chkArchived').iCheck('check');}    else {$('#chkArchived').iCheck('uncheck');}

        if (deviceData['dev_RandomMAC'] == 1)        {$('#iconRandomMACactive').removeClass   ('hidden');
                                                      $('#iconRandomMACinactive').addClass    ('hidden'); }
        else                                         {$('#iconRandomMACactive').addClass      ('hidden');
                                                      $('#iconRandomMACinactive').removeClass ('hidden'); };        
      }

      // Check if device is part of the devicesList      
      pos = devicesList.findIndex(item => item.rowid == deviceData['rowid']);          
      
      if (pos == -1) {
        devicesList.push({"rowid" : deviceData['rowid'], "mac" : deviceData['dev_MAC'], "name": deviceData['dev_Name'], "type": deviceData['dev_DeviceType']});
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
  
  // update the global position in the devices list variable 'pos'
  if(direction == "next")
  {
    // Next Record
    if (pos < (devicesList.length-1) ) {
      pos++;
    }
  }else if (direction == "prev")
  {
    if (pos > 0) {
      pos--;
    }
  }

  // get new mac from the devicesList. Don't change to the commented out line below, the mac query string in the URL isn't updated yet!
  // mac = params.mac;
  
  mac = devicesList[pos].dev_MAC.toString();

  setCache("piaDeviceDetailsMac", mac);
    
  getDeviceData (true); 

}

// -----------------------------------------------------------------------------
function initDefault (value, defaultVal) {
  if (emptyArr.includes(value))
  {
    return defaultVal;
  }

  return value;
}
// -----------------------------------------------------------------------------
function setDeviceData (direction='', refreshCallback='') {
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
    + '&icon='           + $('#txtIcon').val()
    + '&favorite='       + ($('#chkFavorite')[0].checked * 1)
    + '&group='          + $('#txtGroup').val()
    + '&location='       + $('#txtLocation').val()
    + '&comments='       + $('#txtComments').val()
    + '&networknode='    + $('#txtNetworkNodeMac').attr('data-mynodemac')
    + '&networknodeport=' + $('#txtNetworkPort').val()
    + '&staticIP='       + ($('#chkStaticIP')[0].checked * 1)
    + '&scancycle='      + ($('#txtScanCycle').val() == "yes" ? "1" : "0")
    + '&alertevents='    + ($('#chkAlertEvents')[0].checked * 1)
    + '&alertdown='      + ($('#chkAlertDown')[0].checked * 1)
    + '&skiprepeated='   + $('#txtSkipRepeated').val().split(' ')[0]
    + '&newdevice='      + ($('#chkNewDevice')[0].checked * 1)
    + '&archived='       + ($('#chkArchived')[0].checked * 1)
    , function(msg) {
    
    showMessage (msg);

    // clear session storage 
    setCache("#dropdownOwner","");
    setCache("#dropdownDeviceType","");
    setCache("#dropdownGroup","");
    setCache("#dropdownLocation","");
    setCache("#dropdownNetworkNodeMac","");

    // Remove navigation prompt "Are you sure you want to leave..."
    window.onbeforeunload = null;
    somethingChanged      = false;

    // refresh API
    updateApi()

    // Callback fuction
    if (typeof refreshCallback == 'function') {
      refreshCallback(direction);
    }
  });
}

// --------------------------------------------------------
// Calls a backend function to add a front-end event to an execution queue
function updateApi()
{

  // value has to be in format event|param. e.g. run|ARPSCAN
  action = `update_api|devices`

  $.ajax({
    method: "POST",
    url: "php/server/util.php",
    data: { function: "addToExecutionQueue", action: action  },
    success: function(data, textStatus) {
        console.log(data)
    }
  })
}


// -----------------------------------------------------------------------------
function askSkipNotifications () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // When Archived
  if ($('#chkArchived')[0].checked && $('#txtScanCycle').val() != "no") {
    // Ask skip notifications
    showModalDefault ('Device Archived', 'Do you want to skip all notifications for this device?',
      '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Okay');?>', 'skipNotifications');
  }
}

// -----------------------------------------------------------------------------
function skipNotifications () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Set cycle 0
  $('#txtScanCycle').val ('no');  
}
// -----------------------------------------------------------------------------
function askDeleteDeviceEvents () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Ask delete device Events 
  showModalWarning ('<?= lang('DevDetail_button_DeleteEvents');?>', '<?= lang('DevDetail_button_DeleteEvents_Warning');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Delete');?>', 'deleteDeviceEvents');
}

function deleteDeviceEvents () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Delete device events
  $.get('php/server/devices.php?action=deleteDeviceEvents&mac='+ mac, function(msg) {
    showMessage (msg);
  });

  // Deactivate controls
  $('#panDetails :input').attr('disabled', true);
}

// -----------------------------------------------------------------------------
function askCopyFromDevice() {
    // Ask 
    showModalWarning('<?= lang('BackDevDetail_Copy_Title');?>', '<?= lang('BackDevDetail_Copy_Ask');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Run');?>', 'copyFromDevice');
}

function copyFromDevice() {

  // Execute
  $.get('php/server/devices.php?action=copyFromDevice&'
    + '&macTo='         + $('#txtMAC').val()
    + '&macFrom='          + $('#txtFromDevice').val()
    , function(msg) {
    showMessage (msg);

    setTimeout(function() {
      window.location.reload();
    }, 2000);
  });

}

// -----------------------------------------------------------------------------
function askRunAction() {
    // Ask 
    showModalWarning('<?= lang('BackDevDetail_Actions_Title_Run');?>', '<?= lang('BackDevDetail_Actions_Ask_Run');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Run');?>', 'runAction');
}

function runAction() {

  action = $('#txtAction').val();

  switch(action)
  {
    case 'wake-on-lan': 
      wakeonlan();
      break;
    default: 
      showMessage (`<?= lang('BackDevDetail_Actions_Not_Registered');?> ${action} `);
      break;
  }

}

function wakeonlan() {
  // Execute
  $.get('php/server/devices.php?action=wakeonlan&'
    + '&mac='         + $('#txtMAC').val()
    + '&ip='          + $('#txtLastIP').val()
    , function(msg) {
    showMessage (msg);
  });
}

// -----------------------------------------------------------------------------
// Overwrite all devices of the same type with the currently selected icon
function askOverwriteIconType () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Ask overwrite icon types 
  showModalWarning ('<?= lang('DevDetail_button_OverwriteIcons');?>', '<?= lang('DevDetail_button_OverwriteIcons_Warning');?>',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Okay');?>', 'overwriteIconType');
}

// -----------------------------------------------------------------------------
function overwriteIconType () {
  // Check MAC
  if (mac == '') {
    return;
  }

  var icon = $('#txtIcon').val();

  // Mass update icons
  $.get('php/server/devices.php?action=overwriteIconType&mac='+ mac + '&icon=' + icon, function(msg) {
    showMessage (msg);
  });

  // Deactivate controls
  $('#panDetails :input').attr('disabled', true);
}

// -----------------------------------------------------------------------------
function askDeleteDevice () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Ask delete device
  showModalWarning ('Delete Device', 'Are you sure you want to delete this device?<br>(maybe you prefer to archive it)',
    '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Delete');?>', 'deleteDevice');
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

  // refresh API
  updateApi()
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
// Initialize a text input with the correct value
function setTextValue (textElement, textValue) {
  if(textElement == "txtNetworkNodeMac")
  {
    $('#'+textElement).attr ('data-mynodemac', textValue);
    $('#'+textElement).val (getDeviceDataByMacAddress(textValue, "dev_Name")); 
  } else
  {
    $('#'+textElement).attr ('data-myvalue', textValue);
    $('#'+textElement).val (textValue);  
  }
  $('#'+textElement).trigger('change')
}

// -----------------------------------------------------------------------------

function initializeTabsNew () {  

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

  // Save Parameters rows & order when changed
  $('#'+tableId).on( 'length.dt', function ( e, settings, len ) {
    setParameter (parSessionsRows, len);

  } );

}

//-----------------------------------------------------------------------------------

window.onload = function async()
{
  initializeTabsNew();

  
}

//-----------------------------------------------------------------------------------
// Disables network configuration for the root node
function toggleNetworkConfiguration(disable)
{
  $('#txtNetworkNodeMac').prop('readonly', true ); // disable direct input as should only be selected via the dropdown

  if(disable)
  {       
  //   $('#txtNetworkNodeMac').val(getString('Network_Root_Unconfigurable'));   
  //   $('#txtNetworkPort').val(getString('Network_Root_Unconfigurable'));     
    $('#txtNetworkPort').prop('readonly', true );
    $('.parentNetworkNode .input-group-btn').hide();
  }
  else
  {    
    $('#txtNetworkPort').prop('readonly', false );
    $('.parentNetworkNode .input-group-btn').show();
  }
}

</script>
