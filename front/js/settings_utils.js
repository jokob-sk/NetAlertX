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
  // Utility function to check if the value is already Base64
  function isBase64(value) {
    const base64Regex = /^(?:[A-Za-z0-9+\/]{4})*?(?:[A-Za-z0-9+\/]{2}==|[A-Za-z0-9+\/]{3}=)?$/;
    return base64Regex.test(value);
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
// Add item to list
function addList(element, clearInput = true)
{
  const fromId = $(element).attr('my-input-from');
  const toId = $(element).attr('my-input-to');  

  const input = $(`#${fromId}`).val();

  console.log(`fromId | toId | input : ${fromId} | ${toId} | ${input}`);

  const newOption = $("<option class='interactable-option'></option>").attr("value", input).text(input);
  
  const el = $(`#${toId}`).append(newOption);
  
  // clear input
  if (clearInput)
  {
    $(`#${fromId}`).val("");
  }

  // Initialize interaction options only for the newly added option
  initListInteractionOptions(newOption);
  
  settingsChanged();
}

// ---------------------------------------------------------
function removeFromList(element)
{
  settingsChanged();    
  $(`#${$(element).attr('my-input-to')}`).find("option:last").remove();
  
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
  $(`#${$(element).attr('my-input-to')}`).empty();
  
}

// -------------------------------------------------------------------
// Function to initialize remove functionality on select options 

// Counter to track number of clicks
let clickCounter = 0;

// Function to initialize list interaction options
function initListInteractionOptions(element) {
  if(element)
  {
    $options = $(element);
  } else
  {
    $options = $(`.interactable-option`);
  }

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
    function generateOptions(pluginsData, set, input, dataType, isMultiSelect = false, editable = false, transformers = []) {
      let multi           = isMultiSelect ? "multiple" : "";
      let valuesArray     = createArray(set['Value']);
      let settingKey      = set['Code_Name'];
      // editable ? classNames += " interactable-option" : classNames = ""
  
      //  generate different ID depending on if it's the source for the value to be saved or only used as an input
      // isValueSource ? id = settingKey : id = settingKey + '_input';

      // main selection dropdown wrapper
      input += `
        <select onChange="settingsChanged()" my-data-type="${dataType}"  my-editable="${editable}" class="form-control" name="${settingKey}" id="${settingKey}" ${multi}>          
      `;
    
      // if available transformers are applied
      valuesArray = valuesArray.map(value => applyTransformers(value, transformers));

      // get all options
      optionsArray = createArray(getSettingOptions(settingKey)) 

      // loop over all options and select the ones selected in the valuesArray (saved by the user)
      if(optionsArray.length > 0 )
      {
        //  check if needs to be processed ASYNC
        if(isSQLQuery(optionsArray[0]))
        {
          // create temporary placeholder
          targetLocation = settingKey + "_temp_"
          input += `<option value="" id="${targetLocation}" ></option>`; 

          //  callback to the DB
          readData(optionsArray[0], generateDropdownOptions, valuesArray, targetLocation, settingKey);
        } else // sync processing
        {
          optionsArray.forEach(option => {
            let selected = valuesArray.includes(option) ? 'selected' : '';
            input += `<option value="${option}" ${selected}>${option}</option>`;
          });  
        }
      } else // this is an interactable list with default and user-defined values
      {
        // generates [1x 📝 | 2x 🚮]
        valuesArray.forEach(option => {          
          input += `<option class="interactable-option" value="${option}">${option}</option>`;
        });  
      }
    
      input += `</select>`;
    
      // add values from the setting options - execute AJAX callback + SQL query resolution
      // initSettingDropdown(settingKey, valuesArray, targetLocation, generateDropdownOptions);

      return input;
    }

// ------------------------------------------------------------
// Function to apply transformers to a value
function applyTransformers(val, transformers) {
  transformers.forEach(transformer => {
    switch (transformer) {
      case 'sha256':
        // Implement sha256 hashing logic
        if (!isSHA256(val)) {
          val = CryptoJS.SHA256(val).toString(CryptoJS.enc.Hex);
        }
        break;
      case 'base64':
        // Implement base64  logic
        if (!isBase64(val)) {
          val = btoa(val);
        }        
        break;
      default:
        console.warn(`Unknown transformer: ${transformer}`);
    }
  });
  return val;
}



// ------------------------------------------------------------
// Function to initialize relevant variables based on HTML element
const handleElementOptions = (codeName, elementOptions, transformers, val) => {
  let inputType = 'text';
  let readOnly = "";
  let isMultiSelect = false;
  let cssClasses = '';
  let placeholder = '';
  let suffix = '';
  let separator = '';
  let editable = false;
  let valRes = val;
  let sourceIds = [];
  let getStringKey = "";
  let onClick  = "alert('Not implemented');";

  elementOptions.forEach(option => {
    if (option.prefillValue) {
      valRes = option.prefillValue === 'null' ? "" : option.prefillValue;
    }
    if (option.type) {
      inputType = option.type;
    }
    if (option.readonly === "true") {
      readOnly = `readonly`;
    }
    if (option.multiple === "true") {
      isMultiSelect = true;
    }
    if (option.editable === "true") {
      editable = true;
    }
    if (option.cssClasses) {
      cssClasses = option.cssClasses;
    }
    if (option.placeholder) {
      placeholder = option.placeholder;
    }
    if (option.suffix) {
      suffix = option.suffix;
    }
    if (option.sourceSuffixes) {
      $.each(option.sourceSuffixes, function(index, suf) {
        sourceIds.push(codeName + suf)
      })
    }
    if (option.separator) {
      separator = option.separator;
    }
    if (option.getStringKey) {
      getStringKey = option.getStringKey;
    }
    if (option.onClick) {
      onClick = option.onClick;
    }
  });

  if (transformers.includes('sha256')) {
    inputType = 'password';
  }

  return {
    inputType,
    readOnly,
    isMultiSelect,
    cssClasses,
    placeholder,
    suffix,
    sourceIds,
    separator,
    editable,
    valRes,
    getStringKey,
    onClick
  };
};

  
  
