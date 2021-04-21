/* -----------------------------------------------------------------------------
*  Pi.Alert
*  Open Source Network Guard / WIFI & LAN intrusion detector 
*
*  pialert_common.js - Front module. Common Javascript functions
*-------------------------------------------------------------------------------
*  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
----------------------------------------------------------------------------- */

// -----------------------------------------------------------------------------
var timerRefreshData = ''
var modalCallbackFunction = '';


// -----------------------------------------------------------------------------
function setCookie (cookie, value, expirationHours='') {
  // Calc expiration date
  var expires = '';
  if (typeof expirationHours === 'number') {
    expires = ';expires=' + new Date(Date.now() + expirationHours *60*60*1000).toUTCString();
  }

  // Save Cookie
  document.cookie = cookie + "=" + value + expires;
}

// -----------------------------------------------------------------------------
function getCookie (cookie) {
  // Array of cookies
  var allCookies = document.cookie.split(';');

  // For each cookie
  for (var i = 0; i < allCookies.length; i++) {
    var currentCookie = allCookies[i].trim();

    // If the current cookie is the correct cookie
    if (currentCookie.indexOf (cookie +'=') == 0) {
      // Return value
      return currentCookie.substring (cookie.length+1);
    }
  }

  // Return empty (not found)
  return "";
}


// -----------------------------------------------------------------------------
function deleteCookie (cookie) {
  document.cookie = cookie + '=;expires=Thu, 01 Jan 1970 00:00:00 UTC';
}

// -----------------------------------------------------------------------------
function deleteAllCookies() {
  // Array of cookies
  var allCookies = document.cookie.split(";");

  // For each cookie
  for (var i = 0; i < allCookies.length; i++) {
    var cookie = allCookies[i].trim();
    var eqPos = cookie.indexOf("=");
    var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC";
    }
}



// -----------------------------------------------------------------------------
function showModalDefault (title, message, btnCancel, btnOK, callbackFunction) {
  // set captions
  $('#modal-default-title').html   (title);
  $('#modal-default-message').html (message);
  $('#modal-default-cancel').html  (btnCancel);
  $('#modal-default-OK').html      (btnOK);
  modalCallbackFunction =          callbackFunction;

  // Show modal
  $('#modal-default').modal('show');
}

// -----------------------------------------------------------------------------
function showModalWarning (title, message, btnCancel, btnOK, callbackFunction) {
  // set captions
  $('#modal-warning-title').html   (title);
  $('#modal-warning-message').html (message);
  $('#modal-warning-cancel').html  (btnCancel);
  $('#modal-warning-OK').html      (btnOK);
  modalCallbackFunction =          callbackFunction;

  // Show modal
  $('#modal-warning').modal('show');
}

// -----------------------------------------------------------------------------
function modalDefaultOK () {
  // Hide modal
  $('#modal-default').modal('hide');

  // timer to execute function
  window.setTimeout( function() {
    window[modalCallbackFunction]();
  }, 100);
}

// -----------------------------------------------------------------------------
function modalWarningOK () {
  // Hide modal
  $('#modal-warning').modal('hide');

  // timer to execute function
  window.setTimeout( function() {
    window[modalCallbackFunction]();
  }, 100);
}

// -----------------------------------------------------------------------------
function showMessage (textMessage="") {
  if (textMessage.toLowerCase().includes("error")  ) {
    // show error
    alert (textMessage);
  } else {
    // show temporal notification
    $("#alert-message").html (textMessage);
    $("#notification").fadeIn(1, function () {
      window.setTimeout( function() {
        $("#notification").fadeOut(500)
      }, 3000);
    } );
  }
}


// -----------------------------------------------------------------------------
function setParameter (parameter, value) {
  // Retry
  $.get('php/server/parameters.php?action=set&parameter=' + parameter +
    '&value='+ value,
  function(data) {
    if (data != "OK") {
      // Retry
      sleep (200);
      $.get('php/server/parameters.php?action=set&parameter=' + parameter +
        '&value='+ value,
      function(data) {
        if (data != "OK") {
         // alert (data);
        } else {
        // alert ("OK. Second attempt");
        };
      } );
    };
  } );
}


// -----------------------------------------------------------------------------
function sleep(milliseconds) {
  const date = Date.now();
  let currentDate = null;
  do {
    currentDate = Date.now();
  } while (currentDate - date < milliseconds);
}


// -----------------------------------------------------------------------------
function translateHTMLcodes (text) {
  if (text == null) {
    return null;
  }
  var text2 = text.replace(new RegExp(' ', 'g'), "&nbsp");
  text2 = text2.replace(new RegExp('<', 'g'), "&lt");
  return text2;
}


// -----------------------------------------------------------------------------
function stopTimerRefreshData () {
  try {
    clearTimeout (timerRefreshData); 
  } catch (e) {}
}


// -----------------------------------------------------------------------------
function newTimerRefreshData (refeshFunction) {
  timerRefreshData = setTimeout (function() {
    refeshFunction();
  }, 5000);
}


// -----------------------------------------------------------------------------
function debugTimer () {
  $('#pageTitle').html (new Date().getSeconds());
}


