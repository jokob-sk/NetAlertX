<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>

<!-- ----------------------------------------------------------------------- -->
<!-- Datatable -->
<link rel="stylesheet" href="lib/datatables.net-bs/css/dataTables.bootstrap.min.css">
  <link rel="stylesheet" href="lib/datatables.net/css/select.dataTables.min.css">
  <script src="lib/datatables.net/js/jquery.dataTables.min.js"></script>
  <script src="lib/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>
  <script src="lib/datatables.net/js/dataTables.select.min.js"></script>


<!-- Main content ---------------------------------------------------------- -->
<section class="content">
  <div class="plugin-filters">
    <div class="input-group col-sm-12">
      <label class="col-sm-3"><?= lang('Plugins_Filters_Mac');?></label>
      <input class="col-sm-3" id="txtMacFilter" type="text" value="--" readonly>
    </div>
  </div>
  <div class="nav-tabs-custom plugin-content" style="margin-bottom: 0px;">
    
    <ul id="tabs-location" class="nav nav-tabs col-sm-2 ">
      <!-- PLACEHOLDER -->
    </ul>  
    <div id="tabs-content-location" class="tab-content col-sm-10"> 
      <!-- PLACEHOLDER -->
    </div>   
  
</section>



<script>

// -----------------------------------------------------------------------------
// Initializes fields based on current MAC
function initFields() {   

  var urlParams = new URLSearchParams(window.location.search);
  mac = urlParams.get ('mac');  

  // if the current mac has changed, reinitialize the data
  if(mac != undefined && $("#txtMacFilter").val() != mac)
  {    
    
    $("#txtMacFilter").val(mac);    

    getData();
  } 

}

// -----------------------------------------------------------------------------
// Checking if current MAC has changed and triggering an updated if needed
function updater() {   

  initFields()

  // loop
  setTimeout(function() {
    updater();
  }, 500);   
}

// -----------------------------------------------------------------------------
// Get form control according to the column definition from config.json > database_column_definitions
function getFormControl(dbColumnDef, value, index) {  

  result = ''

  // Check if mapped_to_column_data exists and has a value to override the supplied value which is most likely `undefined`
  if (dbColumnDef.mapped_to_column_data && dbColumnDef.mapped_to_column_data.value) {
    value = dbColumnDef.mapped_to_column_data.value;
  }

   
  result = processColumnValue(dbColumnDef, value, index, dbColumnDef.type)

  return result;
}

// -----------------------------------------------------------------------------
// Process column value 
function processColumnValue(dbColumnDef, value, index, type) {
  if (type.includes('.')) {
  const typeParts = type.split('.');
  
  // recursion
  for (const typePart of typeParts) {
    value = processColumnValue(dbColumnDef, value, index, typePart)
  }

  } else{
  // pick form control based on the supplied type
  switch(type)
  {
    case 'label':      
      value = `<span>${value}<span>`;
      break;
    case 'none':      
      value = `${value}`;
      break;
    case 'textarea_readonly':      
      value = `<textarea cols="70" rows="3" wrap="off" readonly style="white-space: pre-wrap;">
          ${value.replace(/^b'(.*)'$/gm, '$1').replace(/\\n/g, '\n').replace(/\\r/g, '\r')}
          </textarea>`;
      break;
    case 'textbox_save':

      value = value == 'null' ? '' : value; // hide 'null' values

      id = `${dbColumnDef.column}_${index}`

      value =  `<span class="form-group">
              <div class="input-group">
                <input class="form-control" type="text" value="${value}" id="${id}" data-my-column="${dbColumnDef.column}"  data-my-index="${index}" name="${dbColumnDef.column}">
                <span class="input-group-addon"><i class="fa fa-save pointer" onclick="genericSaveData('${id}');"></i></span>
              </div>
            <span>`;
      break;
    case 'url':
      value = `<span><a href="${value}" target="_blank">${value}</a><span>`;
      break;
    case 'url_http_https':
      
      value = `<span>
            <a href="http://${value}" target="_blank">
              <i class="fa fa-lock-open "></i>
            </a>
            /
            <a href="https://${value}" target="_blank">
              <i class="fa fa-lock "></i>
            </a>
          <span>`;
      break;
    case 'device_name_mac':
      value = createDeviceLink(value);
      break;
    case 'device_mac':
      value = `<span class="anonymizeMac"><a href="/deviceDetails.php?mac=${value}" target="_blank">${value}</a><span>`;
      break;
    case 'device_ip':
      value = `<span class="anonymizeIp"><a href="#" onclick="navigateToDeviceWithIp('${value}')" >${value}</a><span>`;
      break;
    case 'threshold': 

      valueTmp = ''

      $.each(dbColumnDef.options, function(index, obj) {
        if(Number(value) < Number(obj.maximum) && valueTmp == '') 
        {
          valueTmp = `<div style="background-color:${obj.hexColor}">${value}</div>`
          // return;
        }
      });

      value = valueTmp;

      break;
    case 'replace': 
      $.each(dbColumnDef.options, function(index, obj) {
        if(value == obj.equals)
        {
          value = `<span title="${value}">${obj.replacement}</span>`
        }
      });
      break;
    case 'regex':
      
      for (const option of dbColumnDef.options) {
        if (option.type === type) {
          
          const regexPattern = new RegExp(option.param);
          const match = value.match(regexPattern);
          if (match) {
            // Return the first match
            value =  match[0];
          
          }
        }
      }
      break;
    case 'eval':
      
      for (const option of dbColumnDef.options) {
        if (option.type === type) {
          // console.log(option.param)
          value =  eval(option.param);
        }
      }
      break;
      
    default:
      value = value + `<div style='text-align:center' title="${getString("Plugins_no_control")}"><i class='fa-solid fa-circle-question'></i></div>` ;       
  }
  }

  // Default behavior if no match is found
  return value;
}



