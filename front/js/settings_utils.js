// -------------------------------------------------------------------
// Get all plugin prefixes of a given type
function getPluginsByType(pluginsData, pluginType, onlyEnabled) {
  var result = [];

  pluginsData.forEach((plug) => {
    if (plug.plugin_type == pluginType) {
      // collect all, or if only enabled, check if NOT disabled
      if (
        onlyEnabled == false ||
        (onlyEnabled && getSetting(plug.unique_prefix + "_RUN") != "disabled")
      ) {
        result.push(plug.unique_prefix);
      }
    }
  });

  return result;
}

// -------------------------------------------------------------------
// Get plugin code name base on prefix
function getPluginCodeName(pluginsData, prefix) {
  var result = "";

  pluginsData.forEach((plug) => {
    if (plug.unique_prefix == prefix) {
      id = plug.code_name;

      // console.log(id)
      result = plug.code_name;
    }
  });

  return result;
}

// -------------------------------------------------------------------
// Get plugin type base on prefix
function getPluginType(pluginsData, prefix) {
  var result = "core";

  pluginsData.forEach((plug) => {
    if (plug.unique_prefix == prefix) {
      id = plug.plugin_type;

      // console.log(id)
      result = plug.plugin_type;
    }
  });

  return result;
}

// -------------------------------------------------------------------
// Get plugin config based on prefix
function getPluginConfig(pluginsData, prefix) {
  result = "";

  pluginsData.forEach((plug) => {
    if (plug.unique_prefix == prefix) {
      // console.log(id)
      result = plug;
    }
  });

  return result;
}

// -------------------------------------------------------------------
// Generate plugin HTML card based on prefixes in an array
function pluginCards(prefixesOfEnabledPlugins, includeSettings) {
  html = "";

  prefixesOfEnabledPlugins.forEach((prefix) => {
    includeSettings_html = "";

    includeSettings.forEach((set) => {
      includeSettings_html += `
            <div class="col-sm-6 overview-setting-value-wrap">
              <a href="#${prefix + "_" + set}" onclick="toggleAllSettings()">
                <div class="overview-setting-value  pointer" title="${
                  prefix + "_" + set
                }">
                  <code>${getSetting(prefix + "_" + set)}</code>
                </div> 
              </a>
            </div>
          `;
    });

    html += `            
              <div class="col-xs-6 col-sm-4 col-md-3 col-lg-2  col-xxl-1  padding-5px">
                <div class="small-box bg-green col-sm-12 " >
                  <div class="inner col-sm-12">
                    <a href="#${prefix}_header" onclick="toggleAllSettings('open')">
                      <h5 class="card-title">
                        <b>${getString(prefix + "_display_name")}</b>
                      </h5>
                    </a>
                    ${includeSettings_html}
                  </div>
                  <a href="#${prefix}_header" onclick="toggleAllSettings('open')">
                    <div class="icon"> ${getString(prefix + "_icon")} </div> 
                  </a>  
                </div>
                
              </div>
            `;
  });

  return html;
}

// -----------------------------------------------------------------------------
// Open or close all settings
// -----------------------------------------------------------------------------
function toggleAllSettings(openOrClose = "") {
  inStr = " in";
  allOpen = true;
  openIcon = "fa-angle-double-down";
  closeIcon = "fa-angle-double-up";

  $(".panel-collapse").each(function () {
    if ($(this).attr("class").indexOf(inStr) == -1) {
      allOpen = false;
    }
  });

  if (allOpen == false || openOrClose == "open") {
    // open all
    openAllSettings();
    $("#toggleSettings").attr(
      "class",
      $("#toggleSettings").attr("class").replace(openIcon, closeIcon)
    );
  } else {
    // close all
    $('div[data-myid="collapsible"]').each(function () {
      $(this).attr("class", "panel-collapse collapse  ");
    });
    $("#toggleSettings").attr(
      "class",
      $("#toggleSettings").attr("class").replace(closeIcon, openIcon)
    );
  }
}

