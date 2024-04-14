



<div class="col-md-12">
    <div class="box box-default">

      <div class="box-header">

        <h3 class="box-title"><?= lang('Gen_Selected_Devices');?></h3>

        </div>
    <div class="deviceSelector"></div>

    <div class="callout callout-warning">
      <h4><?= lang('Gen_Warning');?></h4>

      <p><?= lang('Device_MultiEdit_Backup');?></p>
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

</div>




<script defer>
  
  // -------------------------------------------------------------------  
  // Get plugin and settings data from API endpoints
  function getData(){

    $.get('api/table_settings.json?nocache=' + Date.now(), function(res) {    
        
        settingsData = res["data"];

        excludedColumns = ["NEWDEV_dev_MAC", "NEWDEV_dev_FirstConnection", "NEWDEV_dev_LastConnection", "NEWDEV_dev_LastNotification", "NEWDEV_dev_LastIP", "NEWDEV_dev_StaticIP", "NEWDEV_dev_ScanCycle", "NEWDEV_dev_PresentLastScan" ]
        
        const relevantColumns = settingsData.filter(set =>
            set.Group === "NEWDEV" &&
            set.Code_Name.includes("_dev_") &&
            !excludedColumns.includes(set.Code_Name) &&
            !set.Code_Name.includes("__metadata")
        );

        const generateSimpleForm = columns => {
            const form = $('#multi-edit-form');
            const numColumns = 2; // Number of columns

            // Calculate number of elements per column
            const elementsPerColumn = Math.ceil(columns.length / numColumns);

            // Divide columns equally
            for (let i = 0; i < numColumns; i++) {
                const column = $('<div>').addClass('col-md-6');

                // Append form groups to the column
                for (let j = i * elementsPerColumn; j < Math.min((i + 1) * elementsPerColumn, columns.length); j++) {

                  let inputType;

                  switch (columns[j].Type) {
                    case 'integer.checkbox':
                    case 'checkbox':
                      inputType = 'checkbox';
                      break;
                    case 'text.select':
                      inputType = 'text.select';
                      break;
                    default:
                      inputType = 'text';
                      break;
                  }                    
                  
                  if (inputType === 'text.select') {

                    targetLocation = columns[j].Code_Name + "_initSettingDropdown"

                    initSettingDropdown(columns[j].Code_Name, [], targetLocation, generateDropdownOptions)

                    //  Handle Icons as tehy need a preview                 
                    if(columns[j].Code_Name == 'NEWDEV_dev_Icon')
                    {
                      input = `
                            <span class="input-group-addon" id="txtIconFA"></span>
                            <select  class="form-control"
                                      onChange="updateIconPreview('#NEWDEV_dev_Icon')"
                                      id="${columns[j].Code_Name}"
                                      data-my-column="${columns[j].Code_Name}" 
                                      data-my-targetColumns="${columns[j].Code_Name.replace('NEWDEV_','')}" >
                              <option id="${targetLocation}"></option>
                            </select>`
                      
                    } else{                      

                      input = `<select  class="form-control"
                                      id="${columns[j].Code_Name}"
                                      data-my-column="${columns[j].Code_Name}" 
                                      data-my-targetColumns="${columns[j].Code_Name.replace('NEWDEV_','')}" >
                              <option id="${targetLocation}"></option>
                            </select>`
                    }


                  } else { 
                    
                    // Add classes specifically for checkboxes
                    if (inputType === 'checkbox') {
                      inputClass = 'checkbox';
                  
                    } else {
                      inputClass = 'form-control';
                    }

                    input =  `<input  class="${inputClass}" 
                                      id="${columns[j].Code_Name}"  
                                      data-my-column="${columns[j].Code_Name}" 
                                      data-my-targetColumns="${columns[j].Code_Name.replace('NEWDEV_','')}" 
                                      type="${inputType}">`
                  }

          
                  const inputEntry  = `<div class="form-group col-sm-12" >
                                          <label class="col-sm-3 control-label">${columns[j].Display_Name}</label>
                                          <div class="col-sm-9">
                                            <div class="input-group red-hover-border">
                                              ${input}
                                              <span class="input-group-addon pointer red-hover-background" onclick="massUpdateField('${columns[j].Code_Name}');" title="${getString('Device_MultiEdit_Tooltip')}">
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
  }


  // -----------------------------------------------------------------------------
  // Get selected devices Macs
  function selectorMacs () {
    return $('.deviceSelector select').val().join(',');
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
        columnValue = inputElement.val();
    }

    var targetColumns = inputElement.attr('data-my-targetColumns');


    console.log(targetColumns);
    console.log(columnValue);

    // update selected
    executeAction('update', 'dev_MAC', selectorMacs(), targetColumns, columnValue )

    
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
            updateApi()

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
  
  executeAction('delete', 'dev_MAC', selectorMacs() )

}


getData();


</script>

<!-- ----------------------------------------------------------------------- -->
<script src="js/ui_components.js"></script>
<script src="js/db_methods.js"></script>
<!-- ----------------------------------------------------------------------- -->


