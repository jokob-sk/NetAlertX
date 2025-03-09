<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>


<section class="content workflows">
  <div id="workflowContainerWrap" class="bg-grey-dark color-palette  col-sm-12  box-default box-info ">
    <div id="workflowContainer"></div>
    
  </div>
  <div id="buttons" class="buttons col-sm-12">
    <div class="add-workflow col-sm-6">
      <button type="button" class="btn btn-primary btn-default pa-btn bg-green" id="save" onclick="addWorkflow()">
        <?= lang('Gen_Add');?>
      </button>
    </div>
    <div class="save-workflows col-sm-6">
      <button type="button" class="btn btn-primary btn-default pa-btn bg-green" id="save" onclick="saveWorkflows()">
        <?= lang('DevDetail_button_Save');?>
      </button>
    </div>
  </div>
</section>


<script>

let workflows = [];

let fieldOptions = [
        "devMac", "devName", "devOwner", "devType", "devVendor", "devFavorite",
        "devGroup", "devComments", "devFirstConnection", "devLastConnection",
        "devLastIP", "devStaticIP", "devScan", "devLogEvents", "devAlertEvents",
        "devAlertDown", "devSkipRepeated", "devLastNotification", "devPresentLastScan",
        "devIsNew", "devLocation", "devIsArchived", "devParentMAC", "devParentPort",
        "devIcon", "devGUID", "devSite", "devSSID", "devSyncHubNode", "devSourcePlugin"
      ];
      
let triggerTypes = [
  "Devices", "Plugins_Objects"
];

let operatorTypes = [
  "equals", "contains" , "regex"
];

let actionTypes = [
  "update_field", "run_plugin"
];

// --------------------------------------
// Retrieve and process the data
function getData() {
  showSpinner();

  getSetting()

  $.get('php/server/query_json.php?file=workflows.json', function (res) {
    workflows = res;
    console.log(workflows);
    renderWorkflows();
    hideSpinner();
  });
}

// --------------------------------------
// Render all workflows
function renderWorkflows() {
  let $container = $("#workflowContainer");
  $container.empty(); // Clear previous UI

  $.each(workflows, function (index, wf) {
    let $wfElement = generateWorkflowUI(wf, index);
    $container.append($wfElement);
  });
}


// --------------------------------------
// Generate UI for a single workflow
function generateWorkflowUI(wf, index) {

  let $wfContainer = $("<div>", { 
    class: "workflow-card box box-solid box-primary panel panel-default", 
    id: `wf-${index}-container` 
  });

  // Workflow Name
  let $wfLinkWrap = $("<div>",
    {
      class: " ",
      id: `wf-${index}-header` 
    }
  )

  let $wfHeaderLink = $("<a>",
    {
      "class": "",
      "data-toggle": "collapse",
      "data-parent": "#workflowContainer",
      "aria-expanded": false,
      "href" : `#wf-${index}-collapsible-panel`
    }
  )

  let $wfHeaderHeading = $("<h4>",
    {
      class: "panel-title"    
    }
  ).text(wf.name)

  $wfContainer.append($wfHeaderLink.append($wfLinkWrap.append($wfHeaderHeading)));

  // Collapsible panel start
  let $wfCollapsiblePanel = $("<div>", { 
    class: "panel-collapse collapse ", 
    id: `wf-${index}-collapsible-panel` 
  });

  let $wfNameInput = createEditableInput("Workflow name", wf.name, `wf-name-${index}`, "workflow-name-input", function(newValue) {
    console.log(`Saved new value: ${newValue}`);
    wf.name = newValue; // Update the workflow object with the new name
  });

  $wfCollapsiblePanel.append($wfNameInput)

  // Trigger Section with dropdowns
  let $triggerSection = $("<div>",
    {
      class: "condition-list box  box-secondary"
    }
  ).append("<strong>Trigger:</strong> ");

  let $triggerTypeDropdown = createEditableDropdown("Trigger Type", triggerTypes, wf.trigger.object_type, `trigger-${index}-type`, function(newValue) {
    wf.trigger.object_type = newValue; // Update trigger's object_type
  });

  let $eventTypeDropdown = createEditableDropdown("Event Type", ["update", "create", "delete"], wf.trigger.event_type, `event-${index}-type`, function(newValue) {
    wf.trigger.event_type = newValue; // Update trigger's event_type
  });

  $triggerSection.append($triggerTypeDropdown);
  $triggerSection.append($eventTypeDropdown);
  $wfCollapsiblePanel.append($triggerSection);

  // Conditions
  let $conditionsContainer = $("<div>").append("<strong>Conditions:</strong>");
  $conditionsContainer.append(renderConditions(wf.conditions));
  
  $wfCollapsiblePanel.append($conditionsContainer);


  // Actions with action.field as dropdown
  let $actionsContainer = $("<div>",
    {
      class: "actions-list box  box-secondary"
    }
  ).append("<strong>Actions:</strong>");

  $.each(wf.actions, function (_, action) {
    let $actionEl = $("<div>");

    // Dropdown for action.field
    let $fieldDropdown = createEditableDropdown("Field", fieldOptions, action.field, `action-${index}-field`, function(newValue) {
      action.field = newValue; // Update action.field when a new value is selected
    });


    // Dropdown for action.type
    let $actionDropdown= createEditableDropdown("Action", actionTypes, action.field, `action-${index}-type`, function(newValue) {
      action.field = newValue; // Update action.field when a new value is selected
    });


    // Action Value Input (Editable)
    let $actionValueInput = createEditableInput("Value", action.value, `action-${index}-value`, "action-value-input", function(newValue) {
      action.value = newValue; // Update action.value when saved
    });

    $actionEl.append($actionDropdown);
    $actionEl.append($fieldDropdown);
    $actionEl.append($actionValueInput);

    $actionsContainer.append($actionEl);
  });

  // add conditions group button
  let $actionAddButton = $("<button>", {
      class : "btn btn-secondary "
    }).text("Add Action")

  $actionsContainer.append($actionAddButton)
  $wfCollapsiblePanel.append($actionsContainer);

  $wfContainer.append($wfCollapsiblePanel)

  return $wfContainer;
}


