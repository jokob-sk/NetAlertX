// -----------------------------------------------------------------------------
// Modal dialog handling
// -----------------------------------------------------------------------------
var modalCallbackFunction = "";

function showModalOK(title, message, callbackFunction) {
  showModalOk(title, message, callbackFunction);
}
function showModalOk(title, message, callbackFunction) {
  // set captions
  $("#modal-ok-title").html(title);
  $("#modal-ok-message").html(message);

  if (callbackFunction != null) {
    $("#modal-ok-OK").click(function () {
      callbackFunction();
    });
  }

  // Show modal
  $("#modal-ok").modal("show");
}

// -----------------------------------------------------------------------------
function showModalDefault(title, message, btnCancel, btnOK, callbackFunction) {
  // set captions
  $("#modal-default-title").html(title);
  $("#modal-default-message").html(message);
  $("#modal-default-cancel").html(btnCancel);
  $("#modal-default-OK").html(btnOK);
  modalCallbackFunction = callbackFunction;

  // Show modal
  $("#modal-default").modal("show");
}

// -----------------------------------------------------------------------------

function showModalDefaultStrParam(
  title,
  message,
  btnCancel,
  btnOK,
  callbackFunction,
  param = ""
) {
  // set captions
  $("#modal-str-title").html(title);
  $("#modal-str-message").html(message);
  $("#modal-str-cancel").html(btnCancel);
  $("#modal-str-OK").html(btnOK);
  $("#modal-str-OK").off("click"); //remove existing handlers
  $("#modal-str-OK").on("click", function () {
    $("#modal-str").modal("hide");
    callbackFunction(param);
  });

  // Show modal
  $("#modal-str").modal("show");
}

// -----------------------------------------------------------------------------
function showModalWarning(
  title,
  message,
  btnCancel = getString("Gen_Cancel"),
  btnOK = getString("Gen_Okay"),
  callbackFunction = null,
  triggeredBy = null
) {
  prefix = "modal-warning";

  // set captions
  $(`#${prefix}-title`).html(title);
  $(`#${prefix}-message`).html(message);
  $(`#${prefix}-cancel`).html(btnCancel);
  $(`#${prefix}-OK`).html(btnOK);

  if (callbackFunction != null) {
    modalCallbackFunction = callbackFunction;
  }

  if (triggeredBy != null) {
    $('#'+prefix).attr("data-myparam-triggered-by", triggeredBy)
  }

  // Show modal
  $(`#${prefix}`).modal("show");
}

// -----------------------------------------------------------------------------
function showModalInput(
  title,
  message,
  btnCancel = getString("Gen_Cancel"),
  btnOK = getString("Gen_Okay"),
  callbackFunction = null,
  triggeredBy = null,
  defaultValue = ""  
) {
  prefix = "modal-input";

  // set captions
  $(`#${prefix}-title`).html(title);
  $(`#${prefix}-message`).html(message);
  $(`#${prefix}-cancel`).html(btnCancel);
  $(`#${prefix}-OK`).html(btnOK);
  $(`#${prefix}-textarea`).val(defaultValue);

  if (callbackFunction != null) {
    modalCallbackFunction = callbackFunction;
  }

  if (triggeredBy != null) {
    $('#'+prefix).attr("data-myparam-triggered-by", triggeredBy)
  }

  // Show modal
  $(`#${prefix}`).modal("show");

  setTimeout(function () {
    $(`#${prefix}-textarea`).focus();
  }, 500);
  
}

// -----------------------------------------------------------------------------
function showModalFieldInput(
  title,
  message,
  btnCancel = getString("Gen_Cancel"),
  btnOK = getString("Gen_Okay"),
  curValue = "",
  callbackFunction = null,
  triggeredBy = null
) {
  // set captions
  prefix = "modal-field-input";

  $(`#${prefix}-title`).html(title);
  $(`#${prefix}-message`).html(message);
  $(`#${prefix}-cancel`).html(btnCancel);
  $(`#${prefix}-OK`).html(btnOK);

  if (callbackFunction != null) {
    
    modalCallbackFunction = callbackFunction;
  }

  if (triggeredBy != null) {
    $('#'+prefix).attr("data-myparam-triggered-by", triggeredBy)
  }

  $(`#${prefix}-field`).val(curValue);

  setTimeout(function () {
    $(`#${prefix}-field`).focus();
  }, 500);

  // Show modal
  $(`#${prefix}`).modal("show");
}

