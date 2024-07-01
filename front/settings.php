<?php

require 'php/templates/header.php';

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
// Set maximum execution time to 15 seconds
ini_set ('max_execution_time','30');

// check permissions
$dbPath = "../db/app.db";
$confPath = "../config/app.conf";

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

$settingsJSON_DB = json_encode($settings, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);

?>
<!-- Page ------------------------------------------------------------------ -->
<!-- Page ------------------------------------------------------------------ -->

<script src="js/settings_utils.js?v=<?php include 'php/templates/version.php'; ?>"></script>

<script src="lib/crypto/crypto-js.min.js"></script>


<div id="settingsPage" class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">

      <div class="col-sm-5">
        <h1 id="pageTitle col-sm-3">
            <i class="fa fa-cog"></i>
            <?= lang('Navigation_Settings');?> 
            <a style="cursor:pointer">
              <span>
                <i id='toggleSettings' onclick="toggleAllSettings()" class="settings-expand-icon fa fa-angle-double-down"></i>
              </span> 
            </a>
        </h1>
      </div>

      <div class="col-sm-7 settingsImportedTimestamp" title="<?= lang("settings_imported");?> ">
        <div class="settingsImported ">
          <?= lang("settings_imported_label");?>:          

          <span id="lastImportedTime"></span>
        </div>    
      </div>

    </section>
    <section class="content-header">

    <div  class ="bg-white color-palette box box-solid box-primary  col-sm-12  panel panel-default panel-title" > 
      <!-- Settings imported time -->

      
      <a data-toggle="collapse" href="#settingsOverview">
        <div class ="settings-group col-sm-12 panel-heading panel-title">
            <i class="<?= lang("settings_enabled_icon");?>"></i>  <?= lang("settings_enabled");?>  
        </div>     
      </a>  
        <div id="settingsOverview" class="panel-collapse collapse in"> 
          <div class="panel-body"></div>
        <div class =" col-sm-12 " id=""></div>
      </div>
    </section>

    <div class="content settingswrap " id="accordion_gen">

      <div class ="bg-grey-dark color-palette panel panel-default col-sm-12  box-default box-info" id="core_content_header" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_core_icon");?>"></i>  <?= lang("settings_core_label");?>       
          </div>        
          <div class =" col-sm-12" id="core_content"></div>
      </div>    

      <div class ="bg-grey-dark color-palette panel panel-default col-sm-12   box-default box-info" id="system_content_header" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_system_icon");?>"></i>  <?= lang("settings_system_label");?>       
          </div>        
          <div class =" col-sm-12" id="system_content"></div>
      </div> 

      <div class ="bg-grey-dark color-palette  panel panel-default col-sm-12   box-default box-info" id="device_scanner_content_header" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_device_scanners_icon");?>"></i>  <?= lang("settings_device_scanners_label");?>     
          </div>        
          <div class =" col-sm-12" id="device_scanner_content"> <?= lang("settings_device_scanners_info");?> </div>
      </div> 

      <div class ="bg-grey-dark color-palette  panel panel-default col-sm-12   box-default box-info" id="other_content_header">        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_other_scanners_icon");?>"></i>  <?= lang("settings_other_scanners_label");?>       
          </div>        
          <div class =" col-sm-12" id="other_content"></div>
      </div> 

      <div class ="bg-grey-dark color-palette  panel panel-default col-sm-12   box-default box-info" id="publisher_content_header" >        
          <div class ="settings-group col-sm-12">
            <i class="<?= lang("settings_publishers_icon");?>"></i>  <?= lang("settings_publishers_label");?>       
          </div>        
          <div class =" col-sm-12" id="publisher_content"><?= lang("settings_publishers_info");?></div>
      </div> 
     
   </div>
   
    <!-- /.content -->

    <section class=" padding-bottom  col-sm-12">
      <!-- needed so the filter & save button don't hide the settings -->
    </section>


      <section class=" settings-sticky-bottom-section  col-sm-10 col-xs-12">
        <div class="col-xs-8 settingsSearchWrap form-group has-success bg-white color-palette ">
          <div class ="col-xs-8">
            <i class="fa-solid fa-filter"></i> <?= lang("Gen_Filter");?>  
          </div>
            <div class ="col-xs-12">

              <input type="text" id="settingsSearch" class="form-control input-xs col-xs-12" placeholder="Filter Settings...">
              <div class="clear-filter ">
                <i class="fa-solid fa-circle-xmark" onclick="$('#settingsSearch').val('');filterRows();$('#settingsSearch').focus()"></i>
              </div>            
          </div>          
        </div>

        <div class="col-xs-4 saveSettingsWrapper">
            <button type="button" class="   btn btn-primary btn-default pa-btn bg-green" id="save" onclick="saveSettings()"><?= lang('DevDetail_button_Save');?></button>
        </div>
        <div id="result"></div>
    </section>
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
        
        // Wrong number of settings processing
        if(settingsNumberDB != settingsData.length) 
        {
          showModalOk('WARNING', "<?= lang("settings_old")?>");    
          setTimeout(() => {
                  clearCache()
                }, 3000);
        } else
        {
          $.get('api/plugins.json?nocache=' + Date.now(), function(res) {  

            pluginsData = res["data"];  

            // Sort settingsData alphabetically based on the "Group" property
            settingsData.sort((a, b) => {
                if (a["Group"] < b["Group"]) {
                    return -1;
                }
                if (a["Group"] > b["Group"]) {
                    return 1;
                }
                return 0;
            });

            exception_occurred = false;

            // check if cache needs to be refreshed
            // the getSetting method returns an empty string even if a setting is not found
            // however, __metadata needs to be always a JSON object
            // let's use that to verify settings were initialized correctly
            settingsData.forEach((set) => {

              codeName = set['Code_Name']

              try {                
                const isMetadata = codeName.includes('__metadata');
                // is this isn't a metadata entry, get corresponding metadata object from the dummy setting
                const setObj = isMetadata ? {} : JSON.parse(getSetting(`${codeName}__metadata`));
                
              } catch (error) {
                console.error(`Error getting setting for ${codeName}:`, error);
                showModalOk('WARNING', "Outdated cache - refreshing (refresh browser cache if needed)");  

                setTimeout(() => {
                  clearCache()
                }, 3000);

                exception_occurred = true;                
              }
            });
  
            // only proceed if everything was loaded correctly
            if(!exception_occurred)
            {
              initSettingsPage(settingsData, pluginsData, generateDropdownOptions);
            }
          })
        }        
    })
  }

  // -------------------------------------------------------------------
  // main initialization function
  function initSettingsPage(settingsData, pluginsData){

    const settingPluginPrefixes = [];
    const settingKeyOfLists = [];
    
    const enabledDeviceScanners = getPluginsByType(pluginsData, "device_scanner", true);    
    const enabledOthers         = getPluginsByType(pluginsData, "other", true);    
    const enabledPublishers     = getPluginsByType(pluginsData, "publisher", true);


    // Loop through the settingsArray and:
    //    - collect unique settingPluginPrefixes
    //    - collect enabled plugins

    settingsData.forEach((set) => {
      // settingPluginPrefixes
      if (!settingPluginPrefixes.includes(set.Group)) {
        settingPluginPrefixes.push(set.Group); // = Unique plugin prefix
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
                                    <div class="overview-group col-sm-12 col-xs-12">
                                    
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

    $('#settingsOverview .panel-body').append(overviewSections_html);

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

    for (const prefix of settingPluginPrefixes) {   

      // enabled / disabled icons
      enabledHtml = ''

      if(getSetting(prefix+"_RUN") != "")
      {
        // show all enabled plugins
        getSetting(prefix+"_RUN") != 'disabled' ? onOff = 'dot-circle' : onOff = 'circle';

        enabledHtml = `
                      <div class="enabled-disabled-icon">
                        <i class="fa-regular fa-${onOff}"></i>
                      </div>
                      `
      }      

      // console.log(pluginsData);

      // Start constructing the main settings HTML 
      let pluginHtml = `
        <div class="row table_row">
          <div class="table_cell bold">
            <i class="fa-regular fa-book fa-sm"></i>
            ${getString(prefix+'_description')} 
            <a href="https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/${getPluginCodeName(pluginsData, prefix)}" target="_blank">
            ${getString('Gen_ReadDocs')}
            </a>
          </div>
        </div>
      `;

      // Plugin HEADER
      headerHtml = `<div class="box box-solid box-primary panel panel-default" id="${prefix}_header">
                  <a data-toggle="collapse" data-parent="#accordion_gen" href="#${prefix}">
                    <div class="panel-heading">
                      <h4 class="panel-title">
                        <div class="col-sm-1 col-xs-1">${getString(prefix+"_icon")}   </div>
                        <div class="col-sm-10 col-xs-8">${getString(prefix+"_display_name")} </div>     
                        <div class="col-sm-1 col-xs-1">${enabledHtml} </div>
                      </h4>                      
                    </div>
                  </a>
                  <div id="${prefix}" data-myid="collapsible" class="panel-collapse collapse ${prefix == "General" ? ' in ' : ""}">
                    <div class="panel-body">
                    ${prefix != "General" ? pluginHtml: ""}                    
                    </div>
                  </div>
                </div>
                    `;

      // generate headers/sections      
      $('#'+getPluginType(pluginsData, prefix) + "_content").append(headerHtml);
    }  


    // generate panel content
    for (const prefix of settingPluginPrefixes) {

      // go thru all settings and collect settings per settings prefix 
      settingsData.forEach((set) => {

        let val = set['Value'];
        const codeName = set['Code_Name'];
        const setType = set['Type'].toLowerCase();
        const isMetadata = codeName.includes('__metadata');
        // is this isn't a metadata entry, get corresponding metadata object from the dummy setting
        const setObj = isMetadata ? {} : JSON.parse(getSetting(`${codeName}__metadata`));

        // not initialized properly, reload
        if(isMetadata && val == "" )
        {
          console.warn(`Metadata setting value is empty: ${codeName}`);
          clearCache();
        }

        // constructing final HTML for the setting
        setHtml = ""

        if(set["Group"] == prefix)
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
                        <div class="small text-overflow-hidden">
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
            console.log(prefix)
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
            // --- process text ---
            if(setType.includes(".select"))
            {
              inputHtml = generateInputOptions(pluginsData, set, inputHtml, isMultiSelect = false)

            } else if(setType.includes(".multiselect"))
            {
              inputHtml = generateInputOptions(pluginsData, set, inputHtml, isMultiSelect = true)
            } else{

              // if it's overridable set readonly accordingly
              if(overridable)
              {
                override ? readonly = "" : readonly = " readonly" ; 
              }

              inputHtml = `<input class="form-control" onChange="settingsChanged()"  my-data-type="${setType}"  id="${codeName}" value="${val}" ${readonly}/>`;
            }            
          } else if (setType === 'integer') {
            // --- process integer ---
            inputHtml = `<input onChange="settingsChanged()"  my-data-type="${setType}" class="form-control" id="${codeName}" type="number" value="${val}"/>`;
          } else if (setType.startsWith('password')) {
            // --- process password ---
            inputHtml = `<input onChange="settingsChanged()"  my-data-type="${setType}"  class="form-control input" id="${codeName}" type="password" value="${val}"/>`;
          } else if (setType === 'readonly') {
            // --- process readonly ---
            inputHtml = `<input class="form-control input"  my-data-type="${setType}"  id="${codeName}"  value="${val}" readonly/>`;
          } else if (setType === 'boolean' || setType === 'integer.checkbox') {
            // --- process boolean ---
            let checked = val === 'True' || val === '1' ? 'checked' : '';                   

            // if it's overridable set readonly accordingly
            if(overridable)
            {
              override ? disabled = "" : disabled = " disabled" ;
            }             

            inputHtml = `<input onChange="settingsChanged()" my-data-type="${setType}" class="checkbox" id="${codeName}" type="checkbox" value="${val}" ${checked} ${disabled}/>`;          
          } else if (setType === 'integer.select') {

            inputHtml = generateInputOptions(pluginsData, set, inputHtml)
          
          } else if (setType === 'subnets') {
            // --- process subnets ---
            inputHtml = `
            <div class="row form-group">
              <div class="col-xs-5">
                <input class="form-control"  id="ipMask" type="text" placeholder="192.168.1.0/24"/>
              </div>
              <div class="col-xs-4">
                <input class="form-control" id="ipInterface" type="text" placeholder="eth0" />
              </div>
              <div class="col-xs-3">
                <button class="btn btn-primary" onclick="addInterface();initListInteractionOptions('${codeName}')">${getString("Gen_Add")}</button>
              </div>
            </div>
            <div class="form-group">
              <select class="form-control" my-data-type="${setType}" name="${codeName}" id="${codeName}" onchange="initListInteractionOptions(${codeName})" multiple readonly>`;


            saved_values = createArray(val);

            saved_values.forEach(saved_val => {
              inputHtml += `<option value="${saved_val}" >${saved_val}</option>`;
            });

            inputHtml += `</select>
                        </div>
                        <div class="col-xs-12">
                          <button class="btn btn-primary" my-input="${codeName}" onclick="removeFromList(this)">
                            ${getString("Gen_Remove_Last")}
                          </button>     
                          <button class="btn btn-primary" my-input="${codeName}" onclick="removeAllOptions(this)">
                            ${getString("Gen_Remove_All")}
                          </button>                              
                        </div>`;
          } else if (setType === 'list' || setType === 'list.select' || setType === 'list.readonly') {
            // --- process list ---

            settingKeyOfLists.push(codeName);

            inputHtml += `
              <div class="row form-group">
                <div class="col-xs-9">`

            if(setType.includes(".select")) // not tested
            {
              inputHtml += generateInputOptions(pluginsData, set, inputHtml, isMultiSelect = false)
            }
            else
            {
              inputHtml += `
                  <input class="form-control" type="text" id="${codeName}_input" placeholder="Enter value"/>
                `;
            }

            inputHtml += `</div>
                <div class="col-xs-3">
                  <button class="btn btn-primary" my-input-from="${codeName}_input" my-input-to="${codeName}" onclick="addList(this);initListInteractionOptions('${codeName}')">${getString("Gen_Add")}</button>
                </div>
              </div>
              <div class="form-group">
                <select class="form-control" my-data-type="${setType}" name="${codeName}" id="${codeName}" multiple readonly>`;           

            let saved_values = createArray(val);

            saved_values.forEach(saved_val => {

              inputHtml += `<option value="${saved_val}" >${saved_val}</option>`;
            });

            inputHtml += '</select></div>' +
            `<div>
                <button class="btn btn-primary" my-input="${codeName}" onclick="removeFromList(this)">
                  ${getString("Gen_Remove_Last")}
                </button>     
                <button class="btn btn-primary" my-input="${codeName}" onclick="removeAllOptions(this)">
                  ${getString("Gen_Remove_All")}
                </button>                          
            </div>`;
          } else if (setType === 'json') {
            // --- process json ---
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
                data-myparam-plugin="${prefix}"
                data-myevent="${event}"
                onclick="addToExecutionQueue_settingEvent(this)"
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

          // generate settings in the correct prefix (group) section
          $(`#${prefix} .panel-body`).append(setHtml);

          // init remove and edit listitem click gestures
          if(['subnets', 'list' ].includes(setType))
          {
            initListInteractionOptions(codeName)
          }
          
        }
      });

    }

    // init finished
    
    setupSmoothScrolling()
    hideSpinner()

  }



  // display the name of the first person
  // echo $settingsJson[0]->name;
  var settingsNumberDB = <?php echo count($settings)?>;
  var settingsJSON_DB  = <?php echo $settingsJSON_DB  ?>;
  var settingsNumberJSON = <?php echo count($settingsJson->data)?>;

  // Wrong number of settings processing
  if(settingsNumberJSON != settingsNumberDB) 
  {
    showModalOk('WARNING', getString("settings_missing"));    
  }

  // ---------------------------------------------------------
  function saveSettings() {
    if(settingsNumberJSON != settingsNumberDB) 
    {
      console.log(`Error settingsNumberJSON != settingsNumberDB: ${settingsNumberJSON} !=  ${settingsNumberDB}`);

      showModalOk('WARNING', getString("settings_missing_block")); 

      setTimeout(() => {
              clearCache()  
            }, 1500);
         
    } else
    {
      var settingsArray = [];

      // collect values for each of the different input form controls
      const noConversion = ['text', 'integer', 'string', 'password', 'readonly', 'text.select', 'list.select', 'integer.select', 'text.multiselect'];

      // get settings to determine setting type to store values appropriately
      $.get('api/table_settings.json?nocache=' + Date.now(), function(res) { 
      
        settingsJSON = res;
            
        data = settingsJSON["data"];     

        data.forEach(set => {
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
          } else if (set['Type'] === 'password.SHA256') { 
            // save value as SHA256 if value isn't SHA256 already       
            var temps = $('#'+set["Code_Name"]).val(); 
            
            if(temps != "" && !isSHA256(temps))
            {
              temps = CryptoJS.SHA256(temps).toString(CryptoJS.enc.Hex);
            } 
            settingsArray.push([set["Group"], set["Code_Name"], set["Type"], temps]);
          }
        });

        // sanity check to make sure settings were loaded & collected correctly
        if(settingsCollectedCorrectly(settingsArray, settingsJSON_DB))
        {
          // trigger a save settings event in the backend
          $.ajax({
          method: "POST",
          url: "php/server/util.php",
          data: { 
            function: 'savesettings', 
            settings: JSON.stringify(settingsArray) },
            success: function(data, textStatus) {                    
              
              if(data == "OK")
              {
                showMessage (getString("settings_saved"), 5000, "modal_grey");
                // Remove navigation prompt "Are you sure you want to leave..."
                window.onbeforeunload = null;         

                // Reloads the current page
                setTimeout("clearCache()", 5000);    
              } else{
                // something went wrong
                // write_notification(data, 'interrupt')
                write_notification("Please screenshot the next popup (or check Monitoring > Notifications), dev console (F12) and submit it as a new issue here: https://github.com/jokob-sk/NetAlertX/issues", 'interrupt')
                console.log(settingsArray);
                console.log(JSON.stringify(settingsArray));
                write_notification(JSON.stringify(settingsArray), 'interrupt')
              }
            }
          });
        } 
        
      })

    }
  }



</script>


<!-- INIT THE PAGE -->
<script defer>

function handleLoadingDialog()
  {

    // check if config file has been updated
    $.get('api/app_state.json?nocache=' + Date.now(), function(appState) {   

      fileModificationTime = <?php echo filemtime($confPath)*1000;?>;  

      // console.log(appState["settingsImported"]*1000)
      importedMiliseconds = parseInt((appState["settingsImported"]*1000));

      humanReadable = (new Date(importedMiliseconds)).toLocaleString("en-UK", { timeZone: "<?php echo $timeZone?>" });

      // console.log(humanReadable.replaceAll('"', ''))

      // check if displayed settings are outdated
      
      if(appState["showSpinner"] || fileModificationTime > importedMiliseconds)
      { 
  
        showSpinner("settings_old")

        setTimeout("handleLoadingDialog()", 1000);

      } else
      {
        // check if the app is initialized and hide the spinner
        if(isAppInitialized())
        {          
          // init page
          getData()
          
          // reload page if outdated information might be displayed
          if(secondsSincePageLoad() > 3)
          {
            clearCache()
          }
        } 
        else
        {
          // reload the page if not initialized to give time the background tasks to finish 
          setTimeout(() => {

            window.location.reload()
            
          }, 3000);
        }     
      }

      document.getElementById('lastImportedTime').innerHTML = humanReadable; 
     })

  }
  

  showSpinner()
  handleLoadingDialog()



</script>