// --------------------------------------
// Render conditions recursively
function renderConditions(conditions) {
  let $conditionList = $("<div>", { 
    class: "condition-list panel " 
  });

  $.each(conditions, function (index, condition) {
    if (condition.logic) {
      let $nestedCondition = $("<div>",
        {
          class : "condition box  box-secondary"
        }
      );

      let $logicDropdown = createEditableDropdown("Logic Rules", ["AND", "OR"], condition.logic, `logic-${condition.field}`, function(newValue) {
        condition.logic = newValue; // Update condition logic when a new value is selected
      });

      $nestedCondition.append($logicDropdown);

      $conditionListNested = renderConditions(condition.conditions) 


      // add conditions group button
      let $conditionAddButton = $("<button>", {
        class : "btn btn-secondary "
      }).text("Add Condition")

      $conditionListNested.append($conditionAddButton);
      $nestedCondition.append($conditionListNested); // Recursive call for nested conditions

      $conditionList.append($nestedCondition);
      
    } else {
      let $conditionItem = $("<div>",
      {
        class: "panel"
      });

      // Create dropdown for condition field
      let $fieldDropdown = createEditableDropdown("Field", fieldOptions, condition.field, `condition-${index}-field-${condition.field}`, function(newValue) {
        condition.field = newValue; // Update condition field when a new value is selected
      });

      // Create dropdown for operator
      let $operatorDropdown = createEditableDropdown("Operator", operatorTypes, condition.operator, `condition-${index}operator-${condition.field}`, function(newValue) {
        condition.operator = newValue; // Update operator when a new value is selected
      });

      // Editable input for condition value
      let $editableInput = createEditableInput("Condition Value", condition.value, `condition-${index}-value-${condition.field}`, "condition-value-input", function(newValue) {
        condition.value = newValue; // Update condition value when saved
      });

      $conditionItem.append($fieldDropdown); // Append field dropdown
      $conditionItem.append($operatorDropdown); // Append operator dropdown
      $conditionItem.append($editableInput); // Append editable input for condition value
      $conditionList.append($conditionItem);

      
    }
  });

  // add conditions group button
  let $conditionsGroupAddButton = $("<button>", {
    class : "btn btn-secondary"
  }).text("Add Condition Group")

  $conditionList.append($conditionsGroupAddButton);


  return $conditionList;
}


// --------------------------------------
// Render SELECT Dropdown with Predefined Values
function createEditableDropdown(labelText, options, selectedValue, id, onSave) {

  let $wrapper = $("<div>", {
    class: "form-group col-xs-12"
  });

  let $label = $("<label>", {   
    for: id, 
    class: "col-sm-4 col-xs-12 control-label "
  }).text(labelText);

  // Create select wrapper
  let $selectWrapper = $("<div>", {
    class: "col-sm-8 col-xs-12"
  });

  // Create select element
  let $select = $("<select>", {
    id: id,
    class: "form-control col-sm-8 col-xs-12"
  });

  // Add options to the select dropdown
  $.each(options, function (_, option) {
    let $option = $("<option>", { value: option }).text(option);
    if (option === selectedValue) {
      $option.attr("selected", "selected"); // Set the default selection
    }
    $select.append($option);
  });

  // Trigger onSave when the selection changes
  $select.on("change", function() {
    let newValue = $select.val();
    console.log(`Selected new value: ${newValue}`);
    if (onSave && typeof onSave === "function") {
      onSave(newValue); // Call onSave callback with the new value
    }
  });

  $wrapper.append($label);
  $wrapper.append($selectWrapper.append($select));
  return $wrapper;
}



// --------------------------------------
// Render INPUT HTML element
function createEditableInput(labelText, value, id, className = "", onSave = null) {

  // prepare wrapper
  $wrapper = $("<div>", {
    class: "form-group col-xs-12"
  });

  let $label = $("<label>", {   
    for: id, 
    class: "col-sm-4 col-xs-12 control-label "
  }).text(labelText);

  // Create input wrapper
  let $inputWrapper = $("<div>", {
    class: "col-sm-8 col-xs-12"
  });


  let $input = $("<input>", {
    type: "text",
    id: id,
    value: value,
    class: className + " col-sm-8 col-xs-12 form-control "
  });

  // Optional: Add a change event listener to update the workflow name
  $input.on("change", function () {
    let newValue = $input.val();
    console.log(`Value changed to: ${newValue}`);
  });

  // Trigger onSave when the user presses Enter or the input loses focus
  $input.on("blur keyup", function (e) {
    if (e.type === "blur" || e.key === "Enter") {
      if (onSave && typeof onSave === "function") {
        onSave($input.val()); // Call the onSave callback with the new value
      }
    }
  });

  $wrapper.append($label)
  $wrapper.append($inputWrapper.append($input))
  return $wrapper;
}




// --------------------------------------
// Initialize
$(document).ready(function () {
  getData();
});


</script>