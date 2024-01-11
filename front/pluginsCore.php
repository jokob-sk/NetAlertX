



<!-- Main content ---------------------------------------------------------- -->
<section class="content">
    <div class="plugin-filters">
        <div class="input-group col-sm-4">
            <label class="control-label col-sm-3"><?= lang('Plugins_Filters_Mac');?></label>
            <input class="form-control col-sm-3" id="txtMacFilter" type="text" value="--" readonly>
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


<script defer>

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
        case 'textarea_readonly':            
            value = `<textarea cols="70" rows="3" wrap="off" readonly style="white-space: pre-wrap;">
                    ${value.replace(/^b'(.*)'$/gm, '$1').replace(/\\n/g, '\n').replace(/\\r/g, '\r')}
                    </textarea>`;
            break;
        case 'textbox_save':

            value = value == 'null' ? '' : value; // hide 'null' values

            id = `${dbColumnDef.column}_${index}`

            value =    `<span class="form-group">
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
            value = `<span class="anonymizeMac"><a href="/deviceDetails.php?mac=${value}" target="_blank">${getNameByMacAddress(value)}</a><span>`;
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
        console.log(data) 

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

// -----------------------------------------------------------------------------
function generateTabs()
{
    activetab = 'active'

    //  clear previous headers data
    $('#tabs-location').html("");
    //  clear previous content data
    $('#tabs-content-location').html("");

    $.each(pluginDefinitions, function(index, pluginObj) {

        // console.log(pluginObj)

        if(pluginObj.show_ui) // hiding plugins where specified
        {
            prefix = pluginObj.unique_prefix;
            $('#tabs-location').append(
                `<li class=" left-nav ${activetab}">
                    <a class=" col-sm-12  " href="#${prefix}" data-plugin-prefix="${prefix}" id="${prefix}_id" data-toggle="tab" >
                    ${getString(`${prefix}_icon`)} ${getString(`${prefix}_display_name`)}
                    </a>
                </li>`
            );
            activetab = '' // only first tab is active
        }
    });

    activetab = 'active'
    
    $.each(pluginDefinitions, function(index, pluginObj) {

        headersHtml = ""        
        colDefinitions = []
        evRows = ""
        obRows = ""
        hiRows = ""
        prefix = pluginObj.unique_prefix;

        // Generate the header
        $.each(pluginObj["database_column_definitions"], function(index, colDef){
            if(colDef.show == true) // select only the ones to show
            {
                colDefinitions.push(colDef)            
                headersHtml += `<th class="${colDef.css_classes}" >${getString(`${prefix}_${colDef.column}_name` )}</th>`
            }
        });

        // Generate the event rows
        var eveCount = 0;
        for(i=0;i<pluginUnprocessedEvents.length;i++)
        {
            if(pluginUnprocessedEvents[i].Plugin == prefix)
            {
                clm = ""

                for(j=0;j<colDefinitions.length;j++) 
                {   
                    clm += '<td>'+ pluginUnprocessedEvents[i][colDefinitions[j].column] +'</td>'
                }                   
                evRows += `<tr data-my-index="${pluginUnprocessedEvents[i]["Index"]}" >${clm}</tr>`
                eveCount++;
            }            
        }      

        // Generate the history rows        
        var histCount = 0
        var histCountDisplayed = 0
        
        for(i=0;i < pluginHistory.length ;i++) 
        {
            if(pluginHistory[i].Plugin == prefix)
            {
                if(histCount < 50) // only display 50 entries to optimize performance
                {       
                    clm = ""

                    for(j=0;j<colDefinitions.length;j++) 
                    {   
                        clm += '<td>'+ pluginHistory[i][colDefinitions[j].column] +'</td>'
                    }            
                    hiRows += `<tr data-my-index="${pluginHistory[i]["Index"]}" >${clm}</tr>`

                    histCountDisplayed++;
                }
                histCount++; // count and display the total
            }            
        }        

        // Generate the object rows
        var obCount = 0;
        for(var i=0;i<pluginObjects.length;i++)
        {
            if(pluginObjects[i].Plugin == prefix)
            {
                if(shouldBeShown(pluginObjects[i], pluginObj)) // filter TODO
                {
                    clm = ""

                    for(var j=0;j<colDefinitions.length;j++) 
                    {   
                        clm += '<td>'+ getFormControl(colDefinitions[j], pluginObjects[i][colDefinitions[j].column], pluginObjects[i]["Index"], colDefinitions, pluginObjects[i]) +'</td>'
                    }                                   
                    obRows += `<tr data-my-index="${pluginObjects[i]["Index"]}" >${clm}</tr>`
                    obCount++;
                }
            }            
        }

        // Generate the HTML

        $('#tabs-content-location').append(
            `    
            <div id="${prefix}" class="tab-pane ${activetab}">
                <div class="nav-tabs-custom" style="margin-bottom: 0px">
                    <ul class="nav nav-tabs">
                        <li class="active" >
                            <a href="#objectsTarget_${prefix}" data-toggle="tab" >
                                
                                <i class="fa fa-cube"></i> <?= lang('Plugins_Objects');?> (${obCount})
                                
                            </a>
                        </li>

                        <li >
                            <a href="#eventsTarget_${prefix}" data-toggle="tab" >
                                
                                <i class="fa fa-bolt"></i> <?= lang('Plugins_Unprocessed_Events');?> (${eveCount})
                                
                            </a>
                        </li>

                        <li >
                            <a href="#historyTarget_${prefix}" data-toggle="tab" >
                                
                                <i class="fa fa-clock"></i> <?= lang('Plugins_History');?> (${histCountDisplayed} <?= lang('Plugins_Out_of');?> ${histCount})
                                
                            </a>
                        </li>

                    <ul>
                </div>
                

                <div class="tab-content">

                    <div id="objectsTarget_${prefix}" class="tab-pane ${activetab}">
                        <table class="table table-striped" data-my-dbtable="Plugins_Objects"> 
                            <tbody>
                                <tr>
                                    ${headersHtml}                            
                                </tr>  
                                ${obRows}
                            </tbody>
                        </table>
                        <div class="plugin-obj-purge">                                 
                            <button class="btn btn-primary" onclick="purgeAll('${prefix}', 'Plugins_Objects' )"><?= lang('Plugins_DeleteAll');?></button> 
                        </div> 
                    </div>
                    <div id="eventsTarget_${prefix}" class="tab-pane">
                        <table class="table table-striped" data-my-dbtable="Plugins_Events">
                        
                            <tbody>
                                <tr>
                                    ${headersHtml}                            
                                </tr>  
                                ${evRows}
                            </tbody>
                        </table>
                        <div class="plugin-obj-purge">                                 
                            <button class="btn btn-primary" onclick="purgeAll('${prefix}', 'Plugins_Events' )"><?= lang('Plugins_DeleteAll');?></button> 
                        </div> 
                    </div>    
                    <div id="historyTarget_${prefix}" class="tab-pane">
                        <table class="table table-striped" data-my-dbtable="Plugins_History">
                        
                            <tbody>
                                <tr>
                                    ${headersHtml}                            
                                </tr>  
                                ${hiRows}
                            </tbody>
                        </table>
                        <div class="plugin-obj-purge">                                 
                            <button class="btn btn-primary" onclick="purgeAll('${prefix}', 'Plugins_History' )"><?= lang('Plugins_DeleteAll');?></button> 
                        </div> 
                    </div>                   


                </div>

                <div class='plugins-description'>

                    ${getString(prefix + '_description')} 
                
                    <span>
                        <a href="https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins/${pluginObj.code_name}" target="_blank"><?= lang('Gen_ReadDocs');?></a>
                    </span>
                
                </div>
            </div>
        `);

        activetab = '' // only first tab is active
    });

    initTabs()    
}

// --------------------------------------------------------
// Handle active / selected tabs
// handle first tab (objectsTarget_) display 
function initTabs()
{
    // events on tab change
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var target = $(e.target).attr("href") // activated tab
       
        // save the last prefix
        if(target.includes('_') == false )
        {
            pref = target.split('#')[1]
        } else
        {
            pref = target.split('_')[1]
        } 

        everythingHidden = false;

        if($('#objectsTarget_'+ pref) != undefined && $('#historyTarget_'+ pref) != undefined && $('#eventsTarget_'+ pref) != undefined)
        {
            var isObjectsInactive = !$('#objectsTarget_' + pref).hasClass('active');
            var isHistoryInactive = !$('#historyTarget_' + pref).hasClass('active');
            var isEventsInactive = !$('#eventsTarget_' + pref).hasClass('active');

            var everythingHidden = isObjectsInactive && isHistoryInactive && isEventsInactive;

        }

        // show the objectsTarget if no specific pane selected or if selected is hidden        
        if (target === '#' + pref && everythingHidden) {
            var objectsTarget = $('#objectsTarget_' + pref);

            if (objectsTarget.length > 0) {
                var classTmp = objectsTarget.attr('class');

                if (!classTmp.includes('active')) {
                    classTmp += ' active';            
                    objectsTarget.attr('class', classTmp);
                }
            } 
        }
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
dbTable    = ''

function purgeAll(callback) {
  plugPrefix = arguments[0];  // plugin prefix
  dbTable    = arguments[1];  // DB table
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
function purgeVisible() {

    idArr = $(`#${plugPrefix} table[data-my-dbtable="${dbTable}"] tr[data-my-index]`).map(function(){return $(this).attr("data-my-index");}).get();

    $.ajax({
        method: "POST",
        url: "php/server/dbHelper.php",
        data: { action: "delete", dbtable: dbTable, columnName: 'Index', id:idArr.toString() },
        success: function(data, textStatus) {
            showModalOk ('Result', data );
        }
    })

}


// -----------------------------------------------------------------------------
// Main sequence

getData()
updater()

</script>