// -----------------------------------------------------------------------------
// Update the corresponding DB column and entry
function genericSaveData (id) {
  columnName  = $(`#${id}`).attr('data-my-column')
  index  = $(`#${id}`).attr('data-my-index')
  columnValue = $(`#${id}`).val()

  console.log(columnName)
  console.log(index)
  console.log(columnValue)

  $.get(`php/server/dbHelper.php?action=update&dbtable=Plugins_Objects&columnName=Index&id=${index}&columns=UserData&values=${columnValue}`, function(data) {
  
    // var result = JSON.parse(data);
    // console.log(data) 

    if(sanitize(data) == 'OK')
    {      
      showMessage('<?= lang('Gen_DataUpdatedUITakesTime');?>')      
      // Remove navigation prompt "Are you sure you want to leave..."
      window.onbeforeunload = null;
    } else
    {
      showMessage('<?= lang('Gen_LockedDB');?>')       
    }    

  });  
}


// -----------------------------------------------------------------------------
pluginDefinitions = []
pluginUnprocessedEvents = []
pluginObjects = []
pluginHistory = []

function getData(){

  // Show the loading spinner while generating 
  showSpinner();

  $.get('api/plugins.json', function(res) {  
    
    pluginDefinitions = res["data"];

    $.get('api/table_plugins_events.json', function(res) {

      pluginUnprocessedEvents = res["data"];

      $.get('api/table_plugins_objects.json', function(res) {

        pluginObjects = res["data"];
        
        $.get('api/table_plugins_history.json', function(res) {        

          pluginHistory = res["data"];

          generateTabs()

        });
      });
    });

  });
}

function generateTabs() {

  // Reset the tabs by clearing previous headers and content
  resetTabs();

  // Sort pluginDefinitions by unique_prefix alphabetically
  pluginDefinitions.sort((a, b) => a.unique_prefix.localeCompare(b.unique_prefix));

  // Iterate over the sorted pluginDefinitions to create tab headers and content
  pluginDefinitions.forEach(pluginObj => {
    if (pluginObj.show_ui) {
      stats = createTabContent(pluginObj); // Create the content for each tab
      createTabHeader(pluginObj, stats); // Create the header for each tab
    }
  });

  hideSpinner()  
}

function resetTabs() {
  // Clear any existing tab headers and content from the DOM
  $('#tabs-location').empty();
  $('#tabs-content-location').empty();
}

function createTabHeader(pluginObj, stats) {
  const prefix = pluginObj.unique_prefix; // Get the unique prefix for the plugin
  // Determine the active class for the first tab
  const activeClass = pluginDefinitions.indexOf(pluginObj) === 0 ? 'active' : '';

  // Append the tab header to the tabs location
  $('#tabs-location').append(`
    <li class="left-nav ${activeClass} ">
      <a class="col-sm-12 textOverflow" href="#${prefix}" data-plugin-prefix="${prefix}" id="${prefix}_id" data-toggle="tab">
        ${getString(`${prefix}_icon`)} ${getString(`${prefix}_display_name`)}
        
      </a>
      ${stats.objectDataCount > 0 ? `<div class="pluginBadgeWrap"><span title="" class="badge pluginBadge" >${stats.objectDataCount}</span></div>` : ""}      
    </li>
  `);
}

