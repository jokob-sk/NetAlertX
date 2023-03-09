<?php

  require 'php/templates/header.php';  
?>

<script src="js/pialert_common.js"></script>

<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

    <!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
        <?php require 'php/templates/notification.php'; ?>
        <h1 id="pageTitle">
            <i class="fa fa-fw fa-plug"></i> <?= lang('Navigation_Plugins');?>
            <span class="pageHelp"> <a target="_blank" href="https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins"><i class="fa fa-circle-question"></i></a><span>
        </h1>    
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">
        <div class="nav-tabs-custom plugin-content" style="margin-bottom: 0px;">
            <ul id="tabs-location" class="nav nav-tabs">
                <!-- PLACEHOLDER -->
            </ul>  
            <div id="tabs-content-location" class="tab-content"> 
                <!-- PLACEHOLDER -->
            </div>   
        
    </section>    
</div>

<?php
  require 'php/templates/footer.php';
?>

<script defer>

// -----------------------------------------------------------------------------
// Get form control according to the column definition from config.json > database_column_definitions
function getFormControl(dbColumnDef, value, index) {    

    result = ''

    switch(dbColumnDef.type)
    {
        case 'label':            
            result = `<span>${value}<span>`;
            break;
        case 'textboxsave':

            value = value == 'null' ? '' : value; // hide 'null' values

            id = `${dbColumnDef.column}_${index}`

            result =    `<span class="form-group">
                            <div class="input-group">
                                <input class="form-control" type="text" value="${value}" id="${id}" data-my-column="${dbColumnDef.column}"  data-my-index="${index}" name="${dbColumnDef.column}">
                                <span class="input-group-addon"><i class="fa fa-save pointer" onclick="saveData('${id}');"></i></span>
                            </div>
                        <span>`;
            break;
        case 'url':
            result = `<span><a href="${value}" target="_blank">${value}</a><span>`;
            break;
        case 'threshold': 
            $.each(dbColumnDef.options, function(index, obj) {
                if(Number(value) < obj.maximum && result == '')
                {
                    result = `<div style="background-color:${obj.hexColor}">${value}</div>`
                    // return;
                }
            });
            break;
        case 'replace': 
            $.each(dbColumnDef.options, function(index, obj) {
                if(value == obj.equals)
                {
                    result = `<span title="${value}">${obj.replacement}</span>`
                }
            });
            break;
        default:
            result = value;           
    }

    return result;
}

// -----------------------------------------------------------------------------
// Update the coresponding DB column and entry
function saveData (id) {
    columnName  = $(`#${id}`).attr('data-my-column')
    index  = $(`#${id}`).attr('data-my-index')
    columnValue = $(`#${id}`).val()

    $.get(`php/server/dbHelper.php?action=update&dbtable=Plugins_Objects&key=Index&id=${index}&columns=UserData&values=${columnValue}`, function(data) {
    
        // var result = JSON.parse(data);
        console.log(data) 

        if(sanitize(data) == 'OK')
        {
          showMessage("Saved")
          // Remove navigation prompt "Are you sure you want to leave..."
          window.onbeforeunload = null;
        } else
        {
          showMessage("ERROR")
        }        
    
    // if (result) {
    //   period = result;
    //   $('#period').val(period);
    // }

    });    
}

