<?= lang('Gen_Selected_Devices');?>

<div class="deviceSelector"></div>

<div class="callout callout-warning">
  <h4><?= lang('Gen_Warning');?></h4>

  <p><?= lang('Device_MultiEdit_Backup');?></p>
</div>



<div class="row">
  <div class="col-md-12">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title"><?= lang('Device_MultiEdit_Fields');?></h3>
      </div>
      <div class="card-body">
        <form id="multi-edit-form">
          <!-- Form fields will be appended here -->
        </form>
      </div>
    </div>
  </div>
</div>



<script>
  
  // -------------------------------------------------------------------  
  // Get plugin and settings data from API endpoints
  function getData(){

    $.get('api/table_settings.json?nocache=' + Date.now(), function(res) {    
        
        settingsData = res["data"];

        excludedColumns = ["NEWDEV_dev_MAC", "NEWDEV_dev_FirstConnection", "NEWDEV_dev_LastConnection", "dev_LastNotification", "NEWDEV_dev_LastIP", "NEWDEV_dev_StaticIP", "NEWDEV_dev_ScanCycle", "NEWDEV_dev_PresentLastScan" ]
        
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

                    const inputType = columns[j].Type === 'integer.checkbox' ? 'checkbox' : 'text';
                    
                    // Add classes specifically for checkboxes
                    if (inputType === 'checkbox') {
                        inputClass = 'checkbox';
                    } else {
                        inputClass = 'form-control';
                    }


                    const inputEntry  = `<div class="form-group col-sm-12" >
                                            <label class="col-sm-3 control-label">${columns[j].Display_Name}</label>
                                            <div class="col-sm-9">
                                              <div class="input-group red-hover-border">
                                                <input class="${inputClass}" id="${columns[j].Code_Name}"  data-my-column="${columns[j].Code_Name}" data-my-targetColumns="${columns[j].Code_Name.replace('NEWDEV_','')}" type="${inputType}">
                                                <span class="input-group-addon pointer red-hover-background" onclick="genericSaveData('${columns[j].Code_Name}', selectorMacs());" title="${getString('Device_MultiEdit_Tooltip')}">
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


        generateSimpleForm(relevantColumns);

        
    })
  }


  // -----------------------------------------------------------------------------
  // Get selected devices Macs
  function selectorMacs () {
    return $('.deviceSelector select').val().join(',');
  }


  // -----------------------------------------------------------------------------
  // Update the corresponding DB column and entry
  function genericSaveData(id, index) {

    // Get the input element
    var inputElement = $(`#${id}`);

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
    console.log(index);
    console.log(columnValue);

    $.get(`php/server/dbHelper.php?action=update&dbtable=Devices&columnName=dev_MAC&id=${index}&columns=${targetColumns}&values=${columnValue}`, function(data) {
        console.log(data);

        if (sanitize(data) == 'OK') {
            showMessage('<?= lang('Gen_DataUpdatedUITakesTime');?>');
            // Remove navigation prompt "Are you sure you want to leave..."
            window.onbeforeunload = null;

            // update API endpoints to refresh the UI
            updateApi()

        } else {
            showMessage('<?= lang('Gen_LockedDB');?>');
        }
    });
}


  getData();


  </script>


<!-- ----------------------------------------------------------------------- -->
<script src="js/ui_components.js"></script>