// -----------------------------------------------------------------------------
function showModalPopupForm(
  title,
  message,
  btnCancel = getString("Gen_Cancel"),
  btnOK = getString("Gen_Okay"),
  curValue = null,
  popupFormJson = null,
  parentSettingKey = null,
  triggeredBy = null
) {
  // set captions
  prefix = "modal-form";
  console.log(popupFormJson);

  $(`#${prefix}-title`).html(title);
  $(`#${prefix}-message`).html(message);
  $(`#${prefix}-cancel`).html(btnCancel);
  $(`#${prefix}-OK`).html(btnOK);

  // if curValue not null 

  if (curValue)
  {
    initialValues = JSON.parse(atob(curValue));    
  }

  outputHtml = "";

  if (Array.isArray(popupFormJson)) {
    popupFormJson.forEach((field, index) => {
        // You'll need to define these or map them from `field`
        const setKey = field.function || `field_${index}`;        
        const setName = getString(`${parentSettingKey}_popupform_${setKey}_name`);
        const labelClasses = "col-sm-2"; // example, or from your obj.labelClasses
        const inputClasses = "col-sm-10"; // example, or from your obj.inputClasses
        let initialValue = '';
        if (curValue && Array.isArray(initialValues)) {
          const match = initialValues.find(
            v => v[1] == setKey
          );
          if (match) {
            initialValue = match[3];
          }
        }

        const fieldOptionsOverride = field.type?.elements[0]?.elementOptions || [];        
        const setValue = initialValue;
        const setType = JSON.stringify(field.type); 
        const setEvents = field.events || [];  // default to empty array if missing
        const setObj = { setKey, setValue, setType, setEvents };

        // Generate the input field HTML
        const inputFormHtml = `
                              <div class="form-group col-xs-12">
                                  <label id="${setKey}_label" class="${labelClasses}"> ${setName}
                                      <i my-set-key="${parentSettingKey}_popupform_${setKey}"
                                          title="${getString("Settings_Show_Description")}" 
                                          class="fa fa-circle-info pointer helpIconSmallTopRight" 
                                          onclick="showDescriptionPopup(this)">
                                      </i>
                                  </label>
                                  <div class="${inputClasses}">
                                      ${generateFormHtml(
                                        null, // settingsData only required for datatables
                                        setObj, 
                                        null, 
                                        fieldOptionsOverride, 
                                        null
                                      )}
                                  </div>
                              </div>
                  `;

        // Append to result
        outputHtml += inputFormHtml;
    });
  }
  
  $(`#modal-form-plc`).html(outputHtml);

  // Bind OK button click event
  $(`#${prefix}-OK`).off("click").on("click", function() {
    let settingsArray = [];
    if (Array.isArray(popupFormJson)) {
        popupFormJson.forEach(field => {
            collectSetting(
                `${parentSettingKey}_popupform`, // prefix
                field.function,                  // setCodeName
                field.type,                      // setType (object)
                settingsArray
            );
        });
    }

    // Encode settings
    const jsonData = JSON.stringify(settingsArray);
    const encodedValue = btoa(jsonData);

    // Get label from the FIRST field (value in 4th column)
    const label = settingsArray[0][3]

    // Add new option to target select
    const selectId = parentSettingKey;

    // If triggered by an option, update it; otherwise append new
    if (triggeredBy && $(triggeredBy).is("option")) {
      // Update existing option
      $(triggeredBy)
        .attr("value", encodedValue)
        .text(label);
    } else {
      const newOption = $("<option class='interactable-option'></option>")
          .attr("value", encodedValue)
          .text(label);
  
      $("#" + selectId).append(newOption);
      initListInteractionOptions(newOption);
    }

    console.log("Collected popup form settings:", settingsArray);

    if (typeof modalCallbackFunction === "function") {
        modalCallbackFunction(settingsArray);
    }

    $(`#${prefix}`).modal("hide");
  });

  // Show modal
  $(`#${prefix}`).modal("show");
}

