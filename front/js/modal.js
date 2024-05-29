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
    callbackFunction = null
) {
    // set captions
    $("#modal-warning-title").html(title);
    $("#modal-warning-message").html(message);
    $("#modal-warning-cancel").html(btnCancel);
    $("#modal-warning-OK").html(btnOK);

    if (callbackFunction != null) {
        modalCallbackFunction = callbackFunction;
    }

    // Show modal
    $("#modal-warning").modal("show");
}

// -----------------------------------------------------------------------------
function showModalInput(
    title,
    message,
    btnCancel = getString("Gen_Cancel"),
    btnOK = getString("Gen_Okay"),
    callbackFunction = null
) {
    prefix = "modal-input";

    // set captions
    $(`#${prefix}-title`).html(title);
    $(`#${prefix}-message`).html(message);
    $(`#${prefix}-cancel`).html(btnCancel);
    $(`#${prefix}-OK`).html(btnOK);

    if (callbackFunction != null) {
        modalCallbackFunction = callbackFunction;
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
    callbackFunction = null
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

    $(`#${prefix}-field`).val(curValue);

    setTimeout(function () {
        $(`#${prefix}-field`).focus();
    }, 500);

    // Show modal
    $(`#${prefix}`).modal("show");
}

// -----------------------------------------------------------------------------
function modalDefaultOK() {
    // Hide modal
    $("#modal-default").modal("hide");

    // timer to execute function
    window.setTimeout(function () {
        window[modalCallbackFunction]();
    }, 100);
}

// -----------------------------------------------------------------------------
function modalDefaultInput() {
    // Hide modal
    $("#modal-input").modal("hide");

    // timer to execute function
    window.setTimeout(function () {
        window[modalCallbackFunction]();
    }, 100);
}

// -----------------------------------------------------------------------------
function modalDefaultFieldInput() {
    // Hide modal
    $("#modal-field-input").modal("hide");

    // timer to execute function
    window.setTimeout(function () {
        modalCallbackFunction();
    }, 100);
}

// -----------------------------------------------------------------------------
function modalWarningOK() {
    // Hide modal
    $("#modal-warning").modal("hide");

    // timer to execute function
    window.setTimeout(function () {
        window[modalCallbackFunction]();
    }, 100);
}

// -----------------------------------------------------------------------------
function showMessage(textMessage = "", timeout = 3000, colorClass = "modal_green") {
    if (textMessage.toLowerCase().includes("error")) {
        // show error
        alert(textMessage);
    } else {
        // show temporary notification
        $("#notification").removeClass();                                               // remove all classes
        $("#notification").addClass("alert alert-dimissible notification_modal");       // add default ones
        $("#notification").addClass(colorClass);                                       // add color modifiers

        // message
        $("#alert-message").html(textMessage);

        // timeout
        $("#notification").fadeIn(1, function () {
            window.setTimeout(function () {
                $("#notification").fadeOut(500);
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
