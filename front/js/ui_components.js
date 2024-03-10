/* -----------------------------------------------------------------------------
*  Pi.Alert
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
  var devicesListAll_JSON = sessionStorage.getItem('devicesListAll_JSON');

  var devicesList = JSON.parse(devicesListAll_JSON);


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
    
    }, 100);

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
function initSettingDropdown(settingKey, targetLocation)
{

  var optionsHtml = ""
  var targetLocation_options = settingKey + "_initSettingDropdown"
 
  setVal = getSetting(settingKey)  

  console.log(setVal);

  // check if the result is a SQL query
  if(isSQLQuery(setVal))
  {
    
    optionsHtml += `<option id="${targetLocation_options}"></option>`;    
    
    readData(setVal, generateDropdownOptions, targetLocation_options);

  } else // this should be already an array, e.g. from a setting or pre-defined
  {     
    options = createArray(setVal);
    values = createArray(setVal);
    

    options.forEach(option => {
      let selected = values.includes(option) ? 'selected' : '';
      optionsHtml += `<option value="${option}" ${selected}>${option}</option>`;
    });     
    
    // Place the resulting HTML into the specified placeholder div
    $("#" + targetLocation).replaceWith(optionsHtml);
    
  }

}



// -----------------------------------------------------------------------------
// Data processors
// -----------------------------------------------------------------------------


// -----------------------------------------------------------------------------
// Processor to generate options for a dropdown menu
function generateDropdownOptions(data) {
  var optionsHtml = "";
  data.forEach(function(item) {
      optionsHtml += `<option value="${item.id}">${item.name}</option>`;
  });
  return `${optionsHtml}`;
}


// -----------------------------------------------------------------------------
// Processor to generate a list
function generateList(data) {
  var listHtml = "";
  data.forEach(function(item) {
      listHtml += `<li>${item.name}</li>`;
  });
  listHtml += "";
  return listHtml;
}


// -----------------------------------------------------------------------------
// initialize
// -----------------------------------------------------------------------------

initDeviceSelectors();

console.log("init ui_components.js")