// -----------------------------------------------------------------------------
// Get translated string
function localize (obj, key) {

    currLangCode = getCookie("language")

    result = ""
    en_us = ""

    if(obj.localized && obj.localized.includes(key))
    {
        for(i=0;i<obj[key].length;i++)
        {
            code = obj[key][i]["language_code"]

            // console.log(code)

            if( code == 'en_us')
            {
                en_us = obj[key][i]["string"]
            }

            if(code == currLangCode)
            {
                result = obj[key][i]["string"]
            }

        }
    }

    result == "" ? en_us : result ;

    return result;
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

    $.each(pluginDefinitions, function(index, obj) {
        $('#tabs-location').append(
            `<li class=" ${activetab}">
                <a href="#${obj.unique_prefix}" data-plugin-prefix="${obj.unique_prefix}" id="${obj.unique_prefix}_id" data-toggle="tab" >
                ${localize(obj, 'icon')} ${localize(obj, 'display_name')}
                </a>
            </li>`
        );
        activetab = '' // only first tab is active
    });

    activetab = 'active'
    
    $.each(pluginDefinitions, function(index, obj) {

        

        headersHtml = ""
        // headers = []
        colDefinitions = []
        evRows = ""
        obRows = ""
        hiRows = ""

        // Generate the header
        $.each(obj["database_column_definitions"], function(index, colDef){
            if(colDef.show == true) // select only the ones to show
            {
                colDefinitions.push(colDef)            
                headersHtml += `<th class="col-sm-2" >${localize(colDef, "name" )}</th>`
            }
        });

        // Generate the event rows
        var eveCount = 0;
        for(i=0;i<pluginUnprocessedEvents.length;i++)
        {
            if(pluginUnprocessedEvents[i].Plugin == obj.unique_prefix)
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
        for(i=0;i<pluginHistory.length;i++)
        {
            if(pluginHistory[i].Plugin == obj.unique_prefix)
            {
                clm = ""

                for(j=0;j<colDefinitions.length;j++) 
                {   
                    clm += '<td>'+ pluginHistory[i][colDefinitions[j].column] +'</td>'
                }                   
                hiRows += `<tr data-my-index="${pluginHistory[i]["Index"]}" >${clm}</tr>`
                histCount++;
            }            
        }        

        // Generate the object rows
        var obCount = 0;
        for(var i=0;i<pluginObjects.length;i++)
        {
            if(pluginObjects[i].Plugin == obj.unique_prefix)
            {
                clm = ""

                for(var j=0;j<colDefinitions.length;j++) 
                {   
                    clm += '<td>'+ getFormControl(colDefinitions[j], pluginObjects[i][colDefinitions[j].column], pluginObjects[i]["Index"]) +'</td>'
                }                                   
                obRows += `<tr data-my-index="${pluginObjects[i]["Index"]}" >${clm}</tr>`
                obCount++;
            }            
        }


        $('#tabs-content-location').append(
            `    
            <div id="${obj.unique_prefix}" class="tab-pane ${activetab}">
                <div class="nav-tabs-custom" style="margin-bottom: 0px">
                    <ul class="nav nav-tabs">
                        <li class="active" >
                            <a href="#objectsTarget_${obj.unique_prefix}" data-toggle="tab" >
                                
                                <i class="fa fa-cube"></i> <?= lang('Plugins_Objects');?> (${obCount})
                                
                            </a>
                        </li>

                        <li >
                            <a href="#eventsTarget_${obj.unique_prefix}" data-toggle="tab" >
                                
                                <i class="fa fa-bolt"></i> <?= lang('Plugins_Unprocessed_Events');?> (${eveCount})
                                
                            </a>
                        </li>

                        <li >
                            <a href="#historyTarget_${obj.unique_prefix}" data-toggle="tab" >
                                
                                <i class="fa fa-clock"></i> <?= lang('Plugins_History');?> (${histCount})
                                
                            </a>
                        </li>

                    <ul>
                </div>
                

                <div class="tab-content">

                    <div id="objectsTarget_${obj.unique_prefix}" class="tab-pane ${activetab}">
                        <table class="table table-striped" data-my-dbtable="Plugins_Objects"> 
                            <tbody>
                                <tr>
                                    ${headersHtml}                            
                                </tr>  
                                ${obRows}
                            </tbody>
                        </table>
                        <div class="plugin-obj-purge">                                 
                            <button class="btn btn-primary" onclick="purgeAll('${obj.unique_prefix}', 'Plugins_Objects' )"><?= lang('Gen_Purge');?></button> 
                        </div> 
                    </div>
                    <div id="eventsTarget_${obj.unique_prefix}" class="tab-pane">
                        <table class="table table-striped" data-my-dbtable="Plugins_Events">
                        
                            <tbody>
                                <tr>
                                    ${headersHtml}                            
                                </tr>  
                                ${evRows}
                            </tbody>
                        </table>
                        <div class="plugin-obj-purge">                                 
                            <button class="btn btn-primary" onclick="purgeAll('${obj.unique_prefix}', 'Plugins_Events' )"><?= lang('Gen_Purge');?></button> 
                        </div> 
                    </div>    
                    <div id="historyTarget_${obj.unique_prefix}" class="tab-pane">
                        <table class="table table-striped" data-my-dbtable="Plugins_History">
                        
                            <tbody>
                                <tr>
                                    ${headersHtml}                            
                                </tr>  
                                ${hiRows}
                            </tbody>
                        </table>
                        <div class="plugin-obj-purge">                                 
                            <button class="btn btn-primary" onclick="purgeAll('${obj.unique_prefix}', 'Plugins_History' )"><?= lang('Gen_Purge');?></button> 
                        </div> 
                    </div>                   


                </div>

                ${localize(obj, 'description')} 
            
                <span>
                    <a href="https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins/${obj.code_name}" target="_blank"><?= lang('Gen_Help');?></a>
                </span>
                
            </div>
        `);

        activetab = '' // only first tab is active
    });

    initTabs()
    
}

// --------------------------------------------------------
var lastPrefix = ''
function initTabs()
{
    // events on tab change
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var target = $(e.target).attr("href") // activated tab
       
        // save the last prefix
        if(target.includes('_') == false )
        {
            lastPrefix = target.split('#')[1]
        } 

        // show the objectsTarget if no specific pane selected or if selected is

        if($('#objectsTarget_'+ lastPrefix).is(":hidden") && $('#eventsTarget_'+ lastPrefix).is(":hidden") && $('#historyTarget_'+ lastPrefix).is(":hidden"))
        { 
            $('#objectsTarget_'+ lastPrefix).show();            
        } else
        {
            $('#objectsTarget_'+ lastPrefix).hide();
        }

    });
}
// --------------------------------------------------------
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
dbIndexes = ''

function purgeAllExecute() {

    // Execute
    // console.log("targetLogFile:" + targetLogFile)
    // console.log("logFileAction:" + logFileAction)

    idArr = $('#NMAPSRV table[data-my-dbtable="Plugins_Objects"] tr[data-my-index]').map(function(){return $(this).attr("data-my-index");}).get();

    $.ajax({
        method: "POST",
        url: "php/server/dbHelper.php",
        data: { action: "delete", dbtable: 'Plugins_Objects', key: 'Index', id:idArr.toString() },
        success: function(data, textStatus) {
            showModalOk ('Result', data );
        }
    })

}


// -----------------------------------------------------------------------------

getData()

</script>