function openAllSettings() {
  $('div[data-myid="collapsible"]').each(function () {
    $(this).attr("class", "panel-collapse collapse in");
  });
  $('div[data-myid="collapsible"]').each(function () {
    $(this).attr("style", "height:inherit");
  });
}

// -------------------------------------------------------------------
// Checks if all schedules are the same
function schedulesAreSynchronized(prefixesOfEnabledPlugins, pluginsData) {
  plug_schedules = [];

  prefixesOfEnabledPlugins.forEach((prefix) => {
    pluginsData.forEach((plug) => {
      if (plug.unique_prefix == prefix) {
        plug_schedules.push(
          getSetting(prefix + "_RUN_SCHD").replace(/\s/g, "")
        ); // replace all white characters to compare them easier
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
  const base64Regex =
    /^(?:[A-Za-z0-9+\/]{4})*?(?:[A-Za-z0-9+\/]{2}==|[A-Za-z0-9+\/]{3}=)?$/;
  return base64Regex.test(value);
}

// -------------------------------------------------------------------
// Validation
// -------------------------------------------------------------------
function settingsCollectedCorrectly(settingsArray, settingsJSON_DB) {
  // check if the required UI_LANG setting is in the array - if not something went wrong
  $.each(settingsArray, function (index, value) {
    if (value[1] == "UI_LANG") {
      if (isEmpty(value[3]) == true) {
        console.log(`⚠ Error: Required setting UI_LANG not found`);
        showModalOk("ERROR", getString("settings_missing_block"));

        return false;
      }
    }
  });

  const settingsCodeNames = settingsJSON_DB.map((setting) => setting.setKey);
  const detailedCodeNames = settingsArray.map((item) => item[1]);

  const missingCodeNamesOnPage = detailedCodeNames.filter(
    (setKey) => !settingsCodeNames.includes(setKey)
  );
  const missingCodeNamesInDB = settingsCodeNames.filter(
    (setKey) => !detailedCodeNames.includes(setKey)
  );

  // check if the number of settings on the page and in the DB are the same
  if (missingCodeNamesOnPage.length !== missingCodeNamesInDB.length) {
    console.log(
      `⚠ Error: The following settings are missing in the DB or on the page (Reload page to fix):`
    );
    console.log(missingCodeNamesOnPage);
    console.log(missingCodeNamesInDB);

    showModalOk("ERROR", getString("settings_missing_block"));

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
function addList(element, clearInput = true) {
  const fromId = $(element).attr("my-input-from");
  const toId = $(element).attr("my-input-to");

  const input = $(`#${fromId}`).val();

  console.log(`fromId | toId | input : ${fromId} | ${toId} | ${input}`);

  const newOption = $("<option class='interactable-option'></option>")
    .attr("value", input)
    .text(input);

  // add new option
  $(`#${toId}`).append(newOption);

  // clear input
  if (clearInput) {
    $(`#${fromId}`).val("");
  }

  // Initialize interaction options only for the newly added option
  initListInteractionOptions(newOption);

  // flag something changes to prevent navigating from page
  settingsChanged();
}

// ---------------------------------------------------------
function removeFromList(element) {
  settingsChanged();
  $(`#${$(element).attr("my-input-to")}`)
    .find("option:last")
    .remove();
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
function removeAllOptions(element) {
  settingsChanged();
  $(`#${$(element).attr("my-input-to")}`).empty();
}

// -------------------------------------------------------------------
// Add all options
function selectAll(element) {
  settingsChanged();

  // Get the <select> element with the class 'deviceSelector'
  // var selectElement = $('.deviceSelector select');
  var selectElement = $(`#${$(element).attr("my-input-to")}`);
  
  // Iterate over each option within the select element
  selectElement.find('option').each(function() {
    // Mark each option as selected
    $(this).prop('selected', true);
  });

  // Trigger the 'change' event to notify Bootstrap Select of the changes
  selectElement.trigger('change');
}

// -----------------------------------------------------------------------------
// UN-Select All
function unselectAll(element) {
  settingsChanged();
  // Get the <select> element with the class 'deviceSelector'
  // var selectElement = $('.deviceSelector select');
  var selectElement = $(`#${$(element).attr("my-input-to")}`);
  
  // Iterate over each option within the select element
  selectElement.find('option').each(function() {
    // Unselect each option
    $(this).prop('selected', false);
  });
  
  // Trigger the 'change' event to notify Bootstrap Select of the changes
  selectElement.trigger('change');
}

// -----------------------------------------------------------------------------
// Trigger change to open up the dropdown filed
function selectChange(element) {
  settingsChanged();
  // Get the <select> element with the class 'deviceSelector'
  // var selectElement = $('.deviceSelector select');
  var selectElement = $(`#${$(element).attr("my-input-to")}`);
  
  selectElement.parent().find("input").focus().click();
}

// -------------------------------------------------------------------
// Function to initialize remove functionality on select options

// Counter to track number of clicks
let clickCounter = 0;

// Function to initialize list interaction options
function initListInteractionOptions(element) {
  if (element) {
    $options = $(element);
  } else {
    $options = $(`.interactable-option`);
  }

  // Attach click event listener to options
  $options.on("click", function () {
    const $option = $(this);

    // Increment click counter
    clickCounter++;

    // Delay to capture multiple clicks
    setTimeout(() => {
      // Perform action based on click count
      if (clickCounter === 1) {
        // Single-click action
        showModalFieldInput(
          `<i class="fa-regular fa-pen-to-square"></i> ${getString(
            "Gen_Update_Value"
          )}`,
          getString("settings_update_item_warning"),
          getString("Gen_Cancel"),
          getString("Gen_Update"),
          $option.html(),
          function () {
            updateOptionItem($option, $(`#modal-field-input-field`).val());
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

  // open everything if input text is empty
  if (!inputText) {
    inputText = "";

    $(".panel").each(function () {
      var $panel = $(this);
      var $panelHeader = $panel.find('.panel-heading');
      var $panelBody = $panel.find('.panel-collapse');

      $panel.show() 
      $panelHeader.show() 
      $panelBody.collapse('show');

      $panelBody.find(".table_row:not(.docs)").each(function () {
        var $row = $(this)
        var rowId = $row.attr("id");
        var isMetadataRow = rowId && rowId.endsWith("__metadata");
        if (!isMetadataRow) {
          $row.show()
        }        
      });
      
    });
    
  } else{
    // filter

    $(".panel").each(function () {
      var $panel = $(this);
      var $panelHeader = $panel.find('.panel-heading');
      var $panelBody = $panel.find('.panel-collapse');
  
      var anyVisible = false; // Flag to check if any row is visible
  
      $panelBody.find(".table_row:not(.docs)").each(function () {
        var $row = $(this);
  
        // Check if the row ID ends with "__metadata"
        var rowId = $row.attr("id");
        var isMetadataRow = rowId && rowId.endsWith("__metadata");
  
        // Always hide metadata rows
        if (isMetadataRow) {
          $row.hide();
          return; // Skip further processing for metadata rows
        }
  
        var description = $row.find(".setting_description").text().toLowerCase();
        var setKey = $row.find(".setting_name code").text().toLowerCase();
  
        if (
          description.includes(inputText.toLowerCase()) ||
          setKey.includes(inputText.toLowerCase())
        ) {
          $row.show();
          anyVisible = true; // Set the flag to true if at least one row is visible
        } else {
          $row.hide();
        }
      });
  
      // Determine whether to hide or show the panel based on visibility of rows
      if (anyVisible) {
        $panelBody.collapse('show'); // Ensure the panel body is shown if there are visible rows
        $panelHeader.show(); // Show the panel header
        $panel.show(); // Show the entire panel if there are visible rows
      } else {
        $panelBody.collapse('hide'); // Hide the panel body if no rows are visible
        $panelHeader.hide(); // Hide the panel header if no rows are visible
        $panel.hide(); // Hide the entire panel if no rows are visible
      }
    });


  }

  
}


setTimeout(() => {
  // Event listener for input change
  $("#settingsSearch").on("input", function () {
    var searchText = $(this).val();
    // hide the setting overview dashboard
    $("#settingsOverview").collapse("hide");

    filterRows(searchText);
  });

  // Event listener for input focus
  // var firstFocus = true;
  $("#settingsSearch").on("focus", function () {
    openAllSettings();
  });
}, 1000);


// -----------------------------------------------------------------------------
// Show/hide the metadata settings
// -----------------------------------------------------------------------------
function toggleMetadata(element) {
  const id = $(element).attr("my-to-toggle");

  $(`#${id}`).toggle();
}

// -----------------------------------------------------------------------------
// Show setting description in a modal on smaller screens
// -----------------------------------------------------------------------------
function showDescription(element) {
  const id = $(element).attr("my-to-show");

  description = $(`${id}`)[0].innerHTML
  console.log(description);
  showModalOK(getString("Gen_Description"), description);
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
    console.warn(
      "Unsupported input type. Only text, password, and checkbox inputs are supported."
    );
  }
}



// Generate options or set options based on the provided parameters
function generateOptionsOrSetOptions(
  setKey,
  valuesArray, // Array of values to be pre-selected in the dropdown
  placeholder, // ID of the HTML element where dropdown should be rendered (will be replaced)
  processDataCallback, // Callback function to generate entries based on options
  targetField, // Target field or element where selected value should be applied or updated
  transformers = [] // Transformers to be applied to the values
) {

  // console.log(setKey);

  // NOTE {value} options to replace with a setting or SQL value are handled in the cacheSettings() function
  options = arrayToObject(createArray(getSettingOptions(setKey)))

  // Call to render lists
  renderList(
    options,
    processDataCallback,
    valuesArray,
    placeholder,
    targetField,
    transformers
  );
  
  
}


// ------------------------------------------------------------
// Function to apply transformers to a value
function applyTransformers(val, transformers) {
  transformers.forEach((transformer) => {
    switch (transformer) {
      case "sha256":
        // Implement sha256 hashing logic
        if (!isSHA256(val)) {
          val = CryptoJS.SHA256(val).toString(CryptoJS.enc.Hex);
        }
        break;
      case "base64":
        // Implement base64  logic
        if (!isBase64(val)) {
          val = btoa(val);
        }
        break;
      case "getString":
        // no change
        val = val;        
        break;
      default:
        console.warn(`Unknown transformer: ${transformer}`);
    }
  });
  return val;
}

// ------------------------------------------------------------
// Function to reverse transformers applied to a value
function reverseTransformers(val, transformers) {
  transformers.reverse().forEach((transformer) => {
    switch (transformer) {
      case "sha256":
        // Reversing sha256 is not possible since it's a one-way hash function
        console.warn("Reversing sha256 is not possible");
        break;
      case "base64":
        // Implement base64 decoding logic
        if (isBase64(val)) {
          val = atob(val);
        }
        break;
      case "getString":
        // retrieve string
        val = getString(val);        
        break;
      default:
        console.warn(`Unknown transformer: ${transformer}`);
    }
  });
  return val;
}


// ------------------------------------------------------------
// Function to initialize relevant variables based on HTML element
const handleElementOptions = (setKey, elementOptions, transformers, val) => {
  let inputType = "text";
  let readOnly = "";
  let isMultiSelect = false;
  let isOrdeable = false;
  let cssClasses = "";
  let placeholder = "";
  let suffix = "";
  let separator = "";
  let editable = false;
  let valRes = val;
  let sourceIds = [];
  let getStringKey = "";
  let onClick = "console.log('onClick - Not implemented');";
  let onChange = "console.log('onChange - Not implemented');";
  let customParams = "";
  let customId = "";


  elementOptions.forEach((option) => {
    if (option.prefillValue) {
      valRes = option.prefillValue === "null" ? "" : option.prefillValue;
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
    if (option.ordeable === "true") {
      isOrdeable = true;
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
      $.each(option.sourceSuffixes, function (index, suf) {
        sourceIds.push(setKey + suf);
      });
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
    if (option.onChange) {
      onChange = option.onChange;
    }
    if (option.customParams) {
      customParams = option.customParams;
    }
    if (option.customId) {
      customId = option.customId;
    }
  });

  if (transformers.includes("sha256")) {
    inputType = "password";
  }

  return {
    inputType,
    readOnly,
    isMultiSelect,
    isOrdeable,
    cssClasses,
    placeholder,
    suffix,
    sourceIds,
    separator,
    editable,
    valRes,
    getStringKey,
    onClick,
    onChange,
    customParams,
    customId
  };
};


// -----------------------------------------------------------------------------
// Data processors
// -----------------------------------------------------------------------------

// --------------------------------------------------
// Creates an object from an array 
function arrayToObject(array) {
  const obj = [];
  array.forEach((item, index) => {
    obj.push({ id: item, name: item })
  });
  return obj;
}

// -----------------------------------------------------------------------------
// Processor to generate options
function generateOptions(options, valuesArray, targetField, transformers, placeholder) {
  var optionsHtml = "";

  resultArray    = []
  selectedArray  = []
  cssClass       = ""
  

  // determine if options or values are used in the listing
  if (valuesArray.length > 0 && options.length > 0){

    // multiselect list ->  options only + selected the ones in valuesArray 
    resultArray   = options;
    selectedArray = valuesArray

  } else if (valuesArray.length > 0 && options.length == 0){

    // editable list -> values only     
    resultArray   = arrayToObject(valuesArray)
    cssClass = "interactable-option"  // generates [1x 📝 | 2x 🚮]
  } else if (options.length > 0){

    // dropdown -> options only (value == 1 STRING not ARRAY)
    resultArray   = options;
  }

 
  // Create a map to track the index of each item in valuesArray
  const orderMap = new Map(valuesArray.map((item, index) => [item, index]));

  // Sort resultArray based on the order in valuesArray
  resultArray.sort((a, b) => {
    const indexA = orderMap.has(a.id) ? orderMap.get(a.id) : valuesArray.length;
    const indexB = orderMap.has(b.id) ? orderMap.get(b.id) : valuesArray.length;
    return indexA - indexB;
  });

  resultArray.forEach(function(item) {
    let labelName = item.name;

    if (labelName !== '❌None') {
      labelName = reverseTransformers(labelName, transformers);
    }

    // Always include selected if options are used as a source
    let selected = options.length !== 0 && valuesArray.includes(item.id) ? 'selected' : '';

    optionsHtml += `<option class="${cssClass}" value="${item.id}" ${selected}>${labelName}</option>`;
  });


  // Place the resulting HTML into the specified placeholder div
  $("#" + placeholder).replaceWith(optionsHtml);
}


// -----------------------------------------------------------------------------
// Processor to generate a list
function generateList(options, valuesArray, targetField, transformers, placeholder) {
  var listHtml = "";
  options.forEach(function(item) {

    labelName = item.name

    if(labelName != '❌None')
    {
      labelName = reverseTransformers(labelName, transformers)
    }

    let selected = valuesArray.includes(item.id) ? 'selected' : '';

    listHtml += `<li ${selected}>${labelName}</li>`;
  });
  
  // Place the resulting HTML into the specified placeholder div
  $("#" + placeholder).replaceWith(listHtml);
}

// -----------------------------------------------------------------------------
// Processor to generate a list in the deviceDetails page
function genListWithInputSet(options, valuesArray, targetField, transformers, placeholder) {

  var listHtml = "";

  
  options.forEach(function(item) {

    let selected = valuesArray.includes(item.id) ? 'selected' : '';

    // console.log(item);

    labelName = item.name

    if(labelName != '❌None')
    {
      labelName = reverseTransformers(labelName, transformers)
      // console.log(transformers);
    }

    listHtml += `<li ${selected}>
                      <a href="javascript:void(0)" onclick="setTextValue('${targetField}','${item.id}')">${labelName}</a> 
                </li>`;
    
  });

  // Place the resulting HTML into the specified placeholder div
  $("#" + placeholder).replaceWith(listHtml);
}
