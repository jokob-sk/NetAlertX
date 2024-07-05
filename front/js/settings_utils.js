// -------------------------------------------------------------------
  // Get all plugin prefixes of a given type 
  function getPluginsByType(pluginsData, pluginType, onlyEnabled)
  {

    var result = []

    pluginsData.forEach((plug) => {
      
      if(plug.plugin_type == pluginType)
      {
        // collect all, or if only enabled, check if NOT disabled 
        if (onlyEnabled == false || (onlyEnabled && getSetting(plug.unique_prefix + '_RUN') != 'disabled')) {
          result.push(plug.unique_prefix)         
        }
      }
    });

    return result;
  }

  // -------------------------------------------------------------------
  // Get plugin code name base on prefix
  function getPluginCodeName(pluginsData, prefix)
  {
    var result = ""

    pluginsData.forEach((plug) => {

      if (plug.unique_prefix == prefix ) {
        id = plug.code_name;
        
        // console.log(id)
        result = plug.code_name;        
      }
    });

    return result;
  }


  // -------------------------------------------------------------------
  // Get plugin type base on prefix
  function getPluginType(pluginsData, prefix)
  {
    var result = "core"

    pluginsData.forEach((plug) => {

      if (plug.unique_prefix == prefix ) {
        id = plug.plugin_type;
        
        // console.log(id)
        result = plug.plugin_type;        
      }
    });

    return result;
  }

  // -------------------------------------------------------------------
  // Get plugin config based on prefix
  function getPluginConfig(pluginsData, prefix)
  {

    result = ""

    pluginsData.forEach((plug) => {

      if (plug.unique_prefix == prefix ) {
        
        // console.log(id)
        result = plug;        
      }
    });

    return result;
  }

  // -------------------------------------------------------------------
  // Generate plugin HTML card based on prefixes in an array 
  function pluginCards(prefixesOfEnabledPlugins, includeSettings)
  {    
    html = ""

    prefixesOfEnabledPlugins.forEach((prefix) => {

      includeSettings_html = ''

      includeSettings.forEach((set) => {

        includeSettings_html += `
            <div class="col-sm-6 overview-setting-value-wrap">
              <a href="#${prefix + '_' + set}" onclick="toggleAllSettings()">
                <div class="overview-setting-value  pointer" title="${prefix + '_' + set}">
                  <code>${getSetting(prefix + '_' + set)}</code>
                </div> 
              </a>
            </div>
          `
      });

      html += `            
              <div class="col-xs-6 col-sm-4 col-md-3 col-lg-2  col-xxl-1  padding-5px">
                <div class="small-box bg-green col-sm-12 " >
                  <div class="inner col-sm-12">
                    <a href="#${prefix}_header" onclick="toggleAllSettings('open')">
                      <h5 class="card-title">
                        <b>${getString(prefix+"_display_name")}</b>
                      </h5>
                    </a>
                    ${includeSettings_html}
                  </div>
                  <a href="#${prefix}_header" onclick="toggleAllSettings('open')">
                    <div class="icon"> ${getString(prefix+"_icon")} </div> 
                  </a>  
                </div>
                
              </div>
            `
    });

    return html;    
  }


  // -----------------------------------------------------------------------------
  // Open or close all settings
  // -----------------------------------------------------------------------------
  function toggleAllSettings(openOrClose = '')
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
    
    if(allOpen == false || openOrClose == 'open')
    {
      // open all
      openAllSettings()
      $('#toggleSettings').attr('class', $('#toggleSettings').attr('class').replace(openIcon, closeIcon))
      
    }
    else{
      // close all
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('class', 'panel-collapse collapse  ')})      
      $('#toggleSettings').attr('class', $('#toggleSettings').attr('class').replace(closeIcon, openIcon))
    }
    
  }

  function openAllSettings() {
    $('div[data-myid="collapsible"]').each(function(){$(this).attr('class', 'panel-collapse collapse in')})
    $('div[data-myid="collapsible"]').each(function(){$(this).attr('style', 'height:inherit')})
  }


  // -------------------------------------------------------------------
  // Checks if all schedules are the same
  function schedulesAreSynchronized(prefixesOfEnabledPlugins, pluginsData)
  {    
    plug_schedules = []    

    prefixesOfEnabledPlugins.forEach((prefix) => {
      pluginsData.forEach((plug) => {

        if (plug.unique_prefix == prefix) {
          
          plug_schedules.push(getSetting(prefix+"_RUN_SCHD").replace(/\s/g, "")) // replace all white characters to compare them easier

        }

      });
    });

    // Check if all plug_schedules are the same
    if (plug_schedules.length > 0) {
      const firstSchedule = plug_schedules[0];
      return plug_schedules.every((schedule) => schedule === firstSchedule);
    }

    return true; // Return true if no schedules are found
  }

  // -------------------------------------------------------------------
  // Checks if value is already encoded
  function isSHA256(value) {
    // Check if the value is a string and has a length of 64 characters
    if (typeof value === "string" && value.length === 64) {
        // Check if the value contains only hexadecimal characters
        return /^[0-9a-fA-F]+$/.test(value);
    } else {
        return false;
    }
  }

