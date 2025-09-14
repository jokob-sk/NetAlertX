<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>

<!-- INTERNET INFO -->
<?php if ($_REQUEST["mac"] == "Internet") { ?>
    
    <h4 class=""><i class="fa-solid fa-globe"></i>
        <?= lang("DevDetail_Tab_Tools_Internet_Info_Title") ?>
    </h4>
    <h5 class="">
        <?= lang("DevDetail_Tab_Tools_Internet_Info_Description") ?>
    </h5>
    <br>
    <div style="width:100%; text-align: center;">
        <button type="button" id="internetinfo" class="btn btn-primary pa-btn" style="margin: auto;" onclick="internetinfo()">
            <?= lang("DevDetail_Tab_Tools_Internet_Info_Start") ?></button>
        <br>
        <div id="internetinfooutput" style="margin-top: 10px;"></div>
    </div>

<?php } ?>

<!-- COPY FROM DEVICE -->
<?php if ($_REQUEST["mac"] != "Internet") { ?>
    
    <h4 class=""><i class="fa-solid fa-copy"></i>
        <?= lang("DevDetail_Copy_Device_Title") ?>
    </h4>
    <h5 class="">
        <?= lang("DevDetail_Copy_Device_Tooltip") ?>
    </h5>
    <br>
    <div style="width:100%; text-align: center;">
        <select class="form-control" 
                title="<?= lang('DevDetail_Copy_Device_Tooltip');?>" 
                id="txtCopyFromDevice" >
                <option value="lemp_loading" id="lemp_loading">Loading</option>
        </select>
        <button type="button" id="internetinfo" class="btn btn-primary pa-btn" style="margin: auto; margin-top:10px;" onclick="copyFromDevice()">
            <?= lang("BackDevDetail_Copy_Title") ?></button>
        <br>
    </div>

<?php } ?>

<!-- WAKE ON LAN - WOL -->
<?php if ($_REQUEST["mac"] != "Internet") { ?>
    
    <h4 class=""><i class="fa-solid fa-bell"></i>
        <?= lang("DevDetail_Tools_WOL_noti") ?>
    </h4>
    <h5 class="">
        <?= lang("DevDetail_Tools_WOL_noti_text") ?>
    </h5>
    <br>
    <div style="width:100%; text-align: center;">
        <button type="button" id="internetinfo" class="btn btn-primary pa-btn" style="margin: auto;" onclick="wakeonlan()">
            <?= lang("DevDetail_Tools_WOL_noti") ?></button>
        <br>
        <div id="wol_output" style="margin-top: 10px;"></div>
    </div>

<?php } ?>


<!-- Delete Events -->
<h4 class=""><i class="fa-solid fa-bell"></i>
        <?= lang("DevDetail_button_DeleteEvents") ?>
    </h4>
    <h5 class="">
        <?= lang("DevDetail_button_DeleteEvents_Warning") ?>
    </h5>
    <br>
    <div style="width:100%; text-align: center;">
        <button type="button" 
                class="btn btn-default pa-btn pa-btn-delete"  
                style="margin-left:0px;" 
                id="btnDeleteEvents"   
                onclick="askDeleteDeviceEvents()">   
                  <?= lang('DevDetail_button_DeleteEvents');?> 
        </button>
        <br>
        <div id="wol_output" style="margin-top: 10px;"></div>
    </div>

<!-- Reset Custom Proprties -->
<h4 class=""><i class="fa-solid fa-list"></i>
        <?= lang("DevDetail_CustomProperties_Title") ?> 
    </h4>
    <h5 class="">
        <?= lang("DevDetail_CustomProps_reset_info") ?>
    </h5>
    <br>
    <div style="width:100%; text-align: center;">
        <button type="button" 
                class="btn btn-default pa-btn pa-btn-delete"  
                style="margin-left:0px;" 
                id="btnDeleteEvents"   
                onclick="askResetDeviceProps()">   
                    <?= lang("Gen_Reset") ?> 
        </button>
        <br>
        <div id="wol_output" style="margin-top: 10px;"></div>
    </div>