// -----------------------------------------------------------------------------
function modalDefaultOK() {
  // Hide modal
  $("#modal-default").modal("hide");

  // timer to execute function
  window.setTimeout(function () {
    if (typeof modalCallbackFunction === "function") {
      modalCallbackFunction(); // Direct call
    } else if (typeof modalCallbackFunction === "string" && typeof window[modalCallbackFunction] === "function") {
      window[modalCallbackFunction](); // Call via window
    } else {
      console.error("Invalid callback function");
    }
  }, 100);
}

// -----------------------------------------------------------------------------
function modalDefaultInput() {
  // Hide modal
  $("#modal-input").modal("hide");

  // timer to execute function
  window.setTimeout(function () {
    if (typeof modalCallbackFunction === "function") {
      modalCallbackFunction(); // Direct call
    } else if (typeof modalCallbackFunction === "string" && typeof window[modalCallbackFunction] === "function") {
      window[modalCallbackFunction](); // Call via window
    } else {
      console.error("Invalid callback function");
    }
  }, 100);
}

// -----------------------------------------------------------------------------
function modalDefaultFieldInput() {
  // Hide modal
  $("#modal-field-input").modal("hide");

  // timer to execute function
  window.setTimeout(function () {
    if (typeof modalCallbackFunction === "function") {
      modalCallbackFunction(); // Direct call
    } else if (typeof modalCallbackFunction === "string" && typeof window[modalCallbackFunction] === "function") {
      window[modalCallbackFunction](); // Call via window
    } else {
      console.error("Invalid callback function");
    }
  }, 100);
}

// -----------------------------------------------------------------------------
function modalWarningOK() {
  // Hide modal
  $("#modal-warning").modal("hide");

  // timer to execute function
  window.setTimeout(function () {
    if (typeof modalCallbackFunction === "function") {
      modalCallbackFunction(); // Direct call
    } else if (typeof modalCallbackFunction === "string" && typeof window[modalCallbackFunction] === "function") {
      window[modalCallbackFunction](); // Call via window
    } else {
      console.error("Invalid callback function: " + modalCallbackFunction);
    }
  }, 100);
}

// -----------------------------------------------------------------------------
function showMessage(textMessage = "", timeout = 3000, colorClass = "modal_green") {
  if (textMessage.toLowerCase().includes("error")) {
    // show error
    alert(textMessage);
  } else {
    // show temporary notification
    $("#notification_modal").removeClass();                         // remove all classes
    $("#notification_modal").addClass("alert alert-dimissible notification_modal");     // add default ones
    $("#notification_modal").addClass(colorClass);                     // add color modifiers

    // message
    $("#alert-message").html(textMessage);

    // timeout
    $("#notification_modal").fadeIn(1, function () {
      window.setTimeout(function () {
        $("#notification_modal").fadeOut(500);
      }, timeout);
    });
  }
}

// -----------------------------------------------------------------------------
function showTickerAnnouncement(textMessage = "") {
  if (textMessage.toLowerCase().includes("error")) {
    // show error
    alert(textMessage);
  } else {
    // show permanent notification
    $("#ticker-message").html(textMessage);
    $("#tickerAnnouncement").removeClass("myhidden");
    // Move the tickerAnnouncement element to ticker_announcement_plc
    $("#tickerAnnouncement").appendTo("#ticker_announcement_plc");
  }
}

// -----------------------------------------------------------------------------
// Keyboard bindings
// -----------------------------------------------------------------------------

$(document).ready(function () {
  $(document).on("keydown", function (event) {
    // ESC key is pressed
    if (event.keyCode === 27) {
      // Trigger modal dismissal
      $(".modal").modal("hide");
    }

    // Enter key is pressed
    if (event.keyCode === 13) {
      $(".modal:visible").find(".btn-modal-submit").click(); // Trigger the click event of the OK button in visible modals
    }
  });
});


// -----------------------------------------------------------------------------
// Escape text
function safeDecodeURIComponent(content) {
  try {
    return decodeURIComponent(content);
  } catch (error) {
    console.warn('Failed to decode URI component:', error);
    return content;  // Return the original content if decoding fails
  }
  }
  

