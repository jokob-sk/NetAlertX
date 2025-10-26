<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>


<div class="row" id="deviceDetailsEdit">
  <div class="box-body form-horizontal">
    <form id="edit-form">
    <!-- Form fields will be appended here -->
    </form>
  </div>
  <!-- Buttons -->
  <div class="col-xs-12">
    <div class="pull-right">
        <button type="button" 
                class="btn btn-default pa-btn pa-btn-delete"  
                style="margin-left:0px;"  
                id="btnDelete"   
                onclick="askDeleteDevice()">   
                  <i class="fas fa-trash-alt"></i> 
                  <?= lang('DevDetail_button_Delete');?> 
        </button>
        <button type="button" 
                class="btn btn-primary pa-btn" 
                style="margin-left:6px; "  
                id="btnSave"     
                onclick="setDeviceData()" >     
                  <i class="fas fa-save"></i>
                  <?= lang('DevDetail_button_Save');?> 
        </button>
    </div>
    </div>
</div>


<script defer>
  
  // -------------------------------------------------------------------  
  // Get plugin and settings data from API endpoints
  function getDeviceData(){

    mac = getMac()

    console.log(mac);

    // get data from server 
    $.get('php/server/devices.php?action=getServerDeviceData&mac='+ mac + '&period='+ period, function(data) {      

      // show loading dialog
      showSpinner()

      var deviceData = JSON.parse(data);

      // some race condition, need to implement delay
      setTimeout(() => {
        $.get('php/server/query_json.php', { 
          file: 'table_settings.json', 
          // nocache: Date.now() 
        }, 
          function(res) {  
        
        settingsData = res["data"];

        // columns to hide
        hiddenFields = ["NEWDEV_devScan", "NEWDEV_devPresentLastScan" ]
        // columns to disable/readonly - conditional depending if a new dummy device is created
        disabledFields =  mac == "new" ? ["NEWDEV_devLastNotification", "NEWDEV_devFirstConnection", "NEWDEV_devLastConnection"] : ["NEWDEV_devLastNotification", "NEWDEV_devFirstConnection", "NEWDEV_devLastConnection", "NEWDEV_devMac", "NEWDEV_devLastIP", "NEWDEV_devSyncHubNode", "NEWDEV_devFQDN" ];
        
        // Grouping of fields into categories with associated documentation links
        const fieldGroups = {
            // Group for device main information
            DevDetail_MainInfo_Title: {
                data: ["devMac", "devLastIP", "devName", "devOwner", "devType", "devVendor", "devGroup", "devIcon", "devLocation", "devComments"], 
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICE_MANAGEMENT.md",
                iconClass: "fa fa-pencil",
                inputGroupClasses: "field-group main-group col-lg-4 col-sm-6 col-xs-12",
                labelClasses: "col-sm-4 col-xs-12 control-label",
                inputClasses: "col-sm-8 col-xs-12 input-group"
            },            
             // Group for event and alert settings
             DevDetail_EveandAl_Title: {
                data: ["devAlertEvents", "devAlertDown", "devSkipRepeated", "devReqNicsOnline", "devChildrenNicsDynamic"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/NOTIFICATIONS.md",
                iconClass: "fa fa-bell",
                inputGroupClasses: "field-group alert-group col-lg-4 col-sm-6 col-xs-12",
                labelClasses: "col-sm-4 col-xs-12 control-label",
                inputClasses: "col-sm-8 col-xs-12 input-group"
            },
            // Group for network details
            DevDetail_MainInfo_Network_Title: {
                data: ["devParentMAC", "devParentRelType", "devParentPort", "devSSID", "devSite", "devSyncHubNode"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/NETWORK_TREE.md",
                iconClass: "fa fa-sitemap fa-rotate-270",
                inputGroupClasses: "field-group network-group col-lg-4 col-sm-6 col-xs-12",
                labelClasses: "col-sm-4 col-xs-12 control-label",
                inputClasses: "col-sm-8 col-xs-12 input-group"
            },
            // Group for other fields like static IP, archived status, etc.
            DevDetail_DisplayFields_Title: {
                data: ["devStaticIP", "devIsNew", "devFavorite", "devIsArchived"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICE_DISPLAY_SETTINGS.md",
                iconClass: "fa fa-list-check",
                inputGroupClasses: "field-group display-group col-lg-4 col-sm-6 col-xs-12",
                labelClasses: "col-sm-4 col-xs-12 control-label",
                inputClasses: "col-sm-8 col-xs-12 input-group"
            },
            // Group for session information
            DevDetail_SessionInfo_Title: {
                data: ["devStatus", "devLastConnection", "devFirstConnection", "devFQDN"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/SESSION_INFO.md",
                iconClass: "fa fa-calendar",
                inputGroupClasses: "field-group session-group col-lg-4 col-sm-6 col-xs-12",
                labelClasses: "col-sm-4 col-xs-12 control-label",
                inputClasses: "col-sm-8 col-xs-12 input-group"
            },
            // Group for Children.
            DevDetail_Children_Title: {
                data: ["devChildrenDynamic"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/NETWORK_TREE.md",
                iconClass: "fa fa-list",
                inputGroupClasses: "field-group cutprop-group col-lg-6 col-sm-12 col-xs-12",
                labelClasses: "col-sm-12 col-xs-12 control-label",
                inputClasses: "col-sm-12 col-xs-12 input-group"
            },
            // Group for Custom properties.
            DevDetail_CustomProperties_Title: {
                data: ["devCustomProps"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/CUSTOM_PROPERTIES.md",
                iconClass: "fa fa-list",
                inputGroupClasses: "field-group cutprop-group col-lg-6 col-sm-12 col-xs-12",
                labelClasses: "col-sm-12 col-xs-12 control-label",
                inputClasses: "col-sm-12 col-xs-12 input-group"
            }
        };

        // Filter settings data to get relevant settings
        const relevantSettings = settingsData.filter(set =>
            set.setGroup === "NEWDEV" &&               // Filter for settings in the "NEWDEV" group
            set.setKey.includes("_dev") &&             // Include settings with '_dev' in the key
            !hiddenFields.includes(set.setKey) &&     // Exclude settings listed in hiddenFields
            !set.setKey.includes("__metadata")        // Exclude metadata fields
        );

        // Function to generate the form
        const generateSimpleForm = settings => {
            const form = $('#edit-form');  // Get the form element to append generated fields

            // Loop over each field group to generate sections for each category
            Object.entries(fieldGroups).forEach(([groupName, obj]) => {
                const groupDiv = $('<div>').addClass(obj.inputGroupClasses); // Create a div for each group with responsive Bootstrap classes
                
                // Add group title and documentation link
                groupDiv.append(`<h5><i class="${obj.iconClass}"></i>  ${getString(groupName)} 
                                    <span class="helpIconSmallTopRight">
                                        <a target="_blank" href="${obj.docs}">
                                            <i class="fa fa-circle-question"></i>
                                        </a>
                                    </span> 
                                  </h5>
                                  <hr>
                                `);

                // Filter relevant settings for the current group
                const groupSettings = settings.filter(set => obj.data.includes(set.setKey.replace('NEWDEV_', '')));

                // Loop over each setting in the group to generate form fields
                groupSettings.forEach(setting => {
                    const column = $('<div>');  // Create a column for each setting (Bootstrap column)

                    // Get the field data (replace 'NEWDEV_' prefix from the key)
                    fieldData = deviceData[setting.setKey.replace('NEWDEV_', '')]
                    fieldData = fieldData == null ? "" : fieldData;
                    fieldOptionsOverride = null;

                    // console.log(setting.setKey);                    
                    // console.log(fieldData);                    

                    // Additional form elements like the random MAC address button for devMac
                    let inlineControl = "";
                    // handle random mac
                    if (setting.setKey == "NEWDEV_devMac" && deviceData["devIsRandomMAC"] == true) {
                      inlineControl += `<span class="input-group-addon pointer"
                                              title="${getString("RandomMAC_hover")}">
                                              <a href="https://github.com/jokob-sk/NetAlertX/blob/main/docs/RANDOM_MAC.md" target="_blank">     
                                                  <i class="fa-solid fa-shuffle"></i>
                                              </a>
                                          </span>`;
                    }
                    // handle generate MAC for new device
                    if (setting.setKey == "NEWDEV_devMac" && deviceData["devMac"] == "") {
                      inlineControl += `<span class="input-group-addon pointer"
                                              onclick="generate_NEWDEV_devMac()"
                                              title="${getString("Gen_Generate")}">
                                              <i class="fa-solid fa-dice" ></i>
                                          </span>`;
                    }
                    // handle generate IP for new device
                    if (setting.setKey == "NEWDEV_devLastIP" && deviceData["devLastIP"] == "") {
                      inlineControl += `<span class="input-group-addon pointer"
                                              onclick="generate_NEWDEV_devLastIP()"
                                              title="${getString("Gen_Generate")}">
                                              <i class="fa-solid fa-dice" ></i>
                                          </span>`;
                    }
                    
                    // handle devChildrenDynamic or NEWDEV_devChildrenNicsDynamic - selected values and options are the same
                    if ( 
                        Array.isArray(fieldData) && 
                        (setting.setKey == "NEWDEV_devChildrenDynamic" || 
                        setting.setKey == "NEWDEV_devChildrenNicsDynamic" )                  
                        ) 
                      {  
                      fieldDataNew = []                    
                      fieldData.forEach(child => {
                        fieldDataNew.push(child.devMac)
                      })
                      fieldData = fieldDataNew;
                      fieldOptionsOverride = fieldDataNew;
                    }

                    // Generate the input field HTML
                    const inputFormHtml = `<div class="form-group col-xs-12">
                                              <label id="${setting.setKey}_label" class="${obj.labelClasses}" > ${setting.setName}    
                                                  <i my-set-key="${setting.setKey}"
                                                      title="${getString("Settings_Show_Description")}" 
                                                      class="fa fa-circle-info pointer helpIconSmallTopRight" 
                                                      onclick="showDescriptionPopup(this)">
                                                  </i>
                                              </label>
                                              <div class="${obj.inputClasses}">
                                                  ${generateFormHtml(settingsData, setting, fieldData.toString(), fieldOptionsOverride, null)}
                                                  ${inlineControl}
                                              </div>
                                          </div>`;

                    column.append(inputFormHtml);  // Append the input field to the column
                    groupDiv.append(column);       // Append the column to the group div
                });

                form.append(groupDiv);  // Append the group div (containing columns) to the form
            });


            // wait until everything is initialized to update icons
            updateAllIconPreviews();

            // update readonly fields
            handleReadOnly(settingsData, disabledFields);           
          };

          // console.log(relevantSettings)

          generateSimpleForm(relevantSettings);

          toggleNetworkConfiguration(mac == 'Internet') 

          initSelect2();
          initHoverNodeInfo();

          hideSpinner();
        
        })
      
        }, 100);
      });
    
    }


  

  // ----------------------------------------
  // Handle the read-only fields
  function handleReadOnly(settingsData, disabledFields) {
    settingsData.forEach(setting => {
    const element = $(`#${setting.setKey}`);
    if (disabledFields.includes(setting.setKey)) {
      element.prop('readonly', true);
    } else {
      element.prop('readonly', false);
    }
  });
  }

  // -----------------------------------------------------------------------------
  // Save device data to DB
  function setDeviceData(direction = '', refreshCallback = '') {
    // Check MAC
    if (mac === '') {
      return;
    }

    // Determine if a new device should be created
    const createNew = mac === 'new' ? 1 : 0;

    const devLastIP = $('#NEWDEV_devLastIP').val();
    const newMac = $('#NEWDEV_devMac').val()

    // Validate MAC and Last IP
    if (mac === '' || !isValidMac(newMac) || !( isValidIPv4(devLastIP) || isValidIPv6(devLastIP) )) {
      showMessage(getString("DeviceEdit_ValidMacIp"), 5000, "modal_red");
      return;
    }

    showSpinner();

    // Update data to server using POST
    $.post('php/server/devices.php?action=setDeviceData', {
        mac: $('#NEWDEV_devMac').val(),
        name: encodeURIComponent($('#NEWDEV_devName').val().replace(/'/g, "’")),
        owner: encodeURIComponent($('#NEWDEV_devOwner').val().replace(/'/g, "’")),
        type: $('#NEWDEV_devType').val().replace(/'/g, ""),        
        vendor: encodeURIComponent($('#NEWDEV_devVendor').val().replace(/'/g, "’")),
        icon: encodeURIComponent($('#NEWDEV_devIcon').val()),
        favorite: ($('#NEWDEV_devFavorite')[0].checked * 1),
        group: encodeURIComponent($('#NEWDEV_devGroup').val().replace(/'/g, "’")),
        location: encodeURIComponent($('#NEWDEV_devLocation').val().replace(/'/g, "’")),
        comments: encodeURIComponent(encodeSpecialChars($('#NEWDEV_devComments').val())),
        networknode: $('#NEWDEV_devParentMAC').val(),
        networknodeport: $('#NEWDEV_devParentPort').val(),
        ssid: $('#NEWDEV_devSSID').val(),
        networksite: $('#NEWDEV_devSite').val(),
        staticIP: ($('#NEWDEV_devStaticIP')[0].checked * 1),
        scancycle: "1",
        alertevents: ($('#NEWDEV_devAlertEvents')[0].checked * 1),
        alertdown: ($('#NEWDEV_devAlertDown')[0].checked * 1),
        skiprepeated: $('#NEWDEV_devSkipRepeated').val().split(' ')[0],
        relType: $('#NEWDEV_devParentRelType').val().replace(/'/g, ""),
        reqNics: ($('#NEWDEV_devReqNicsOnline')[0].checked * 1),
        newdevice: ($('#NEWDEV_devIsNew')[0].checked * 1),
        archived: ($('#NEWDEV_devIsArchived')[0].checked * 1),
        devFirstConnection: ($('#NEWDEV_devFirstConnection').val()),
        devLastConnection: ($('#NEWDEV_devLastConnection').val()),
        devCustomProps: btoa(JSON.stringify(collectTableData("#NEWDEV_devCustomProps_table"))),
        ip: ($('#NEWDEV_devLastIP').val()),
        createNew: createNew
    }, function(msg) {
        showMessage(msg);

        // Remove navigation prompt "Are you sure you want to leave..."
        window.onbeforeunload = null;
        somethingChanged = false;

        // refresh API
        updateApi("devices,appevents");

        // Callback function
        if (typeof refreshCallback == 'function') {
            refreshCallback(direction);
        }

        // Everything loaded
        hideSpinner();
    });
  }

  //-----------------------------------------------------------------------------------
  // Disables or enables network configuration for the root node
  function toggleNetworkConfiguration(disable) {
    if (disable) {  
      // Completely disable the NEWDEV_devParentMAC <select> and NEWDEV_devParentPort
      $('#NEWDEV_devParentMAC').prop('disabled', true).val("").prop('selectedIndex', 0); 
      $('#NEWDEV_devParentMAC').empty() // Remove all options
      .append('<option value="">Root Node</option>')
      $('#NEWDEV_devParentPort').prop('disabled', true);
      $('#NEWDEV_devParentPort').prop('readonly', true );
      $('#NEWDEV_devParentMAC').prop('readonly', true );
    } else {
      // Enable the NEWDEV_devParentMAC <select> and NEWDEV_devParentPort
      $('#NEWDEV_devParentMAC').prop('disabled', false);
      $('#NEWDEV_devParentPort').prop('disabled', false);
      $('#NEWDEV_devParentPort').prop('readonly', false );
      $('#NEWDEV_devParentMAC').prop('readonly', false );
    }
  }

// -----------------------------------------------
// INIT with polling for panel element visibility
// -----------------------------------------------

var deviceDetailsPageInitialized = false; 

function initdeviceDetailsPage()
{
  // Only proceed if .plugin-content is visible
  if (!$('#panDetails:visible').length) {
    return; // exit early if nothing is visible
  }

  // init page once
  if (deviceDetailsPageInitialized) return; //  ENSURE ONCE
  deviceDetailsPageInitialized = true;

  showSpinner();

  getDeviceData();

}

// -----------------------------------------------------------------------------
// Recurring function to monitor the URL and reinitialize if needed
function deviceDetailsPageUpdater() {
  initdeviceDetailsPage();

  // Run updater again after delay
  setTimeout(deviceDetailsPageUpdater, 200);
}

// if visible, load immediately, if not start updater
if (!$('#panDetails:visible').length) {
  deviceDetailsPageUpdater();
}
else
{
  getDeviceData();
}



</script>