<!-- SPEEDTEST -->
<?php if ($_REQUEST["mac"] == "Internet") { ?>
    <h4 class=""><i class="fa-solid fa-gauge-high"></i>
        <?= lang("DevDetail_Tab_Tools_Speedtest_Title") ?>
    </h4>
    <h5 class="">
        <?= lang("DevDetail_Tab_Tools_Speedtest_Description") ?>
    </h5>
    <br>
    <div style="width:100%; text-align: center;">
        <button type="button" id="speedtestcli" class="btn btn-primary pa-btn" style="margin: auto;" onclick="speedtestcli()">
            <?= lang("DevDetail_Tab_Tools_Speedtest_Start") ?></button>
        <br>
        <div id="speedtestoutput" style="margin-top: 10px;"></div>
    </div>

<?php } ?>

<!-- TRACEROUTE -->
<?php if ($_REQUEST["mac"] != "Internet") { ?>
    <h4 class=""><i class="fa-solid fa-route"></i>
        <?= lang("DevDetail_Tab_Tools_Traceroute_Title") ?>
    </h4>
    <h5 class="">
        <?= lang("DevDetail_Tab_Tools_Traceroute_Description") ?>
    </h5>
    <div style="width:100%; text-align: center;">
        <button type="button" id="traceroute" class="btn btn-primary pa-btn" style="margin: auto;" onclick="traceroute()">
            <?= lang("DevDetail_Tab_Tools_Traceroute_Start") ?>
        </button>
        <br>
        <div id="tracerouteoutput" style="margin-top: 10px;"></div>
    </div>

<?php } ?>

<!-- NSLOOKUP -->
<?php if ($_REQUEST["mac"] != "Internet") { ?>
    <h4 class=""><i class="fa-solid fa-magnifying-glass"></i>
        <?= lang("DevDetail_Tab_Tools_Nslookup_Title") ?>
    </h4>
    <h5 class="">
        <?= lang("DevDetail_Tab_Tools_Nslookup_Description") ?>
    </h5>
    <div style="width:100%; text-align: center;">
        <button type="button" id="nslookup" class="btn btn-primary pa-btn" style="margin: auto;" onclick="nslookup()">
            <?= lang("DevDetail_Tab_Tools_Nslookup_Start") ?>
        </button>
        <br>
        <div id="nslookupoutput" style="margin-top: 10px;"></div>
    </div>

<?php } ?>                                             

<!-- NMAP SCANS -->
<h4 class=""><i class="fa-solid fa-ethernet"></i>
    <?= lang("DevDetail_Nmap_Scans") ?>    
</h4>
<div style="width:100%; text-align: center;">
    <div>
        <?= lang("DevDetail_Nmap_Scans_desc") ?>
    </div>

    <button type="button" id="piamanualnmap_fast" class="btn btn-primary pa-btn" style="margin-bottom: 20px; margin-left: 10px; margin-right: 10px;" onclick="manualnmapscan(getDevDataByMac(getMac(), 'devLastIP'), 'fast')">
        <?= lang("DevDetail_Loading") ?>
    </button>
    <button type="button" id="piamanualnmap_normal" class="btn btn-primary pa-btn" style="margin-bottom: 20px; margin-left: 10px; margin-right: 10px;" onclick="manualnmapscan(getDevDataByMac(getMac(), 'devLastIP'), 'normal')">
        <?= lang("DevDetail_Loading") ?>
    </button>
    <button type="button" id="piamanualnmap_detail" class="btn btn-primary pa-btn" style="margin-bottom: 20px; margin-left: 10px; margin-right: 10px;" onclick="manualnmapscan(getDevDataByMac(getMac(), 'devLastIP'), 'detail')">
        <?= lang("DevDetail_Loading") ?>
    </button>
    <button type="button" id="piamanualnmap_skipdiscovery" class="btn btn-primary pa-btn" style="margin-bottom: 20px; margin-left: 10px; margin-right: 10px;" onclick="manualnmapscan(getDevDataByMac(getMac(), 'devLastIP'), 'skipdiscovery')">
        <?= lang("DevDetail_Loading") ?>
    </button>

    <div style="text-align: left;">
        <ul style="padding:20px;">
            <li>
                <?= lang("DevDetail_Nmap_buttonFast_text") ?>
            </li>
            <li>
                <?= lang("DevDetail_Nmap_buttonDefault_text") ?>
            </li>
            <li>
                <?= lang("DevDetail_Nmap_buttonDetail_text") ?>
            </li>
            <li>
                <?= lang("DevDetail_Nmap_buttonSkipDiscovery_text") ?>
            </li>
            <li>
                <a onclick="setCache('activeMaintenanceTab', 'tab_Logging_id')" href="maintenance.php#tab_Logging">
                    <?= lang("DevDetail_Nmap_resultsLink") ?>
                </a>
            </li>

        </ul>
    </div>
