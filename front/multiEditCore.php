<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>

<div class="col-md-12">
    <div class="callout callout-warning">
      <h4><?= lang('Gen_Warning');?></h4>

      <p><?= lang('Device_MultiEdit_Backup');?></p>
    </div>
    <div class="box box-default">

      <div class="box-header">

        <h3 class="box-title"><?= lang('Gen_Selected_Devices');?></h3>

      </div>
    <div class="deviceSelector col-md-11 col-sm-11" style="z-index:5"></div> 

    <div class="col-md-1"> 
      <button type="button" class="btn btn-default col-md-12" onclick="markAllSelected()" title="<?= lang('Gen_Add_All');?>"> 
        <i class="fa-solid fa-circle-check"></i>  
      </button>
      <button type="button" class="btn btn-default col-md-12"  onclick="markAllNotSelected()" title="<?= lang('Gen_Remove_All');?>"> 
        <i class="fa-solid fa-circle-xmark"></i>  
      </button>
    </div>


  </div>


<div class="col-md-12">
    <div class="box box-default">

      <div class="box-header">
        <h3 class="box-title"><?= lang('Device_MultiEdit_Fields');?></h3>
      </div>
      <div class="box-body">
        <form id="multi-edit-form">
          <!-- Form fields will be appended here -->
        </form>
      </div>
    </div>
  </div>
</div>


  <div class="col-md-12">
    <div class="box box-default">
      <div class="box-header ">
        <h3 class="box-title"><?= lang('Device_MultiEdit_MassActions');?></h3>
      </div>
      <div class="box-body">

          <div class="col-md-2" style="">
              <button type="button" class="btn btn-default pa-btn pa-btn-delete bg-red" id="btnDeleteMAC" onclick="askDeleteSelectedDevices()"><?= lang('Maintenance_Tool_del_selecteddev');?></button>
          </div>
          <div class="col-md-10"><?= lang('Maintenance_Tool_del_selecteddev_text');?></div>

      </div>
    </div>
  </div>