// -----------------------------------------------------------------------------
// Backend notification Polling 
// -----------------------------------------------------------------------------
// Function to check for notifications
function checkNotification() {
  const notificationEndpoint = 'php/server/utilNotification.php?action=get_unread_notifications';
  const phpEndpoint = 'php/server/utilNotification.php';

  $.ajax({
    url: notificationEndpoint, 
    type: 'GET',
    success: function(response) {
      // console.log(response);

      if(response != "[]")
      {
        // Find the oldest unread notification with level "interrupt"
        const oldestInterruptNotification = response.find(notification => notification.read === 0 && notification.level === "interrupt");
        const allUnreadNotification = response.filter(notification => notification.read === 0 && notification.level === "alert");

        if (oldestInterruptNotification) {
          // Show modal dialog with the oldest unread notification

          console.log(oldestInterruptNotification.content);

          const decodedContent = safeDecodeURIComponent(oldestInterruptNotification.content);

          // only check and display modal if no modal currently displayed to prevent looping
          if($("#modal-ok").is(":visible") == false)
          {
            showModalOK("Notification", decodedContent, function() {
              // Mark the notification as read
              $.ajax({
                url: phpEndpoint,
                type: 'GET',
                data: {
                  action: 'mark_notification_as_read',
                  guid: oldestInterruptNotification.guid
                },
                success: function(response) {
                  console.log(response);
                  // After marking the notification as read, check for the next one
                  checkNotification();
                  hideSpinner();
                },
                error: function(xhr, status, error) {
                  console.error("Error marking notification as read:", status, error);
                },
                complete:function() {
                  hideSpinner();
                }
              });
            });
          }
        }

        handleUnreadNotifications(allUnreadNotification.length)
      }
    },
    error: function() {
      console.warn(`🟥 Error checking ${notificationEndpoint}`)
      
    }
  });
}

// Handling unread notifications favicon + bell floating number bublbe
function handleUnreadNotifications(count) {
  $('#unread-notifications-bell-count').html(count);
  if (count > 0) {
    $('#unread-notifications-bell-count').show();
    // Change the favicon to show there are notifications
    $('#favicon').attr('href', 'img/NetAlertX_logo_notification.png');
    // Update the title to include the count
    document.title = `(${count}) ` + originalTitle;
  } else {
    $('#unread-notifications-bell-count').hide();
    // Change the favicon back to the original
    $('#favicon').attr('href', 'img/NetAlertX_logo.png');
    // Revert the title to the original title
    document.title = originalTitle;
  }
}

// Store the original title of the document
var originalTitle = document.title;


// Start checking for notifications periodically
setInterval(checkNotification, 3000);

// --------------------------------------------------
// User notification handling methods
// --------------------------------------------------

const phpEndpoint = 'php/server/utilNotification.php';

// --------------------------------------------------
// Write a notification
function write_notification(content, level) {  

  $.ajax({
    url: phpEndpoint, // Change this to the path of your PHP script
    type: 'GET',
    data: {
      action: 'write_notification',
      content: content,
      level: level
    },
    success: function(response) {
      console.log('Notification written successfully.');
    },
    error: function(xhr, status, error) {
      console.error('Error writing notification:', error);
    }
  });
}

// --------------------------------------------------
// Write a notification
function markNotificationAsRead(guid) {  
  
  $.ajax({
    url: phpEndpoint,
    type: 'GET',
    data: {
    action: 'mark_notification_as_read',
    guid: guid
    },
    success: function(response) {
    console.log(response);
    // Perform any further actions after marking the notification as read here
    showMessage(getString("Gen_Okay"))
    },
    error: function(xhr, status, error) {
    console.error("Error marking notification as read:", status, error);
    },
    complete: function() {
    // Perform any cleanup tasks here
    }
  });
  }

// --------------------------------------------------
// Remove a notification
function removeNotification(guid) {  
  
  $.ajax({
    url: phpEndpoint,
    type: 'GET',
    data: {
    action: 'remove_notification',
    guid: guid
    },
    success: function(response) {
    console.log(response);
    // Perform any further actions after marking the notification as read here
    showMessage(getString("Gen_Okay"))
    },
    error: function(xhr, status, error) {
    console.error("Error removing notification:", status, error);
    },
    complete: function() {
    // Perform any cleanup tasks here
    }
  });
  }