function createTabContent(pluginObj) {
  const prefix = pluginObj.unique_prefix; // Get the unique prefix for the plugin
  const colDefinitions = getColumnDefinitions(pluginObj); // Get column definitions for DataTables
  
  // Get data for events, objects, and history related to the plugin
  const objectData = getObjectData(prefix, colDefinitions, pluginObj);
  const eventData = getEventData(prefix, colDefinitions);
  const historyData = getHistoryData(prefix, colDefinitions, pluginObj);

  // Append the content structure for the plugin's tab to the content location
  $('#tabs-content-location').append(`
    <div id="${prefix}" class="tab-pane ${pluginDefinitions.indexOf(pluginObj) === 0 ? 'active' : ''}">
      ${generateTabNavigation(prefix, objectData.length, eventData.length, historyData.length)} <!-- Create tab navigation -->
      <div class="tab-content">
        ${generateDataTable(prefix, 'Objects', objectData, colDefinitions)} 
        ${generateDataTable(prefix, 'Events', eventData, colDefinitions)} 
        ${generateDataTable(prefix, 'History', historyData, colDefinitions)} 
      </div>
      <div class='plugins-description'>
        ${getString(`${prefix}_description`)} <!-- Display the plugin description -->
        <span><a href="https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins/${pluginObj.code_name}" target="_blank">${getString('Gen_ReadDocs')}</a></span> <!-- Link to documentation -->
      </div>
    </div>
  `);

  // Initialize DataTables for the respective sections
  initializeDataTables(prefix, objectData, eventData, historyData, colDefinitions);

  return { 
            "objectDataCount": objectData.length, 
            "eventDataCount": eventData.length, 
            "historyDataCount": historyData.length 
         }
}

function getColumnDefinitions(pluginObj) {
  // Filter and return only the columns that are set to show in the UI
  return pluginObj["database_column_definitions"].filter(colDef => colDef.show);
}

function getEventData(prefix, colDefinitions) {
  // Extract event data specific to the plugin and format it for DataTables
  return pluginUnprocessedEvents
    .filter(event => event.Plugin === prefix) // Filter events for the specific plugin
    .map(event => colDefinitions.map(colDef => event[colDef.column] || '')); // Map to the defined columns
}

function getObjectData(prefix, colDefinitions, pluginObj) {
  // Extract object data specific to the plugin and format it for DataTables
  return pluginObjects
    .filter(object => object.Plugin === prefix && shouldBeShown(object, pluginObj)) // Filter objects for the specific plugin
    .map(object => colDefinitions.map(colDef => getFormControl(colDef, object[colDef.column], object["Index"], colDefinitions, object))); // Map to the defined columns
}

function getHistoryData(prefix, colDefinitions, pluginObj) {
  // Extract history data for the plugin, limiting to the first 50 entries for performance
  return pluginHistory
    .filter((history, index) => history.Plugin === prefix && index < 50) // Filter history for the specific plugin
    .map(history => colDefinitions.map(colDef => history[colDef.column] || '')); // Map to the defined columns
}

function generateTabNavigation(prefix, objectCount, eventCount, historyCount) {
  // Create navigation tabs for Objects, Unprocessed Events, and History
  return `
    <div class="nav-tabs-custom" style="margin-bottom: 0px">
      <ul class="nav nav-tabs">
        <li class="active">
          <a href="#objectsTarget_${prefix}" data-toggle="tab"><i class="fa fa-cube"></i> ${getString('Plugins_Objects')} (${objectCount})</a>
        </li>
        <li>
          <a href="#eventsTarget_${prefix}" data-toggle="tab"><i class="fa fa-bolt"></i> ${getString('Plugins_Unprocessed_Events')} (${eventCount})</a>
        </li>
        <li>
          <a href="#historyTarget_${prefix}" data-toggle="tab"><i class="fa fa-clock"></i> ${getString('Plugins_History')} (${historyCount})</a>
        </li>
      </ul>
    </div>
  `;
}

function generateDataTable(prefix, tableType, data, colDefinitions) {
  // Generate HTML for a DataTable and associated buttons for a given table type
  const headersHtml = colDefinitions.map(colDef => `<th class="${colDef.css_classes}">${getString(`${prefix}_${colDef.column}_name`)}</th>`).join('');
  
  return `
    <div id="${tableType.toLowerCase()}Target_${prefix}" class="tab-pane ${tableType == "Objects" ? "active":""}">
      <table id="${tableType.toLowerCase()}Table_${prefix}" class="display table table-striped table-stretched" data-my-dbtable="Plugins_${tableType}">
        <thead><tr>${headersHtml}</tr></thead>
      </table>
      <div class="plugin-obj-purge">
        <button class="btn btn-primary" onclick="purgeAll('${prefix}', 'Plugins_${tableType}' )"><?= lang('Plugins_DeleteAll');?></button>
        ${tableType !== 'Events' ? `<button class="btn btn-danger" onclick="deleteListed('${prefix}', 'Plugins_${tableType}' )"><?= lang('Plugins_Obj_DeleteListed');?></button>` : ''}
      </div>
    </div>
  `;
}