// -------------------------------------------------------------------
// Validation
// -------------------------------------------------------------------
function settingsCollectedCorrectly(settingsArray, settingsJSON_DB) {

  // check if the required UI_LANG setting is in the array - if not something went wrong
  $.each(settingsArray, function(index, value) {
      if (value[1] == "UI_LANG") {
        if(isEmpty(value[3]) == true)
        {
          console.log(`⚠ Error: Required setting UI_LANG not found`);
          showModalOk('ERROR', getString('settings_missing_block')); 

          return false;
        }
      }
  });

  const settingsCodeNames = settingsJSON_DB.map(setting => setting.Code_Name);
  const detailedCodeNames = settingsArray.map(item => item[1]);

  const missingCodeNamesOnPage = detailedCodeNames.filter(codeName => !settingsCodeNames.includes(codeName));
  const missingCodeNamesInDB = settingsCodeNames.filter(codeName => !detailedCodeNames.includes(codeName));

  // check if the number of settings on the page and in the DB are the same
  if (missingCodeNamesOnPage.length !== missingCodeNamesInDB.length) {

      console.log(`⚠ Error: The following settings are missing in the DB or on the page (Reload page to fix):`);
      console.log(missingCodeNamesOnPage);
      console.log(missingCodeNamesInDB);

      showModalOk('ERROR', getString('settings_missing_block')); 

      return false;
  } 

  //  all OK
  return true;
}
// -------------------------------------------------------------------
// Manipulating Editable List options
// -------------------------------------------------------------------

