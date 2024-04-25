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
  // Get plugin type base on prefix
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
  // Generate plugin HTML card based on prefixes in an array 
  function pluginCards(prefixesOfEnabledPlugins, includeSettings)
  {    
    html = ""

    prefixesOfEnabledPlugins.forEach((prefix) => {

      includeSettings_html = ''

      includeSettings.forEach((set) => {

        includeSettings_html += `
            <a href="#${prefix + '_' + set}" onclick="toggleAllSettings()">
              <div class="overview-setting-value  pointer" title="${prefix + '_' + set}">
                <code>${getSetting(prefix + '_' + set)}</code>
              </div> 
            </a>
          `

      });

      html += `            
              <div class="col-sm-4 ">
                <div class="small-box bg-green " >
                <div class="inner ">
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
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('class', 'panel-collapse collapse in')})
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('style', 'height:inherit')})
      $('#toggleSettings').attr('class', $('#toggleSettings').attr('class').replace(openIcon, closeIcon))
      
    }
    else{
      // close all
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('class', 'panel-collapse collapse  ')})      
      $('#toggleSettings').attr('class', $('#toggleSettings').attr('class').replace(closeIcon, openIcon))
    }
    
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
// Manipulating Editable List options
// -------------------------------------------------------------------


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