<script defer>
  
  // -------------------------------------------------------------------  
  // Get plugin and settings data from API endpoints
  function getData(){

    // some race condition, need to implement delay
    setTimeout(() => {
      $.get('php/server/query_json.php', { file: 'table_settings.json', nocache: Date.now() }, function(res) {    
        
        settingsData = res["data"];

        excludedColumns = ["NEWDEV_devMac", "NEWDEV_devFirstConnection", "NEWDEV_devLastConnection", "NEWDEV_devLastNotification", "NEWDEV_devScan", "NEWDEV_devPresentLastScan", "NEWDEV_devCustomProps", "NEWDEV_devChildrenNicsDynamic", "NEWDEV_devChildrenDynamic" ]
        
        const relevantColumns = settingsData.filter(set =>
            set.setGroup === "NEWDEV" &&
            set.setKey.includes("_dev") &&
            !excludedColumns.includes(set.setKey) &&
            !set.setKey.includes("__metadata")
        );

        const generateSimpleForm = multiEditColumns => {
            const form = $('#multi-edit-form');
            const numColumns = 2; // Number of columns

            // Calculate number of elements per column
            const elementsPerColumn = Math.ceil(multiEditColumns.length / numColumns);

            // Divide columns equally
            for (let i = 0; i < numColumns; i++) {
                const column = $('<div>').addClass('col-md-6');

                // Append form groups to the column
                for (let j = i * elementsPerColumn; j < Math.min((i + 1) * elementsPerColumn, multiEditColumns.length); j++) {

                  const setTypeObject  = JSON.parse(multiEditColumns[j].setType.replace(/'/g, '"'));         

                  // get the element with the input value(s)
                  let elements = setTypeObject.elements.filter(element => element.elementHasInputValue === 1);

                  //  if none found, take last
                  if(elements.length == 0)
                  {
                    elementWithInputValue = setTypeObject.elements[setTypeObject.elements.length - 1]
                  } else
                  {
                    elementWithInputValue = elements[0]
                  }

                  const { elementType, elementOptions = [], transformers = [] } = elementWithInputValue;
                  const { 
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
                    customId,
                    columns,
                    base64Regex
                  } = handleElementOptions('none', elementOptions, transformers, val = "");

                  //  render based on element type 
                  if (elementType === 'select') {

                    targetLocation = multiEditColumns[j].setKey + "_generateSetOptions"

                    generateOptionsOrSetOptions(multiEditColumns[j].setKey, [], targetLocation, generateOptions, null)

                    console.log(multiEditColumns[j].setKey)
                    //  Handle Icons as they need a preview                 
                    if(multiEditColumns[j].setKey == 'NEWDEV_devIcon')
                    {
                      input = `
                            <span class="input-group-addon iconPreview" my-customid="NEWDEV_devIcon_preview"></span>
                            <select  class="form-control"
                                      onChange="updateIconPreview(this)"
                                      my-customparams="NEWDEV_devIcon,NEWDEV_devIcon_preview"
                                      id="${multiEditColumns[j].setKey}"
                                      data-my-column="${multiEditColumns[j].setKey}" 
                                      data-my-targetColumns="${multiEditColumns[j].setKey.replace('NEWDEV_','')}" >
                              <option id="${targetLocation}"></option>
                            </select>`
                      
                    } else{                      

                      input = `<select  class="form-control"
                                      id="${multiEditColumns[j].setKey}"
                                      data-my-column="${multiEditColumns[j].setKey}" 
                                      data-my-targetColumns="${multiEditColumns[j].setKey.replace('NEWDEV_','')}" >
                              <option id="${targetLocation}"></option>
                            </select>`
                    }


                  } else if (elementType === 'input'){ 
                    
                    // Add classes specifically for checkboxes
                    inputType === 'checkbox' ?  inputClass = 'checkbox' : inputClass = 'form-control';
                    

                    input =  `<input  class="${inputClass}" 
                                      id="${multiEditColumns[j].setKey}"  
                                      my-customid="${multiEditColumns[j].setKey}"  
                                      data-my-column="${multiEditColumns[j].setKey}" 
                                      data-my-targetColumns="${multiEditColumns[j].setKey.replace('NEWDEV_','')}" 
                                      type="${inputType}">`
                  }

          
                  const inputEntry  = `<div class="form-group col-sm-12" >
                                          <label class="col-sm-3 control-label">${multiEditColumns[j].setName}</label>
                                          <div class="col-sm-9">
                                            <div class="input-group red-hover-border">
                                              ${input}
                                              <span class="input-group-addon pointer red-hover-background" onclick="massUpdateField('${multiEditColumns[j].setKey}');" title="${getString('Device_MultiEdit_Tooltip')}">
                                                <i class="fa fa-save"></i>
                                              </span>
                                            </div>
                                          </div>
                                        </div>`

                  
                  column.append(inputEntry);
                }

                form.append(column);
            }
        };

        console.log(relevantColumns)

        generateSimpleForm(relevantColumns);

        
    })
      
    }, 500);
    
  }


  // -----------------------------------------------------------------------------
  // Get selected devices Macs
  function selectorMacs () {
    return $('.deviceSelector select').val().join(',');
  }

  // -----------------------------------------------------------------------------
  // Select All
  function markAllSelected() {
    // Get the <select> element with the class 'deviceSelector'
    var selectElement = $('.deviceSelector select');
    
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
  function markAllNotSelected() {
    // Get the <select> element with the class 'deviceSelector'
    var selectElement = $('.deviceSelector select');
    
    // Iterate over each option within the select element
    selectElement.find('option').each(function() {
      // Unselect each option
      $(this).prop('selected', false);
    });
    
    // Trigger the 'change' event to notify Bootstrap Select of the changes
    selectElement.trigger('change');
  }



  // -----------------------------------------------------------------------------
  // Update specified field over the specified DB column and selected entry(ies)
  function massUpdateField(id) {

    // Get the input element
    var inputElement = $(`#${id}`);

    console.log(inputElement);
    console.log(id);

    // Initialize columnValue variable
    var columnValue;

    // Check the type of the input element
    if (inputElement.is(':checkbox')) {
        // For checkboxes, set the value to 1 if checked, otherwise set it to 0
        columnValue = inputElement.is(':checked') ? 1 : 0;
    } else {
        // For other input types (like textboxes), simply retrieve their values
        columnValue = encodeURIComponent(inputElement.val());
    }

    var targetColumns = inputElement.attr('data-my-targetColumns');


    console.log(targetColumns);
    console.log(columnValue);

    // update selected
    executeAction('update', 'devMac', selectorMacs(), targetColumns, columnValue )

    
}

// -----------------------------------------------------------------------------
// action: Represents the action to be performed, a CRUD operation like "update", "delete", etc.
// whereColumnName: Specifies the name of the column used in the WHERE or SELECT statement for filtering.
// key: Represents the unique identifier of the row or record to be acted upon.
// targetColumns: Indicates the columns to be updated or affected by the action.
// newTargetColumnValue: Specifies the new value to be assigned to the specified column(s).
function executeAction(action, whereColumnName, key, targetColumns, newTargetColumnValue )
{
  $.get(`php/server/dbHelper.php?action=${action}&dbtable=Devices&columnName=${whereColumnName}&id=${key}&columns=${targetColumns}&values=${newTargetColumnValue}`, function(data) {
        // console.log(data);

        if (sanitize(data) == 'OK') {
            showMessage(getString('Gen_DataUpdatedUITakesTime'));
            // Remove navigation prompt "Are you sure you want to leave..."
            window.onbeforeunload = null;

            // update API endpoints to refresh the UI
            updateApi("devices,appevents")

            write_notification(`[Multi edit] Executed "${action}" on Columns "${targetColumns}" matching "${key}"`, 'info')

        } else {
            showMessage(getString('Gen_LockedDB'));
        }
    });
}


// -----------------------------------------------------------------------------
// Ask to delete selected devices 
function askDeleteSelectedDevices () {
  // Ask 
  showModalWarning(
    getString('Maintenance_Tool_del_alldev_noti'), 
    getString('Gen_AreYouSure'),
    getString('Gen_Cancel'), 
    getString('Gen_Delete'), 
    'deleteSelectedDevices');
}

// -----------------------------------------------------------------------------
// Delete selected devices 
function deleteSelectedDevices()
{ 
  macs_tmp = selectorMacs()
  executeAction('delete', 'devMac', macs_tmp )
  write_notification('[Multi edit] Manually deleted devices with MACs:' + macs_tmp, 'info')
}


getData();


</script>

<!-- ----------------------------------------------------------------------- -->

<!-- ----------------------------------------------------------------------- -->