function initializeDataTables(prefix, objectData, eventData, historyData, colDefinitions) {
  // Common settings for DataTables initialization
  const commonDataTableSettings = {
    orderable: false, // Disable ordering
    createdRow: function(row, data) {
      $(row).attr('data-my-index', data[0]); // Set data attribute for indexing
    }
  };

  // Initialize DataTable for Objects
  $(`#objectsTable_${prefix}`).DataTable({
    data: objectData,
    columns: colDefinitions.map(colDef => ({ title: getString(`${prefix}_${colDef.column}_name`) })), // Column titles
    ...commonDataTableSettings // Spread common settings
  });

  // Initialize DataTable for Unprocessed Events
  $(`#eventsTable_${prefix}`).DataTable({
    data: eventData,
    columns: colDefinitions.map(colDef => ({ title: getString(`${prefix}_${colDef.column}_name`) })), // Column titles
    ...commonDataTableSettings // Spread common settings
  });

  // Initialize DataTable for History
  $(`#historyTable_${prefix}`).DataTable({
    data: historyData,
    columns: colDefinitions.map(colDef => ({ title: getString(`${prefix}_${colDef.column}_name`) })), // Column titles
    ...commonDataTableSettings // Spread common settings
  });
}

// --------------------------------------------------------
// Filter method that determines if an entry should be shown
function shouldBeShown(entry, pluginObj)
{  
  if (pluginObj.hasOwnProperty('data_filters')) {
    
    let dataFilters = pluginObj.data_filters;

    // Loop through 'data_filters' array and appply filters on individual plugin entries
    for (let i = 0; i < dataFilters.length; i++) {
      
      compare_field_id = dataFilters[i].compare_field_id;
      compare_column = dataFilters[i].compare_column;
      compare_operator = dataFilters[i].compare_operator;
      compare_js_template = dataFilters[i].compare_js_template;
      compare_use_quotes = dataFilters[i].compare_use_quotes;
      compare_field_id_value = $(`#${compare_field_id}`).val();      

      // apply filter i sthe filter field has a valid value
      if(compare_field_id_value != undefined && compare_field_id_value != '--') 
      {
        // valid value        
        // resolve the left and right part of the comparison 
        let left = compare_js_template.replace('{value}', `${compare_field_id_value}`)
        let right = compare_js_template.replace('{value}', `${entry[compare_column]}`)

        // include wrapper quotes if specified
        compare_use_quotes ? quotes = '"' : quotes = ''         

        result =  eval(
                quotes +  `${eval(left)}` + quotes + 
                        ` ${compare_operator} ` + 
                quotes +  `${eval(right)}` + quotes 
              ); 

        return result;                
      }
    }
  }
  return true;
}

// --------------------------------------------------------
// Data cleanup/purge functionality
plugPrefix = ''
dbTable  = ''

function purgeAll(callback) {
  plugPrefix = arguments[0];  // plugin prefix
  dbTable  = arguments[1];  // DB table
  // Ask 
  showModalWarning('<?= lang('Gen_Purge');?>' + ' ' + plugPrefix + ' ' + dbTable , '<?= lang('Gen_AreYouSure');?>',
  '<?= lang('Gen_Cancel');?>', '<?= lang('Gen_Okay');?>', "purgeAllExecute");
}

// --------------------------------------------------------
function purgeAllExecute() {
  $.ajax({
    method: "POST",
    url: "php/server/dbHelper.php",
    data: { action: "delete", dbtable: dbTable, columnName: 'Plugin', id:plugPrefix },
    success: function(data, textStatus) {
      showModalOk ('Result', data );
    }
  })
}

// --------------------------------------------------------
function deleteListed(plugPrefix, dbTable) {

  idArr = $(`#${plugPrefix} table[data-my-dbtable="${dbTable}"] tr[data-my-index]`).map(function(){return $(this).attr("data-my-index");}).get();

  console.log(idArr);

  $.ajax({
    method: "POST",
    url: "php/server/dbHelper.php",
    data: { action: "delete", dbtable: dbTable, columnName: 'Index', id:idArr.toString() },
    success: function(data, textStatus) {
      updateApi("plugins_objects")
      showModalOk ('Result', data );      
    }
  })

}


// -----------------------------------------------------------------------------
// Main sequence

// show spinning icon
showSpinner()
getData()
updater()

</script>
