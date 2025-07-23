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

      <div id="devicePageInfoPlc" class="card-body bg-light">
          <div class="small-box panel  rounded">
              <div class="inner text-center">
                  
              </div>                    
          </div>
      </div>

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
              <li> 
                <a id="tabDetails"  href="#panDetails"  data-toggle="tab"> 
                  <i class="fa fa-info-circle"></i> 
                    <span class="dev-detail-tab-name"> 
                      <?= lang('DevDetail_Tab_Details');?>  
                    </span>
                </a>
                </li>
                <li> 
                <a id="tabTools"    href="#panTools"    data-toggle="tab"> 
                  <i class="fa fa-screwdriver-wrench"></i> 
                    <span class="dev-detail-tab-name">
                      <?= lang('DevDetail_Tab_Tools');?>    
                    </span>
                </a>
                </li>
              <li> 
                <a id="tabSessions" href="#panSessions" data-toggle="tab"> 
                  <i class="fa fa-list-ol"></i> 
                    <span class="dev-detail-tab-name">
                      <?= lang('DevDetail_Tab_Sessions');?> 
                    </span>
                </a>
                </li>
              <li> 
                <a id="tabPresence" href="#panPresence" data-toggle="tab"> 
                  <i class="fa fa-calendar"></i> 
                    <span class="dev-detail-tab-name"> 
                      <?= lang('DevDetail_Tab_Presence');?> 
                    </span>
                </a>
                </li>
              <li> 
                <a id="tabEvents"   href="#panEvents"   data-toggle="tab"> 
                  <i class="fa fa-bolt"></i>  
                    <span class="dev-detail-tab-name">
                      <?= lang('DevDetail_Tab_Events');?>   
                    </span>
                </a>
                </li>              
              <li> 
                <a id="tabPlugins"  href="#panPlugins"  data-toggle="tab"> 
                  <i class="fa fa-plug"></i> 
                    <span class="dev-detail-tab-name">
                      <?= lang('DevDetail_Tab_Plugins');?>  
                    </span>
                </a>
                </li>

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
              <?php  
                  require 'deviceDetailsSessions.php';
                ?>
                
              </div>

        
<!-- tab page "Tools" ------------------------------------------------------------ -->

              <div class="tab-pane fade" id="panTools">

                <?php  
                  require 'deviceDetailsTools.php';
                ?>
              
		      
              </div>

<!-- tab page 3 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panPresence">        
                
                <?php
                  // Include the other page
                  include 'deviceDetailsPresence.php';
                ?>

              </div>

<!-- tab page 4 ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" id="panEvents">

              <?php
                  // Include the other page
                  include 'deviceDetailsEvents.php';
                ?>

                
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

  var tab                 = 'tabDetails'
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
   	

  // Init tabs once DOM ready
  $( document ).ready(function() {
    initializeTabs();
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
function periodChanged () {
  loadSessionsData();
  loadPresenceData();
  loadEventsData();
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

  devicesList = getDevicesList()

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

  setCache("naxDeviceDetailsMac", mac);

  // Update the query string with the new MAC and refresh the page
  const baseUrl = window.location.href.split('?')[0];
  window.location.href = `${baseUrl}?mac=${encodeURIComponent(mac)}`;

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
  // $('.nav-tabs a[id='+ selectedTab +']').parent().click();
  //  $('.nav-tabs a[id="tabPlugins"]').tab('show');

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
                "dataValue": `${deviceData.devPresenceHours ?? 0}h`
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


