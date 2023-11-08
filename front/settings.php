<?php

require 'php/templates/header.php';

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
// Set maximum execution time to 15 seconds
ini_set ('max_execution_time','30');

// check permissions
$dbPath = "../db/pialert.db";
$confPath = "../config/pialert.conf";

checkPermissions([$dbPath, $confPath]);

// get settings from the API json file

// path to your JSON file
$file = '../front/api/table_settings.json'; 
// put the content of the file in a variable
$data = file_get_contents($file); 
// JSON decode
$settingsJson = json_decode($data); 

// get settings from the DB

global $db;
global $settingKeyOfLists;

$result = $db->query("SELECT * FROM Settings");  

// array 
$settingKeyOfLists = array();

$settings = array();
while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {   
  // Push row data      
  $settings[] = array(  'Code_Name'    => $row['Code_Name'],
                        'Display_Name' => $row['Display_Name'],
                        'Description'  => $row['Description'],
                        'Type'         => $row['Type'],
                        'Options'      => $row['Options'],
                        'RegEx'        => $row['RegEx'],
                        'Value'        => $row['Value'],
                        'Group'        => $row['Group'],
                        'Events'       => $row['Events']
                      ); 
}


?>
<!-- Page ------------------------------------------------------------------ -->
<!-- Page ------------------------------------------------------------------ -->

<script src="js/pialert_common.js"></script>
<script src="js/settings_utils.js"></script>


<div id="settingsPage" class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
          <i class="fa fa-cog"></i>
          <?= lang('Navigation_Settings');?> 
          <a style="cursor:pointer">
            <span>
              <i id='toggleSettings' onclick="toggleAllSettings()" class="settings-expand-icon fa fa-angle-double-down"></i>
            </span> 
          </a>
      </h1>

      <div class="col-sm-2 " title="<?= lang("settings_imported");?> ">
        <div class="settingsImported">
          <?= lang("settings_imported_label");?>           
        </div>
      </div>
      <div class="col-sm-10">
        <span id="lastImportedTime"></span>
      </div>           

          
    </section>
    <section class="content-header">

    <div id="settingsOverview" class ="bg-white color-palette box panel panel-default col-sm-12 box-default box-info" > 
      <!-- Settings imported time -->

      <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_enabled_icon");?>"></i>  <?= lang("settings_enabled");?>       
          </div>        
          <div class =" col-sm-12" id=""></div>

    </section>


    <div class="content settingswrap " id="accordion_gen">

      <div class ="bg-grey-dark color-palette box panel panel-default col-sm-12 box-default box-info" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_core_icon");?>"></i>  <?= lang("settings_core_label");?>       
          </div>        
          <div class =" col-sm-12" id="core_content"></div>
      </div>    

      <div class ="bg-grey-dark color-palette box panel panel-default col-sm-12 box-default box-info" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_system_icon");?>"></i>  <?= lang("settings_system_label");?>       
          </div>        
          <div class =" col-sm-12" id="system_content"></div>
      </div> 

      <div class ="bg-grey-dark color-palette box panel panel-default col-sm-12 box-default box-info" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_device_scanners_icon");?>"></i>  <?= lang("settings_device_scanners_label");?>     
          </div>        
          <div class =" col-sm-12" id="device_scanner_content"></div>
      </div> 

      <div class ="bg-grey-dark color-palette box panel panel-default col-sm-12 box-default box-info" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_other_scanners_icon");?>"></i>  <?= lang("settings_other_scanners_label");?>       
          </div>        
          <div class =" col-sm-12" id="other_content"></div>
      </div> 

      <div class ="bg-grey-dark color-palette box panel panel-default col-sm-12 box-default box-info" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_publishers_icon");?>"></i>  <?= lang("settings_publishers_label");?>       
          </div>        
          <div class =" col-sm-12" id="publisher_content"></div>
      </div> 
     
   </div>
   
    <!-- /.content -->
    <div class="row" >
          <div class="row">
            <button type="button" class="center top-margin  btn btn-primary btn-default pa-btn bg-green dbtools-button" id="save" onclick="saveSettings()"><?= lang('DevDetail_button_Save');?></button>
          </div>
          <div id="result"></div>
      </div>
