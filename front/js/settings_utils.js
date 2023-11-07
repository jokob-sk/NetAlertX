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
                    <h5 class="card-title">
                      ${getString(prefix+"_display_name")}
                    </h5>
                    ${includeSettings_html}
                </div>
                <div class="icon"> ${getString(prefix+"_icon")} </div> 
                  
                </div>
              </div>
            `
    });

    return html;    
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