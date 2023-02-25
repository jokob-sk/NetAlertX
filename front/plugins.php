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
        <div class="nav-tabs-custom" style="margin-bottom: 0px;">
            <ul id="tabs-location" class="nav nav-tabs">
                <!-- PLACEHOLDER -->
            </ul>  
        <div id="tabs-content-location" class="nav nav-tabs"> 
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

function getData(){

    $.get('api/plugins.json', function(res) {    
        
        pluginDefinitions = res["data"];

        $.get('api/table_plugins_events.json', function(res) {

            pluginUnprocessedEvents = res["data"];

            $.get('api/table_plugins_objects.json', function(res) {

                pluginObjects = res["data"];

                generateTabs()

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
            `<li class="${activetab}">
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

        // Generate the header
        $.each(obj["database_column_definitions"], function(index, colDef){
            if(colDef.show == true) // select only the ones to show
            {
                colDefinitions.push(colDef)            
                headersHtml += `<th class="col-sm-2" >${localize(colDef, "name" )}</th>`
            }
        });



        // Generate the event rows
        for(i=0;i<pluginUnprocessedEvents.length;i++)
        {
            if(pluginUnprocessedEvents[i].Plugin == obj.unique_prefix)
            {
                clm = ""

                for(j=0;j<colDefinitions.length;j++) 
                {   
                    clm += '<td>'+ pluginUnprocessedEvents[i][colDefinitions[j].column] +'</td>'
                }                   
                evRows += '<tr>' + clm + '</tr>'
            }            
        }

        

        // Generate the object rows
        for(i=0;i<pluginObjects.length;i++)
        {
            if(pluginObjects[i].Plugin == obj.unique_prefix)
            {
                clm = ""

                for(j=0;j<colDefinitions.length;j++) 
                {   
                    
                    clm += '<td>'+ getFormControl(colDefinitions[j], pluginObjects[i][colDefinitions[j].column], pluginObjects[i]["Index"]) +'</td>'
                }                   
                obRows += '<tr>' + clm + '</tr>'
            }            
        }


        $('#tabs-content-location').append(
            `    
            <div id="${obj.unique_prefix}" class="tab-pane ${activetab}">
                <div class="nav-tabs-custom" style="margin-bottom: 0px">
                    <ul class="nav nav-tabs">
                        <li class="active">
                            <a href="#objectsTarget" data-toggle="tab" >
                                
                                <i class="fa fa-cube"></i> <?= lang('Plugins_Objects');?> (${pluginObjects.length})
                                
                            </a>
                        </li>

                        <li>
                            <a href="#eventsTarget" data-toggle="tab" >
                                
                                <i class="fa fa-bolt"></i> <?= lang('Plugins_Unprocessed_Events');?> (${pluginUnprocessedEvents.length})
                                
                            </a>
                        </li>

                    <ul>
                </div>
                

                <div class="tab-content">

                    <div id="objectsTarget" class="tab-pane active">
                        <table class="table table-striped">                    
                            <tbody>
                                <tr>
                                    ${headersHtml}                            
                                </tr>  
                                ${obRows}
                            </tbody>
                        </table>
                    </div>
                    <div id="eventsTarget" class="tab-pane">
                        <table class="table table-striped">
                        
                            <tbody>
                                <tr>
                                    ${headersHtml}                            
                                </tr>  
                                ${evRows}
                            </tbody>
                        </table>
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
}

// -----------------------------------------------------------------------------

getData()

</script>



