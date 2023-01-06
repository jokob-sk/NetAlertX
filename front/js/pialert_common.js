/* -----------------------------------------------------------------------------
*  Pi.Alert
*  Open Source Network Guard / WIFI & LAN intrusion detector 
*
*  pialert_common.js - Front module. Common Javascript functions
*-------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
----------------------------------------------------------------------------- */

// -----------------------------------------------------------------------------
var timerRefreshData = ''
var modalCallbackFunction = '';
var emptyArr            = ['undefined', "", undefined, null];

// urlParams = new Proxy(new URLSearchParams(window.location.search), {
//   get: (searchParams, prop) => searchParams.get(prop.toString()),
// });

function getCache(key)
{
  // check cache
  if(sessionStorage.getItem(key))
  {
    return sessionStorage.getItem(key);
  } else
  {
    return "";
  }
}

function setCache(key, data)
{
  sessionStorage.setItem(key, data); 
}


// -----------------------------------------------------------------------------
function setCookie (cookie, value, expirationMinutes='') {
  // Calc expiration date
  var expires = '';
  if (typeof expirationMinutes === 'number') {
    expires = ';expires=' + new Date(Date.now() + expirationMinutes *60*1000).toUTCString();
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
function showModalOk (title, message, callbackFunction = null) {
  // set captions
  $('#modal-ok-title').html   (title);
  $('#modal-ok-message').html (message); 
  
  if(callbackFunction!= null)
  {   
    $("#modal-ok-OK").click(function()
    { 
      callbackFunction()      
    });
  }

  // Show modal
  $('#modal-ok').modal('show');
}
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

function showModalDefaultStrParam (title, message, btnCancel, btnOK, callbackFunction, param='') {
  // set captions
  $('#modal-str-title').html   (title);
  $('#modal-str-message').html (message);
  $('#modal-str-cancel').html  (btnCancel);
  $('#modal-str-OK').html      (btnOK);
  $("#modal-str-OK").off("click"); //remove existing handlers
  $('#modal-str-OK').on('click', function (){ 
    $('#modal-str').modal('hide');
    callbackFunction(param)
  })

  // Show modal
  $('#modal-str').modal('show');
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
// remove unnecessary lines from the result
function sanitize(data)
{
  return data.replace(/(\r\n|\n|\r)/gm,"").replace(/[^\x00-\x7F]/g, "")
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
function saveData(functionName, index, value) {
  $.ajax({
    method: "GET",
    url: "php/server/devices.php",
    data: { action: functionName, index: index, value:value  },
    success: function(data) {      
        
        if(sanitize(data) == 'OK')
        {
          showMessage("Saved")
          // Remove navigation prompt "Are you sure you want to leave..."
          window.onbeforeunload = null;
        } else
        {
          showMessage("ERROR")
        }        

      }
  });

}

// -----------------------------------------------------------------------------
function sleep(milliseconds) {
  const date = Date.now();
  let currentDate = null;
  do {
    currentDate = Date.now();
  } while (currentDate - date < milliseconds);
}

// --------------------------------------------------------- 
somethingChanged = false;
function settingsChanged()
{
  somethingChanged = true;
  // Enable navigation prompt ... "Are you sure you want to leave..."
  window.onbeforeunload = function() {  
    return true;
  };
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
  }, 60000);
}


// -----------------------------------------------------------------------------
function debugTimer () {
  $('#pageTitle').html (new Date().getSeconds());
}


// -----------------------------------------------------------------------------
function openInNewTab (url) {
  window.open(url, "_blank");
}



