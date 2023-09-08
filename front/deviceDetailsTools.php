<script>
    deviceIP = getDeviceDataByMacAddress("<?php echo $_REQUEST["mac"]?>", "dev_LastIP")
</script>

<?php if ($_REQUEST["mac"] == "Internet") { ?>
    
<h4 class=""><i class="fa-solid fa-globe"></i>
    <?= lang("DevDetail_Tab_Tools_Internet_Info_Title") ?>
</h4>
<h5 class="">
    <?= lang("DevDetail_Tab_Tools_Internet_Info_Description") ?>
</h5>
<br>
<div style="width:100%; text-align: center; margin-bottom: 50px;">
    <button type="button" id="internetinfo" class="btn btn-primary pa-btn" style="margin: auto;" onclick="internetinfo()">
        <?= lang("DevDetail_Tab_Tools_Internet_Info_Start") ?></button>
    <br>
    <div id="internetinfooutput" style="margin-top: 10px;"></div>
</div>

<?php } ?>

<?php if ($_REQUEST["mac"] == "Internet") { ?>
<h4 class=""><i class="fa-solid fa-gauge-high"></i>
    <?= lang("DevDetail_Tab_Tools_Speedtest_Title") ?>
</h4>
<h5 class="">
    <?= lang("DevDetail_Tab_Tools_Speedtest_Description") ?>
</h5>
<br>
<div style="width:100%; text-align: center; margin-bottom: 50px;">
    <button type="button" id="speedtestcli" class="btn btn-primary pa-btn" style="margin: auto;" onclick="speedtestcli()">
        <?= lang("DevDetail_Tab_Tools_Speedtest_Start") ?></button>
    <br>
    <div id="speedtestoutput" style="margin-top: 10px;"></div>
</div>

<?php } ?>

<?php if ($_REQUEST["mac"] != "Internet") { ?>
<h4 class=""><i class="fa-solid fa-route"></i>
    <?= lang("DevDetail_Tab_Tools_Traceroute_Title") ?>
</h4>
<h5 class="">
    <?= lang("DevDetail_Tab_Tools_Traceroute_Description") ?>
</h5>
<div style="width:100%; text-align: center; margin-bottom: 50px;">
    <button type="button" id="traceroute" class="btn btn-primary pa-btn" style="margin: auto;" onclick="traceroute()">
        <?= lang("DevDetail_Tab_Tools_Traceroute_Start") ?>
    </button>
    <br>
    <div id="tracerouteoutput" style="margin-top: 10px;"></div>
</div>

<?php } ?>

<?php if ($_REQUEST["mac"] != "Internet") { ?>
<h4 class=""><i class="fa-solid fa-magnifying-glass"></i>
    <?= lang("DevDetail_Tab_Tools_Nslookup_Title") ?>
</h4>
<h5 class="">
    <?= lang("DevDetail_Tab_Tools_Nslookup_Description") ?>
</h5>
<div style="width:100%; text-align: center; margin-bottom: 50px;">
    <button type="button" id="nslookup" class="btn btn-primary pa-btn" style="margin: auto;" onclick="nslookup()">
        <?= lang("DevDetail_Tab_Tools_Nslookup_Start") ?>
    </button>
    <br>
    <div id="nslookupoutput" style="margin-top: 10px;"></div>
</div>

<?php } ?>                                             

<h4 class=""><i class="fa-solid fa-ethernet"></i>
    <?= lang("DevDetail_Nmap_Scans") ?>    
</h4>
<div style="width:100%; text-align: center;">
    <div>
        <?= lang("DevDetail_Nmap_Scans_desc") ?>
    </div>

    <button type="button" id="piamanualnmap_fast" class="btn btn-primary pa-btn" style="margin-bottom: 20px; margin-left: 10px; margin-right: 10px;" onclick="manualnmapscan(deviceIP, 'fast')">
        <?= lang("DevDetail_Loading") ?>
    </button>
    <button type="button" id="piamanualnmap_normal" class="btn btn-primary pa-btn" style="margin-bottom: 20px; margin-left: 10px; margin-right: 10px;" onclick="manualnmapscan(deviceIP, 'normal')">
        <?= lang("DevDetail_Loading") ?>
    </button>
    <button type="button" id="piamanualnmap_detail" class="btn btn-primary pa-btn" style="margin-bottom: 20px; margin-left: 10px; margin-right: 10px;" onclick="manualnmapscan(deviceIP, 'detail')">
        <?= lang("DevDetail_Loading") ?>
    </button>
    <button type="button" id="piamanualnmap_skipdiscovery" class="btn btn-primary pa-btn" style="margin-bottom: 20px; margin-left: 10px; margin-right: 10px;" onclick="manualnmapscan(deviceIP, 'skipdiscovery')">
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
                <a onclick="setCache('activeMaintenanceTab', 'tab_Logging_id')" href="/maintenance.php#tab_Logging">
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
                    console.log(data);
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
                    url: "./php/server/traceroute.php?action=get&ip=" + deviceIP + "",
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
                    url: "./php/server/nslookup.php?action=get&ip=" + deviceIP + "",
                    beforeSend: function() { $('#nslookupoutput').addClass("ajax_scripts_loading"); },
                    complete: function() { $('#nslookupoutput').removeClass("ajax_scripts_loading"); },
                    success: function(data, textStatus) {
                        $("#nslookupoutput").html(data);
                    }
                })
        }

        // ----------------------------------------------------------------
        setTimeout(function(){
                    document.getElementById('piamanualnmap_fast').innerHTML='<?= lang(
                        "DevDetail_Nmap_buttonFast"
                    ) ?> (' + deviceIP +')';
                    document.getElementById('piamanualnmap_normal').innerHTML='<?= lang(
                        "DevDetail_Nmap_buttonDefault"
                    ) ?> (' + deviceIP +')';
                    document.getElementById('piamanualnmap_detail').innerHTML='<?= lang(
                        "DevDetail_Nmap_buttonDetail"
                    ) ?> (' + deviceIP +')';
                    document.getElementById('piamanualnmap_skipdiscovery').innerHTML='<?= lang(
                        "DevDetail_Nmap_buttonSkipDiscovery"
                    ) ?> (' + deviceIP +')';
                    }, 2000);


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
</script>
