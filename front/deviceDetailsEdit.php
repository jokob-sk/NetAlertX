<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>


<div class="row">
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
                id="btnDeleteEvents"   
                onclick="askDeleteDeviceEvents()">   
                <?= lang('DevDetail_button_DeleteEvents');?> 
        </button>
        <button type="button" 
                class="btn btn-default pa-btn pa-btn-delete"  
                style="margin-left:0px;"  
                id="btnDelete"   
                onclick="askDeleteDevice()">   
                <?= lang('DevDetail_button_Delete');?> 
        </button>
        <button type="button" 
                class="btn btn-primary pa-btn" 
                style="margin-left:6px; "  
                id="btnSave"     
                onclick="setDeviceData()" >     
                <?= lang('DevDetail_button_Save');?> 
        </button>
    </div>
    </div>
</div>


<script defer>
  
  // -------------------------------------------------------------------  
  // Get plugin and settings data from API endpoints
  function getDeviceData(readAllData){

    mac = getMac()

    console.log(mac);

    // get data from server 
    $.get('php/server/devices.php?action=getServerDeviceData&mac='+ mac + '&period='+ period, function(data) {      

      // show loading dialog
      showSpinner()

      var deviceData = JSON.parse(data);

      // Deactivate next previous buttons
      if (readAllData) {
        $('#btnPrevious').attr    ('disabled','');
        $('#btnPrevious').addClass  ('text-gray50');
        $('#btnNext').attr      ('disabled','');
        $('#btnNext').addClass    ('text-gray50');
      }

      // some race condition, need to implement delay
      setTimeout(() => {
        $.get('api/table_settings.json?nocache=' + Date.now(), function(res) {  
        
        settingsData = res["data"];

        // columns to hide
        hiddenFields = ["NEWDEV_devScan", "NEWDEV_devPresentLastScan" ]
        // columns to disable - conditional depending if a new dummy device is created
        disabledFields =  mac == "new" ? ["NEWDEV_devLastNotification", "NEWDEV_devFirstConnection", "NEWDEV_devLastConnection"] : ["NEWDEV_devLastNotification", "NEWDEV_devFirstConnection", "NEWDEV_devLastConnection", "NEWDEV_devMac", "NEWDEV_devLastIP" ];
        
        // Grouping of fields into categories with associated documentation links
        const fieldGroups = {
            // Group for device main information
            DevDetail_MainInfo_Title: {
                data: ["devMac", "devLastIP", "devName", "devOwner", "devType", "devVendor", "devGroup", "devIcon", "devLocation", "devComments"], 
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICE_MANAGEMENT.md",
                iconClass: "fa fa-pencil"
            },
            // Group for session information
            DevDetail_SessionInfo_Title: {
                data: ["devStatus", "devLastConnection", "devFirstConnection"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/SESSION_INFO.md",
                iconClass: "fa fa-calendar"
            },
             // Group for event and alert settings
             DevDetail_EveandAl_Title: {
                data: ["devAlertEvents", "devAlertDown", "devSkipRepeated"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/NOTIFICATIONS.md",
                iconClass: "fa fa-bell"
            },
            // Group for network details
            DevDetail_MainInfo_Network_Title: {
                data: ["devParentMAC", "devParentPort", "devSSID", "devSite"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/NETWORK_TREE.md",
                iconClass: "fa fa-network-wired"
            },
            // Group for other fields like static IP, archived status, etc.
            DevDetail_DisplayFields_Title: {
                data: ["devStaticIP", "devIsNew", "devFavorite", "devIsArchived"],
                docs: "https://github.com/jokob-sk/NetAlertX/blob/main/docs/DEVICE_DISPLAY_SETTINGS.md",
                iconClass: "fa fa-list-check"

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
                const groupDiv = $('<div>').addClass('field-group col-lg-4 col-sm-6 col-xs-12'); // Create a div for each group with responsive Bootstrap classes
                
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

                    // console.log(setting.setKey);                    
                    // console.log(fieldData);                    

                    // Additional form elements like the random MAC address button for devMac
                    let inlineControl = "";
                    // handle rendom mac
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

                    // handle generate IP for new device
                    if (setting.setKey == "NEWDEV_devIcon") {
                      inlineControl += `<span class="input-group-addon pointer"
                                              onclick="showIconSelection()"
                                              title="${getString("Gen_Select")}">
                                              <i class="fa-solid fa-chevron-down" ></i>
                                          </span>`;
                    }
                    

                    // Generate the input field HTML
                    const inputFormHtml = `<div class="form-group col-xs-12">
                                              <label class="col-sm-4 col-xs-12 control-label"> ${setting.setName}    
                                                  <i my-set-key="${setting.setKey}"
                                                      title="${getString("Settings_Show_Description")}" 
                                                      class="fa fa-circle-info pointer helpIconSmallTopRight" 
                                                      onclick="showDescriptionPopup(this)">
                                                  </i>
                                              </label>
                                              <div class="col-sm-8 col-xs-12 input-group">
                                                  ${generateFormHtml(setting, fieldData.toString())}
                                                  ${inlineControl}
                                              </div>
                                          </div>`;

                    column.append(inputFormHtml);  // Append the input field to the column
                    groupDiv.append(column);       // Append the column to the group div
                });

                form.append(groupDiv);  // Append the group div (containing columns) to the form
            });


            // wait until everything is initialized to update icon
            updateIconPreview();

            // update readonly fields
            handleReadOnly(settingsData, disabledFields);

            // Page title - Name
            if (mac == "new") {
                $('#pageTitle').html(`<i title="${getString("Gen_create_new_device")}" class="fa fa-square-plus"></i> ` +  getString("Gen_create_new_device"));
            } else if (deviceData['devOwner'] == null || deviceData['devOwner'] == '' ||
                (deviceData['devName'].toString()).indexOf(deviceData['devOwner']) != -1) {
                $('#pageTitle').html(deviceData['devName']);
            } else {
                $('#pageTitle').html(deviceData['devName'] + ' (' + deviceData['devOwner'] + ')');
            }
        };

        // console.log(relevantSettings)

        generateSimpleForm(relevantSettings);

        // <> chevrons
        updateChevrons(deviceData)

        toggleNetworkConfiguration(mac == 'Internet') 

        hideSpinner();
      
      })
    
      }, 1);
    });
  
  }
  

  // ----------------------------------------
  // Handle previous/next arrows/chevrons
  function updateChevrons(deviceData) {

    devicesList = getDevicesList();    

    // console.log(devicesList);

    // Check if device is part of the devicesList      
    pos = devicesList.findIndex(item => item.rowid == deviceData['rowid']);        
    
    // console.log(pos);    

    if (pos == -1) {
      devicesList.push({"rowid" : deviceData['rowid'], "mac" : deviceData['devMac'], "name": deviceData['devName'], "type": deviceData['devType']});
      pos=0;
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


  // ----------------------------------------
  // Show the description of a setting
  function showDescriptionPopup(e) {

    console.log($(e).attr("my-set-key"));    

    showModalOK("Info", getString($(e).attr("my-set-key") + '_description'))
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
    updateApi("devices,appevents")
  }

  // -----------------------------------------------------------------------------
  function setDeviceData(direction = '', refreshCallback = '') {
    // Check MAC
    if (mac === '') {
      return;
    }

    // Determine if a new device should be created
    const createNew = mac === 'new' ? 1 : 0;

    const devLastIP = $('#NEWDEV_devLastIP').val();

    // Validate MAC and Last IP
    if (mac === '' || !(isValidIPv4(devLastIP) || isValidIPv6(devLastIP))) {
      showMessage(getString("DeviceEdit_ValidMacIp"), 5000, "modal_red");
      return;
    }

    showSpinner();

     // update data to server
     $.get('php/server/devices.php?action=setDeviceData&mac='+ $('#NEWDEV_devMac').val()
      + '&name='           + encodeURIComponent($('#NEWDEV_devName').val().replace(/'/g, ""))
      + '&owner='          + encodeURIComponent($('#NEWDEV_devOwner').val().replace(/'/g, ""))
      + '&type='           + $('#NEWDEV_devType').val()
      + '&vendor='         + encodeURIComponent($('#NEWDEV_devVendor').val().replace(/'/g, ""))
      + '&icon='           + encodeURIComponent($('#NEWDEV_devIcon').val())
      + '&favorite='       + ($('#NEWDEV_devFavorite')[0].checked * 1)
      + '&group='          + encodeURIComponent($('#NEWDEV_devGroup').val())
      + '&location='       + encodeURIComponent($('#NEWDEV_devLocation').val())
      + '&comments='       + encodeURIComponent(encodeSpecialChars($('#NEWDEV_devComments').val()))
      + '&networknode='    + $('#NEWDEV_devParentMAC').val()
      + '&networknodeport=' + $('#NEWDEV_devParentPort').val()
      + '&ssid='            + $('#NEWDEV_devSSID').val()
      + '&networksite='     + $('#NEWDEV_devSite').val()
      + '&staticIP='       + ($('#NEWDEV_devStaticIP')[0].checked * 1)
      + '&scancycle='      + "1"
      + '&alertevents='    + ($('#NEWDEV_devAlertEvents')[0].checked * 1)
      + '&alertdown='      + ($('#NEWDEV_devAlertDown')[0].checked * 1)
      + '&skiprepeated='   + $('#NEWDEV_devSkipRepeated').val().split(' ')[0]
      + '&newdevice='      + ($('#NEWDEV_devIsNew')[0].checked * 1)
      + '&archived='       + ($('#NEWDEV_devIsArchived')[0].checked * 1)
      + '&devFirstConnection='       + ($('#NEWDEV_devFirstConnection').val())
      + '&devLastConnection='       + ($('#NEWDEV_devLastConnection').val())
      + '&ip='             + ($('#NEWDEV_devLastIP').val())
      + '&createNew='          + createNew
      , function(msg) {
      
        showMessage (msg);

        // Remove navigation prompt "Are you sure you want to leave..."
        window.onbeforeunload = null;
        somethingChanged      = false;

        // refresh API
        updateApi("devices,appevents")

        // Callback fuction
        if (typeof refreshCallback == 'function') {
          refreshCallback(direction);
        }

      // everything loaded 
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


  // -------------------- INIT ------------------------
  getDeviceData(true);


</script>