// ---------------------------------------------------------
function addList(element, clearInput = true)
{

  const fromId = $(element).attr('my-input-from');
  const toId = $(element).attr('my-input-to');

  

  input = $(`#${fromId}`).val();

  console.log(input);
  console.log(toId);
  console.log($(`#${toId}`));

  $(`#${toId}`).append($("<option ></option>").attr("value", input).text(input));
  
  // clear input
  if (clearInput)
  {
    $(`#${fromId}`).val("");
  }
  
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


// -------------------------------------------------------------------
// Function to remove an item from the select element
function removeOptionItem(option) {
  settingsChanged();  
  option.remove();
}

// -------------------------------------------------------------------
// Update value of an item from the select element
 function updateOptionItem(option, value) {
  settingsChanged();  
  option.html(value);
  option.val(value);
}

// -------------------------------------------------------------------
// Remove all options
function removeAllOptions(element)
{
  settingsChanged();    
  $(`#${$(element).attr('my-input')}`).empty();
  
}

// -------------------------------------------------------------------
// Function to initialize remove functionality on select options 

// Counter to track number of clicks
let clickCounter = 0;

// Function to initialize list interaction options
function initListInteractionOptions(selectorId) {
  // Select all options within the specified selector
  const $options = $(`#${selectorId} option`);

  // Add class to make options interactable
  $options.addClass('interactable-option');

  // Attach click event listener to options
  $options.on('click', function() {
    const $option = $(this);

    // Increment click counter
    clickCounter++;

    // Delay to capture multiple clicks
    setTimeout(() => {
      // Perform action based on click count
      if (clickCounter === 1) {
        // Single-click action
        // btoa(iconHtml.replace(/"/g, "'")   <-- encode
        // atob()    <--- decode
        showModalFieldInput(
          `<i class="fa-regular fa-pen-to-square"></i> ${getString('Gen_Update_Value')}`,
          getString('settings_update_item_warning'),
          getString('Gen_Cancel'),
          getString('Gen_Update'),
          $option.html(),
          function() {
            updateOptionItem($option, $(`#modal-field-input-field`).val())
          }
        );
      } else if (clickCounter === 2) {
        // Double-click action
        removeOptionItem($option);
      }

      // Reset click counter
      clickCounter = 0;
    }, 300); // Adjust delay as needed
  });
}


// -------------------------------------------------------------------
// Function to filter rows based on input text
function filterRows(inputText) {

  if(!inputText)
  {
    inputText = ''
  }

  $('.table_row').each(function() {
    // Check if the row id ends with '__metadata'
    var idAttribute = $(this).attr('id');
    if (idAttribute && idAttribute.endsWith('__metadata')) {
      $(this).hide(); // Hide the row if it ends with '__metadata'
      return; // Skip to the next iteration
    }

    var description = $(this).find('.setting_description').text().toLowerCase();
    var codeName = $(this).find('.setting_name code').text().toLowerCase();
    if (description.includes(inputText.toLowerCase()) || codeName.includes(inputText.toLowerCase())) {
      $(this).show(); // Show the row if it matches the input text
    } else {
      $(this).hide(); // Hide the row if it doesn't match the input text
    }
  });
}

  setTimeout(() => {

    // Event listener for input change
    $('#settingsSearch').on('input', function() {
      var searchText = $(this).val();
      // hide the setting overview dashboard
      $('#settingsOverview').collapse('hide');

      filterRows(searchText);
    });

    // Event listener for input focus
    // var firstFocus = true;
    $('#settingsSearch').on('focus', function() {
      openAllSettings()
    });

    
    
  }, 1000);



  // ----------------------------------------------------------------------------- 
  // handling events on the backend initiated by the front end END
  // ----------------------------------------------------------------------------- 


// ---------------------------------------------------------  
// UNUSED?
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
  // Show/hide the metadata settings
  // ----------------------------------------------------------------------------- 
  function toggleMetadata(element)
  {
    const id = $(element).attr('my-to-toggle');

    $(`#${id}`).toggle();
  }



  // ---------------------------------------------------------  
  // Helper methods
  // ---------------------------------------------------------  
  // Toggle readonly mode of the target element specified by the id in the "my-input-toggle-readonly" attribute
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
  // generate a list of options for a input select
  function generateOptions(pluginsData, set, input, isMultiSelect = false, isValueSource = true)
  {
    multi = isMultiSelect ? "multiple" : "";

    // optionsArray = getSettingOptions(set['Code_Name'] )
    valuesArray = createArray(set['Value']);  


    // create unique ID  
    var targetLocation = set['Code_Name'] + "_initSettingDropdown";  

    // execute AJAX callabck + SQL query resolution
    initSettingDropdown(set['Code_Name'] , valuesArray,  targetLocation, generateDropdownOptions); 

    //  generate different ID depending on if it's the source for the value to be saved or only used as an input
    isValueSource ? id = set['Code_Name'] : id = set['Code_Name'] + '_input';
    
    // main selection dropdown wrapper
    input += `
      <select onChange="settingsChanged()"  
              my-data-type="${set['Type']}" 
              class="form-control" 
              name="${set['Code_Name']}" 
              id="${id}" 
              ${multi}>

            <option id="${targetLocation}" temporary="temporary"></option>
    
      </select>`;
      
    return input;
  }

  