</div>

<div id="scanoutput" style="margin-top: 30px;"></div>

<script>
    // ----------------------------------------------------------------
        function manualnmapscan(targetip, mode) {
            $( "#scanoutput" ).empty();
                $.ajax({
                    method: "POST",
                    url: "./php/server/nmap_scan.php",
                    data: { scan: targetip, mode: mode },
                    beforeSend: function() { $('#scanoutput').addClass("ajax_scripts_loading"); },
                    complete: function() { $('#scanoutput').removeClass("ajax_scripts_loading"); },
                    success: function(data, textStatus) {
                    // console.log(data);
                        $("#scanoutput").html(data);    
                    }
                })
        }


        // ----------------------------------------------------------------
        function speedtestcli() {
            $( "#speedtestoutput" ).empty();
                $.ajax({
                    method: "POST",
                    url: "./php/server/speedtestcli.php",
                    beforeSend: function() { $('#speedtestoutput').addClass("ajax_scripts_loading"); },
                    complete: function() { $('#speedtestoutput').removeClass("ajax_scripts_loading"); },
                    success: function(data, textStatus) {
                        $("#speedtestoutput").html(data);    
                    }
                })
        }


        // ----------------------------------------------------------------
        function traceroute() {
                
            $( "#tracerouteoutput" ).empty();
                $.ajax({
                    method: "GET",
                    url: "./php/server/traceroute.php?action=get&ip=" + getDevDataByMac(getMac(), 'devLastIP') + "",
                    beforeSend: function() { $('#tracerouteoutput').addClass("ajax_scripts_loading"); },
                    complete: function() { $('#tracerouteoutput').removeClass("ajax_scripts_loading"); },
                    success: function(data, textStatus) {
                        $("#tracerouteoutput").html(data);
                    }
                })
        }

        // ----------------------------------------------------------------
        function nslookup() {
                
            $( "#nslookupoutput" ).empty();
                $.ajax({
                    method: "GET",
                    url: "./php/server/nslookup.php?action=get&ip=" + getDevDataByMac(getMac(), 'devLastIP') + "",
                    beforeSend: function() { $('#nslookupoutput').addClass("ajax_scripts_loading"); },
                    complete: function() { $('#nslookupoutput').removeClass("ajax_scripts_loading"); },
                    success: function(data, textStatus) {
                        $("#nslookupoutput").html(data);
                    }
                })
        }

        // ----------------------------------------------------------------
        function initNmapButtons() {
                setTimeout(function(){
                            document.getElementById('piamanualnmap_fast').innerHTML=getString(
                                "DevDetail_Nmap_buttonFast"
                            ) ;
                            document.getElementById('piamanualnmap_normal').innerHTML=getString(
                                "DevDetail_Nmap_buttonDefault"
                            ) ;
                            document.getElementById('piamanualnmap_detail').innerHTML=getString(
                                "DevDetail_Nmap_buttonDetail"
                            ) ;
                            document.getElementById('piamanualnmap_skipdiscovery').innerHTML=getString(
                                "DevDetail_Nmap_buttonSkipDiscovery"
                            ) ;
                            }, 500);
        }


        // ----------------------------------------------------------------
        function initCopyFromDevice() {

            const devices = getVisibleDevicesList()
            // console.log(devices);

            const $select = $('#txtCopyFromDevice');
            $select.empty(); // Clear existing options

            devices.forEach(device => {
                const option = $('<option></option>')
                    .val(device.devMac)
                    .text(device.devName);
                $select.append(option);
            });
            
            
        }

        // ----------------------------------------------------------------
        function wakeonlan() {

            macAddress = getMac();

            // Execute
            $.get('php/server/devices.php?action=wakeonlan&'
                + '&mac='         + macAddress
                + '&ip='          + getDevDataByMac(macAddress, "devLastIP")
                , function(msg) {
                showMessage (msg);
            });
        }

        // ------------------------------------------------------------
        function copyFromDevice() {

            macAddress = getMac();

            // Execute
            $.get('php/server/devices.php?action=copyFromDevice&'
                + '&macTo='         + macAddress
                + '&macFrom='          + $('#txtCopyFromDevice').val()
                , function(msg) {
                    showMessage (msg);

                    setTimeout(function() {
                        window.location.reload();
                    }, 2000);
            });

        }

        // ------------------------------------------------------------
        function getVisibleDevicesList()
        {
            // Read cache (skip cookie expiry check)
            devicesList = getCache('devicesListAll_JSON', true);
            
            if (devicesList != '') {
                devicesList = JSON.parse (devicesList);
            } else {
                devicesList = [];
            }

            // only loop thru the filtered down list
            visibleDevices = getCache("ntx_visible_macs")

            if(visibleDevices != "") {
            visibleDevicesMACs = visibleDevices.split(',');

            devicesList_tmp = [];

            // Iterate through the data and filter only visible devices
            $.each(devicesList, function(index, item) {
                // Check if the current item's MAC exists in visibleDevicesMACs
                if (visibleDevicesMACs.includes(item.devMac)) {
                devicesList_tmp.push(item);
                }
            });

            // Update devicesList with the filtered items
            devicesList = devicesList_tmp;
            }

            return devicesList;
        }

        // ----------------------------------------------------------------

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
        }

        // -----------------------------------------------------------------------------
        function askResetDeviceProps () {
            // Check MAC
            if (mac == '') {
                return;
            }

            // Ask Resert Custom properties 
            showModalWarning ('<?= lang('Gen_Reset');?>', '<?= lang('DevDetail_CustomProps_reset_info');?>',
            '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Delete');?>', 'resetDeviceProps');
        }

        function resetDeviceProps () {
            // Check MAC
            if (mac == '') {
                return;
            }

            // Execute
            $.get('php/server/devices.php?action=resetDeviceProps&mac='+ mac, function(msg) {
            showMessage (msg);
            });
        }

        // ----------------------------------------------------------------
        function internetinfo() {
                $( "#internetinfooutput" ).empty();
                $.ajax({
                    method: "POST",
                    url: "./php/server/internetinfo.php",
                    beforeSend: function() { $('#internetinfooutput').addClass("ajax_scripts_loading"); },
                    complete: function() { $('#internetinfooutput').removeClass("ajax_scripts_loading"); },
                    success: function(data, textStatus) {
                        $("#internetinfooutput").html(data);    
                    }
                })
        }

        // init first time
        // ----------------------------------------------------------- 
        var toolsPageInitialized = false;

        function initDeviceToolsPage()
        {
            // Only proceed if .panTools is visible
            if (!$('#panTools:visible').length) {
                return; // exit early if nothing is visible
            }

            // init page once
            if (toolsPageInitialized) return;
            toolsPageInitialized = true;

            initNmapButtons();
            initCopyFromDevice();

            hideSpinner();

        }

        // -----------------------------------------------------------------------------
        // Recurring function to monitor the URL and reinitialize if needed
        function deviceToolsPageUpdater() {
            initDeviceToolsPage();

            // Run updater again after delay
            setTimeout(deviceToolsPageUpdater, 200);
        }

        // start updater
        deviceToolsPageUpdater();  

</script>