</div>


  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';  
?>


<script>
  


  // -------------------------------------------------------------------  
  // Get plugin and settings data from API endpoints
  function getData(){

    $.get('api/table_settings.json?nocache=' + Date.now(), function(res) {    
        
        settingsData = res["data"];       

        $.get('api/plugins.json?nocache=' + Date.now(), function(res) {  

          pluginsData = res["data"];  

          initSettingsPage(settingsData, pluginsData);
        })
    })
  }

  // -------------------------------------------------------------------
  // main initialization function
  function initSettingsPage(settingsData, pluginsData){

    const settingGroups = [];
    const settingKeyOfLists = [];
    
    const enabledDeviceScanners = getPluginsByType(pluginsData, "device_scanner", true);    
    const enabledOthers         = getPluginsByType(pluginsData, "other", true);    
    const enabledPublishers     = getPluginsByType(pluginsData, "publisher", true);



    // Loop through the settingsArray and:
    //    - collect unique settingGroups
    //    - collect enabled plugins

    settingsData.forEach((set) => {
      // settingGroups
      if (!settingGroups.includes(set.Group)) {
        settingGroups.push(set.Group); // = Unique plugin prefix
      }      
    });    

    // Init the overview section
    overviewSections      = [
                              'device_scanners',  
                              'other_scanners', 
                              'publishers'                                                          
                            ]
    overviewSectionsHtml  = [
                              pluginCards(enabledDeviceScanners,['RUN', 'RUN_SCHD']),
                              pluginCards(enabledOthers, ['RUN', 'RUN_SCHD']), 
                              pluginCards(enabledPublishers, []), 
                              
                            ]

    index = 0
    overviewSections_html = ''

    overviewSections.forEach((section) => {

      overviewSections_html += `<div class="overview-section col-sm-12" id="${section}">
                                  <div class="col-sm-12 " title="${getString("settings_"+section)}">
                                    <div class="overview-group col-sm-12">
                                    
                                      <i title="${section}" class="${getString("settings_"+section+"_icon")}"></i>       
          
                                      ${getString("settings_"+section+"_label")}                                      
                                    </div>                                    
                                  </div>
                                  <div class="col-sm-12">
                                    ${overviewSectionsHtml[index]}        
                                  </div>
                                </div>`
      index++;
    });

    $('#settingsOverview').append(overviewSections_html);

    // Display warning 
    if(schedulesAreSynchronized(enabledDeviceScanners, pluginsData) == false)
    {
      $("#device_scanners").append(
        `
          <small class="label pull-right bg-red pointer" onClick="showModalOk('WARNING', '${getString("Settings_device_Scanners_desync_popup")}')">
            ${getString('Settings_device_Scanners_desync')}
          </small>
        `)
    } 
    
    // Start constructing the main settings HTML 
    let pluginHtml = `
          <div class="row table_row">
            <div class="table_cell bold">
              <i class="fa-regular fa-book fa-sm"></i>
              <a href="https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins" target="_blank">
                ${getString('Gen_ReadDocs')}
              </a>
            </div>
          </div>
        `;

    let isIn = ' in '; // to open the active panel in AdminLTE

    for (const group of settingGroups) {     

      // enabled / disabled icons
      enabledHtml = ''

      if(getSetting(group+"_RUN") != "")
      {
        let isEnabled =  ["once", "schedule", "always_after_scan", "on_new_device", "on_notification", "before_config_save"  ].includes(getSetting(group+"_RUN"));      

        isEnabled ? onOff = 'on' : onOff = 'off';

        enabledHtml = `
                      <div class="enabled-disabled-icon">
                        <i class="fa-solid fa-toggle-${onOff}"></i>
                      </div>
                      `
      }      

      headerHtml = `<div class="box box-solid box-primary panel panel-default">
                  <a data-toggle="collapse" data-parent="#accordion_gen" href="#${group}">
                    <div class="panel-heading">
                      <h4 class="panel-title">
                        <div class="col-sm-1 col-xs-1">${getString(group+"_icon")}   </div>
                        <div class="col-sm-10 col-xs-8">${getString(group+"_display_name")} </div>     
                        <div class="col-sm-1 col-xs-1">${enabledHtml} </div>
                      </h4>                      
                    </div>
                  </a>
                  <div id="${group}" data-myid="collapsible" class="panel-collapse collapse ${isIn}">
                    <div class="panel-body">
                    ${group != "general" ? pluginHtml: ""}                    
                    </div>
                  </div>
                </div>
                    `;
      isIn = ' '; // open the first panel only by default on page load

      // generate headers/sections      
      $('#'+getPluginType(pluginsData, group) + "_content").append(headerHtml);
    }  


    // generate panel content
    for (const group of settingGroups) {

      // go thru all settings and collect settings per settings group 
      settingsData.forEach((set) => {

        let val = set['Value'];
        const codeName = set['Code_Name'];
        const setType = set['Type'].toLowerCase();
        const isMetadata = codeName.includes('__metadata');
        // is this isn't a metadata entry, get corresponding metadata object from the dummy setting
        const setObj = isMetadata ? {} : JSON.parse(getSetting(`${codeName}__metadata`));

        // constructing final HTML for the setting
        setHtml = ""

        if(set["Group"] == group)
        {
          // hide metadata by default by assigning it a special class          
          isMetadata ? metadataClass = 'metadata' : metadataClass = '';
          isMetadata ? infoIcon = '' : infoIcon = `<i 
                                                      my-to-toggle="row_${codeName}__metadata"
                                                      title="${getString("Settings_Metadata_Toggle")}" 
                                                      class="fa fa-circle-question pointer" 
                                                      onclick="toggleMetadata(this)">
                                                    </i>` ;

          // NAME & DESCRIPTION columns
          setHtml += `
                    <div class="row table_row ${metadataClass}" id="row_${codeName}">
                      <div class="table_cell setting_name bold">
                        <label>${getString(codeName + '_name', set['Display_Name'])}</label>
                        <div class="small">
                          <code>${codeName}</code>${infoIcon}
                        </div>
                      </div>
                      <div class="table_cell setting_description">
                        ${getString(codeName + '_description', set['Description'])}
                      </div>
                      <div class="table_cell setting_input input-group">
                  `;

          // OVERRIDE
          // surface settings override functionality if the setting is a template that can be overriden with user defined values
          // if the setting is a json of the correct structure, handle like a template setting

          let overrideHtml = "";  

          //pre-check if this is a json object that needs value extraction

          let overridable = false;  // indicates if the setting is overridable
          let override = false;     // If the setting is set to be overriden by the user or by default     
          let readonly = "";        // helper variable to make text input readonly
          let disabled = "";        // helper variable to make checkbox input readonly

          // TODO finish
          if ('override_value' in setObj) {
            overridable = true;
            overrideObj = setObj["override_value"]
            override = overrideObj["override"];            

            console.log(setObj)
            console.log(group)
          }

          // prepare override checkbox and HTML
          if(overridable)
          { 
            let checked = override ? 'checked' : '';   

            overrideHtml = `<div class="override col-xs-12">
                              <div class="override-check col-xs-1">
                                <input onChange="overrideToggle(this)" my-data-type="${setType}" my-input-toggle-readonly="${codeName}" class="checkbox" id="${codeName}_override" type="checkbox" ${checked} />
                              </div>
                              <div class="override-text col-xs-11" title="${getString("Setting_Override_Description")}">
                                ${getString("Setting_Override")}
                              </div>
                            </div>`;            

          } 

          
          // INPUT
          // pre-processing done, render setting based on type        

          let inputHtml = "";
          if (setType.startsWith('text') || setType.startsWith('string') || setType.startsWith('date-time') ) {
            
            if(setType.includes(".select"))
            {
              inputHtml = generateInputOptions(set, inputHtml, isMultiSelect = false)

            } else if(setType.includes(".multiselect"))
            {
              inputHtml = generateInputOptions(set, inputHtml, isMultiSelect = true)
            } else{

              // if it's overridable set readonly accordingly
              if(overridable)
              {
                override ? readonly = "" : readonly = " readonly" ; 
              }

              inputHtml = `<input class="form-control" onChange="settingsChanged()"  my-data-type="${setType}"  id="${codeName}" value="${val}" ${readonly}/>`;
            }            
          } else if (setType === 'integer') {
            inputHtml = `<input onChange="settingsChanged()"  my-data-type="${setType}" class="form-control" id="${codeName}" type="number" value="${val}"/>`;
          } else if (setType === 'password') {
            inputHtml = `<input onChange="settingsChanged()"  my-data-type="${setType}"  class="form-control input" id="${codeName}" type="password" value="${val}"/>`;
          } else if (setType === 'readonly') {
            inputHtml = `<input class="form-control input"  my-data-type="${setType}"  id="${codeName}"  value="${val}" readonly/>`;
          } else if (setType === 'boolean' || setType === 'integer.checkbox') {
            let checked = val === 'True' || val === '1' ? 'checked' : '';                   

            // if it's overridable set readonly accordingly
            if(overridable)
            {
              override ? disabled = "" : disabled = " disabled" ;
            }             

            inputHtml = `<input onChange="settingsChanged()" my-data-type="${setType}" class="checkbox" id="${codeName}" type="checkbox" value="${val}" ${checked} ${disabled}/>`;          
          } else if (setType === 'integer.select') {

            inputHtml = generateInputOptions(set, inputHtml)
          
          } else if (setType === 'subnets') {
            inputHtml = `
            <div class="row form-group">
              <div class="col-xs-5">
                <input class="form-control"  id="ipMask" type="text" placeholder="192.168.1.0/24"/>
              </div>
              <div class="col-xs-4">
                <input class="form-control" id="ipInterface" type="text" placeholder="eth0" />
              </div>
              <div class="col-xs-3">
                <button class="btn btn-primary" onclick="addInterface()">Add</button>
              </div>
            </div>
            <div class="form-group">
              <select class="form-control" my-data-type="${setType}" name="${codeName}" id="${codeName}" multiple readonly>`;


            options = createArray(val);

            options.forEach(option => {
              inputHtml += `<option value="${option}" disabled>${option}</option>`;
            });

            inputHtml += '</select></div>' +
            '<div><button class="btn btn-primary" onclick="removeInterfaces()">Remove all</button></div>';
          } else if (setType === 'list' || setType === 'list.readonly') {

            settingKeyOfLists.push(codeName);

            inputHtml = `
              <div class="row form-group">
                <div class="col-xs-9">
                  <input class="form-control" type="text" id="${codeName}_input" placeholder="Enter value"/>
                </div>
                <div class="col-xs-3">
                  <button class="btn btn-primary" my-input-from="${codeName}_input" my-input-to="${codeName}" onclick="addList(this)">Add</button>
                </div>
              </div>
              <div class="form-group">
                <select class="form-control" my-data-type="${setType}" name="${codeName}" id="${codeName}" multiple readonly>`;

            let options = createArray(val);

            options.forEach(option => {
              inputHtml += `<option value="${option}" disabled>${option}</option>`;
            });

            inputHtml += '</select></div>' +
            `<div><button class="btn btn-primary" my-input="${codeName}" onclick="removeFromList(this)">Remove last</button></div>`;
          } else if (setType === 'json') {
            inputHtml = `<textarea class="form-control input" my-data-type="${setType}" id="${codeName}" readonly>${JSON.stringify(val, null, 2)}</textarea>`;
          }

          // EVENTS
          // process events (e.g. run ascan, or test a notification) if associated with the setting
          let eventsHtml = "";          

          const eventsList = createArray(set['Events']);          

          if (eventsList.length > 0) {
            // console.log(eventsList)
            eventsList.forEach(event => {
              eventsHtml += `<span class="input-group-addon pointer"
                data-myparam="${codeName}"
                data-myparam-plugin="${group}"
                data-myevent="${event}"
                onclick="addToExecutionQueue(this)"
              >
                <i title="${getString(event + "_event_tooltip")}" class="fa ${getString(event + "_event_icon")}">                 
                </i>
              </span>`;
            });
          }

          // construct final HTML for the setting
          setHtml += inputHtml +  eventsHtml + overrideHtml + `
              </div>
            </div>
          `

          // generate settings in the correct group section
          $(`#${group} .panel-body`).append(setHtml);
          
        }
      });

    }

  }




  // ---------------------------------------------------------
  // generate a list of options for a input select
  function generateInputOptions(set, input, isMultiSelect = false)
  {

    multi = isMultiSelect ? "multiple" : "";
    input = `<select onChange="settingsChanged()"  my-data-type="${set['Type']}" class="form-control" name="${set['Code_Name']}" id="${set['Code_Name']}" ${multi}>`;

            values = createArray(set['Value']);
            options = createArray(set['Options']);

            options.forEach(option => {
              let selected = values.includes(option) ? 'selected' : '';
              input += `<option value="${option}" ${selected}>${option}</option>`;
            });

            input += '</select>';

    return input;
  }

  

  // ---------------------------------------------------------  
  // Helper methods
  // ---------------------------------------------------------  
  // Toggle readonly mode of teh target element specified by the id in the "my-input-toggle-readonly" attribute
  function overrideToggle(element) {
    settingsChanged();

    targetId = $(element).attr("my-input-toggle-readonly");

    inputElement = $(`#${targetId}`)[0];    

    if (!inputElement) {
      console.error("Input element not found!");
      return;
    }

    if (inputElement.type === "text" || inputElement.type === "password") {
      inputElement.readOnly = !inputElement.readOnly;
    } else if (inputElement.type === "checkbox") {
      inputElement.disabled = !inputElement.disabled;
    } else {
      console.warn("Unsupported input type. Only text, password, and checkbox inputs are supported.");
    }

  }

  // ---------------------------------------------------------  
  // Generate an array object from a string representation of an array
  function createArray(input) {
    // Empty array
    if (input === '[]') {
      return [];
    }

    // Regex patterns
    const patternBrackets = /(^\s*\[)|(\]\s*$)/g;
    const patternQuotes = /(^\s*')|('\s*$)/g;
    const replacement = '';

    // Remove brackets
    const noBrackets = input.replace(patternBrackets, replacement);

    const options = [];

    // Create array
    const optionsTmp = noBrackets.split(',');

    // Handle only one item in array
    if (optionsTmp.length === 0) {
      return [noBrackets.replace(patternQuotes, replacement)];
    }

    // Remove quotes
    optionsTmp.forEach(item => {
      options.push(item.replace(patternQuotes, replacement).trim());
    });

    return options;
  }

  // number of settings has to be equal to

  // display the name of the first person
  // echo $settingsJson[0]->name;
  var settingsNumber = <?php echo count($settingsJson->data)?>;

  // Wrong number of settings processing
  if(<?php echo count($settings)?> != settingsNumber) 
  {
    showModalOk('WARNING', "<?= lang("settings_missing")?>");    
  }

  // ---------------------------------------------------------
  function addList(element)
  {

    const fromId = $(element).attr('my-input-from');
    const toId = $(element).attr('my-input-to');

    input = $(`#${fromId}`).val();
    $(`#${toId}`).append($("<option disabled></option>").attr("value", input).text(input));
    
    // clear input
    $(`#${fromId}`).val("");

    settingsChanged();
  }
  // ---------------------------------------------------------
  function removeFromList(element)
  {
    settingsChanged();    
    $(`#${$(element).attr('my-input')}`).find("option:last").remove();
  }
  // ---------------------------------------------------------
  function addInterface()
  {
    ipMask = $('#ipMask').val();
    ipInterface = $('#ipInterface').val();

    full = ipMask + " --interface=" + ipInterface;

    console.log(full)

    if(ipMask == "" || ipInterface == "")
    {
      showModalOk ('Validation error', 'Specify both, the network mask and the interface');
    } else {
      $('#SCAN_SUBNETS').append($('<option disabled></option>').attr('value', full).text(full));

      $('#ipMask').val('');
      $('#ipInterface').val('');

      settingsChanged();
    }
  }

  // ---------------------------------------------------------
  function removeInterfaces()
  {
    settingsChanged();
    $('#SCAN_SUBNETS').empty();
  }

  // ---------------------------------------------------------
  function collectSettings()
  {
    var settingsArray = [];

    // collect values for each of the different input form controls
    const noConversion = ['text', 'integer', 'string', 'password', 'readonly', 'text.select', 'integer.select', 'text.multiselect'];

    settingsJSON["data"].forEach(set => {
      if (noConversion.includes(set['Type'])) {

        settingsArray.push([set["Group"], set["Code_Name"], set["Type"], $('#'+set["Code_Name"]).val()]);

      } else if (set['Type'] === 'boolean' || set['Type'] === 'integer.checkbox') {
        
        const temp = $(`#${set["Code_Name"]}`).is(':checked') ? 1 : 0;
        settingsArray.push([set["Group"], set["Code_Name"], set["Type"], temp]);
      
      } else if (set['Type'] === 'list' || set['Type'] === 'subnets') {
        const temps = [];
        $(`#${set["Code_Name"]} option`).each(function (i, selected) {
          const vl = $(selected).val();
          if (vl !== '') {
            temps.push(vl);
          }
        });        
        settingsArray.push([set["Group"], set["Code_Name"], set["Type"], JSON.stringify(temps)]);
      } else if (set['Type'] === 'json') {        
        const temps = $('#'+set["Code_Name"]).val();        
        settingsArray.push([set["Group"], set["Code_Name"], set["Type"], temps]);
      }
    });

    return settingsArray;
  }  

  // ---------------------------------------------------------
  function saveSettings() {
    if(<?php echo count($settings)?> != settingsNumber) 
    {
      showModalOk('WARNING', "<?= lang("settings_missing_block")?>");    
    } else
    {

      // trigger a save settings event in the backend
      $.ajax({
      method: "POST",
      url: "php/server/util.php",
      data: { 
        function: 'savesettings', 
        settings: JSON.stringify(collectSettings()) },
        success: function(data, textStatus) {                    
          
          showModalOk ('Result', data );
         
          // Remove navigation prompt "Are you sure you want to leave..."
          window.onbeforeunload = null;         

          // Reloads the current page
          setTimeout("window.location.reload()", 3000);
          
         
        }
      });
    }
  }

  
  // ---------------------------------------------------------  
  function getParam(targetId, key, skipCache = false) {  

    skipCacheQuery = "";

    if(skipCache)
    {
      skipCacheQuery = "&skipcache";
    }

    // get parameter value
    $.get('php/server/parameters.php?action=get&defaultValue=0&parameter='+ key + skipCacheQuery, function(data) {

      var result = data;   
      
      result = result.replaceAll('"', '');
      
      document.getElementById(targetId).innerHTML = result.replaceAll('"', ''); 
    });
  }

  // -----------------------------------------------------------------------------
  function handleLoadingDialog()
  {
    $.get('api/app_state.json?nocache=' + Date.now(), function(appState) {   

      fileModificationTime = <?php echo filemtime($confPath)*1000;?>;  

      console.log(appState["settingsImported"]*1000)
      importedMiliseconds = parseInt((appState["settingsImported"]*1000));

      humanReadable = (new Date(importedMiliseconds)).toLocaleString("en-UK", { timeZone: "<?php echo $timeZone?>" });

      console.log(humanReadable.replaceAll('"', ''))

      // check if displayed settings are outdated
      // if(fileModificationTime > importedMiliseconds)
      if(appState["showSpinner"] || fileModificationTime > importedMiliseconds)
      { 
        showSpinner("settings_old")

        setTimeout("handleLoadingDialog()", 1000);

      } else
      {
        hideSpinner()        
      }

      document.getElementById('lastImportedTime').innerHTML = humanReadable; 

     })

  }
  
  
  
  // -----------------------------------------------------------------------------
  function toggleAllSettings()
  {
    inStr = ' in';
    allOpen = true;
    openIcon = 'fa-angle-double-down';
    closeIcon = 'fa-angle-double-up';    

    $('.panel-collapse').each(function(){
      if($(this).attr('class').indexOf(inStr) == -1)
      {
        allOpen = false;
      }
    })
    
    if(allOpen)
    {
      // close all
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('class', 'panel-collapse collapse  ')})      
      $('#toggleSettings').attr('class', $('#toggleSettings').attr('class').replace(closeIcon, openIcon))
    }
    else{
      // open all
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('class', 'panel-collapse collapse in')})
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('style', 'height:inherit')})
      $('#toggleSettings').attr('class', $('#toggleSettings').attr('class').replace(openIcon, closeIcon))
    }
    
  }

  getData()

