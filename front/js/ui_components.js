/* -----------------------------------------------------------------------------
*  NetAlertX
*  Open Source Network Guard / WIFI & LAN intrusion detector 
*
*  ui_components.js - Front module. Common UI components
*-------------------------------------------------------------------------------
#  jokob             jokob@duck.com                GNU GPLv3
----------------------------------------------------------------------------- */


// -----------------------------------------------------------------------------
// Initialize device selectors / pickers fields
// -----------------------------------------------------------------------------
function initDeviceSelectors() {

  console.log(devicesList)
  // Retrieve device list from session variable
  var devicesListAll_JSON = getCache('devicesListAll_JSON');

  var devicesList = JSON.parse(devicesListAll_JSON);

  console.log(devicesList);


  // Check if both device list exists
  if (devicesListAll_JSON) {
      // Parse the JSON string to get the device list array
      var devicesList = JSON.parse(devicesListAll_JSON);

      var selectorFieldsHTML = ''

      // Loop through the devices list
      devicesList.forEach(function(device) {         

          selectorFieldsHTML += `<option value="${device.dev_MAC}">${device.dev_Name}</option>`;
      });

      selector = `<div class="db_info_table_row  col-sm-12" > 
                    <div class="form-group" > 
                      <div class="input-group col-sm-12 " > 
                        <select class="form-control select2 select2-hidden-accessible" multiple=""  style="width: 100%;"  tabindex="-1" aria-hidden="true">
                        ${selectorFieldsHTML}
                        </select>
                      </div>
                    </div>
                  </div>`


      // Find HTML elements with class "deviceSelector" and append selector field
      $('.deviceSelector').append(selector);
  }

  // Initialize selected items after a delay so selected macs are available in the context
  setTimeout(function(){
        // Retrieve MAC addresses from query string or cache
        var macs = getQueryString('macs') || getCache('selectedDevices');

        if(macs)
        {
          // Split MAC addresses if they are comma-separated
          macs = macs.split(',');
  
          console.log(macs)

          // Loop through macs to be selected list
          macs.forEach(function(mac) {

            // Create the option and append to Select2
            var option = new Option($('.deviceSelector select option[value="' + mac + '"]').html(), mac, true, true);

            $('.deviceSelector select').append(option).trigger('change');
          });       

        }        
    
    }, 10);

}


// --------------------------------------------------------
//Initialize Select2 Elements and make them sortable

$(function () {
  // Iterate over each Select2 dropdown
  $('.select2').each(function() {
      var selectEl = $(this).select2();

      // Apply sortable functionality to the dropdown's dropdown-container
      selectEl.next().children().children().children().sortable({
          containment: 'parent',
          update: function () {
              var sortedValues = $(this).children().map(function() {
                  return $(this).attr('title');
              }).get();

              var sortedOptions = selectEl.find('option').sort(function(a, b) {
                  return sortedValues.indexOf($(a).text()) - sortedValues.indexOf($(b).text());
              });

              // Replace all options in selectEl
              selectEl.empty().append(sortedOptions);

              // Trigger change event on Select2
              selectEl.trigger('change');
          }
      });
  });
});




// -----------------------------------------------------------------------------
// Initiate dropdown
function initSettingDropdown(settingKey,       // Identifier for the setting
                            valuesArray,       // Array of values to be pre-selected in the dropdown
                            targetLocation,    // ID of the HTML element where dropdown should be rendered (will be replaced)
                            callbackToGenerateEntries,  // Callback function to generate entries based on options
                            targetField,      // Target field or element where selected value should be applied or updated
                            nameTransformer)      // callback to transform the name (e.g. base64)
{

  var optionsHtml = ""
 
  optionsArray = createArray(getSettingOptions(settingKey))  

  // check if the result is a SQL query
  if(isSQLQuery(optionsArray[0]))
  {    
    readData(optionsArray[0], callbackToGenerateEntries, valuesArray, targetLocation, targetField, nameTransformer);

  } else // this should be already an array, e.g. from a setting or pre-defined
  {     
    optionsArray.forEach(option => {
      let selected = valuesArray.includes(option) ? 'selected' : '';
      optionsHtml += `<option value="${option}" ${selected}>${option}</option>`;
    });    
    
    // Replace the specified placeholder div with the resulting HTML 
    setTimeout(() => {

      $("#" + targetLocation).replaceWith(optionsHtml);
      
      }, 50);   
    
  }
}


// -----------------------------------------------------------------------------
// Hide elements on the page based on the supplied setting
function hideUIelements(settingKey) {

  hiddenSectionsSetting = getSetting(settingKey)
  
  if(hiddenSectionsSetting != "") // handle if settings not yet initialized
  {

    sectionsArray = createArray(hiddenSectionsSetting)

    // remove spaces to get IDs
    var newArray = $.map(sectionsArray, function(value) {
        return value.replace(/\s/g, '');
    });

    $.each(newArray, function(index, hiddenSection) {

      if($('#' + hiddenSection))
      {
        $('#' + hiddenSection).hide()      
      }    
      
    });
  }

}




// -----------------------------------------------------------------------------
// Data processors
// -----------------------------------------------------------------------------


// -----------------------------------------------------------------------------
// Processor to generate options for a dropdown menu
function generateDropdownOptions(data, valuesArray, targetField, nameTransformer) {
  var optionsHtml = "";
  data.forEach(function(item) {

    labelName = item.name

    // console.log(nameTransformer);
    // console.log(labelName);

    // if(nameTransformer && nameTransformer != '' && labelName != '❌None')
    // {
    //   console.log(labelName);
    //   labelName = nameTransformer(labelName)
    //   console.log(labelName);
    // }

    let selected = valuesArray.includes(item.id) ? 'selected' : '';

    optionsHtml += `<option value="${item.id}" ${selected}>${labelName}</option>`;
  });
  return `${optionsHtml}`;
}


// -----------------------------------------------------------------------------
// Processor to generate a list
function generateList(data, valuesArray, targetField, nameTransformer) {
  var listHtml = "";
  data.forEach(function(item) {

    labelName = item.name

    if(nameTransformer && nameTransformer != '' && labelName != '❌None')
    {
      labelName = nameTransformer(labelName)
    }

    let selected = valuesArray.includes(item.id) ? 'selected' : '';

    listHtml += `<li ${selected}>${labelName}</li>`;
  });

  return listHtml;
}

// -----------------------------------------------------------------------------
// Processor to generate a list in the deviceDetails page
function genListWithInputSet(data, valuesArray, targetField, nameTransformer) {

  var listHtml = "";

  console.log(data);
  data.forEach(function(item) {

    let selected = valuesArray.includes(item.id) ? 'selected' : '';

    console.log(item);

    labelName = item.name

    if(nameTransformer && nameTransformer != '' && labelName != '❌None')
    {
      labelName = nameTransformer(labelName)
    }

    listHtml += `<li ${selected}>
                      <a href="javascript:void(0)" onclick="setTextValue('${targetField}','${item.id}')">${labelName}</a> 
                </li>`;
    
  });

  return listHtml;
}


// -----------------------------------------------------------------------------
// Updates the icon preview  
function updateIconPreview (inputId) {
  // update icon
  iconInput = $(inputId) 

  value = iconInput.val()

  iconInput.on('change input', function() {
    $('#txtIconFA').html(atob(value))
  });    

  $('#txtIconFA').html(atob(value))
  
}

// -----------------------------------------------------------------------------
// initialize
// -----------------------------------------------------------------------------

initDeviceSelectors();

console.log("init ui_components.js")