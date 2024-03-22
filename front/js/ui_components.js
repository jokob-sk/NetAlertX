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
function initSettingDropdown(settingKey, valuesArray, targetLocation, callbackToGenerateEntries, targetField)
{

  var optionsHtml = ""
 
  optionsArray = createArray(getSettingOptions(settingKey))  

  // check if the result is a SQL query
  if(isSQLQuery(optionsArray[0]))
  {    
    readData(optionsArray[0], callbackToGenerateEntries, valuesArray, targetLocation, targetField);

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
// Data processors
// -----------------------------------------------------------------------------


// -----------------------------------------------------------------------------
// Processor to generate options for a dropdown menu
function generateDropdownOptions(data, valuesArray) {
  var optionsHtml = "";
  data.forEach(function(item) {

    let selected = valuesArray.includes(item.id) ? 'selected' : '';

    optionsHtml += `<option value="${item.id}" ${selected}>${item.name}</option>`;
  });
  return `${optionsHtml}`;
}


// -----------------------------------------------------------------------------
// Processor to generate a list
function generateList(data, valuesArray) {
  var listHtml = "";
  data.forEach(function(item) {

    let selected = valuesArray.includes(item.id) ? 'selected' : '';

    listHtml += `<li ${selected}>${item.name}</li>`;
  });

  return listHtml;
}

// -----------------------------------------------------------------------------
// Processor to generate a list
function generatedevDetailsList(data, valuesArray, targetField) {

  var listHtml = "";

  console.log(data);
  data.forEach(function(item) {

    let selected = valuesArray.includes(item.id) ? 'selected' : '';


    console.log(item);

    // listHtml += `<li ${selected}>${item.name}</li>`;
    listHtml += `<li ${selected}>
                      <a href="javascript:void(0)" onclick="setTextValue('${targetField}','${item.id}')">${item.name}</a> 
                </li>`;
    
  });

  return listHtml;
}


// -----------------------------------------------------------------------------
// initialize
// -----------------------------------------------------------------------------

initDeviceSelectors();

console.log("init ui_components.js")