</script>

<script defer>

  // ----------------------------------------------------------------------------- 
  // handling events on the backend initiated by the front end START
  // ----------------------------------------------------------------------------- 
  function toggleMetadata(element)
  {
    const id = $(element).attr('my-to-toggle');

    $(`#${id}`).toggle();
  }


  // ----------------------------------------------------------------------------- 
  // handling events on the backend initiated by the front end START
  // ----------------------------------------------------------------------------- 

  modalEventStatusId = 'modal-message-front-event'

// --------------------------------------------------------
// Calls a backend function to add a front-end event (specified by the attributes 'data-myevent' and 'data-myparam-plugin' on the passed  element) to an execution queue
function addToExecutionQueue(element)
{

  // value has to be in format event|param. e.g. run|ARPSCAN
  action = `${getGuid()}|${$(element).attr('data-myevent')}|${$(element).attr('data-myparam-plugin')}`

  $.ajax({
    method: "POST",
    url: "php/server/util.php",
    data: { function: "addToExecutionQueue", action: action  },
    success: function(data, textStatus) {
        // showModalOk ('Result', data );

        // show message
        showModalOk(getString("general_event_title"), `${getString("general_event_description")}  <br/> <br/> <code id='${modalEventStatusId}'></code>`);

        updateModalState()
    }
  })
}

// --------------------------------------------------------
// Updating the execution queue in in modal pop-up
function updateModalState() {
    setTimeout(function() {
        // Fetch the content from the log file using an AJAX request
        $.ajax({
            url: '/log/execution_queue.log',
            type: 'GET',
            success: function(data) {
                // Update the content of the HTML element (e.g., a div with id 'logContent')
                $('#'+modalEventStatusId).html(data);

                updateModalState();
            },
            error: function() {
                // Handle error, such as the file not being found
                $('#logContent').html('Error: Log file not found.');
            }
        });
    }, 2000);
}


  // ----------------------------------------------------------------------------- 
  // handling events on the backend initiated by the front end END
  // ----------------------------------------------------------------------------- 

  // ---------------------------------------------------------
  // Show last time settings have been imported  

  handleLoadingDialog()

  

</script>
