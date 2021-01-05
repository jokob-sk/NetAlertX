/* -----------------------------------------------------------------------------
  Pi.Alert Common Javascript functions
----------------------------------------------------------------------------- */

// -----------------------------------------------------------------------------
var timerRefreshData = ''


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
  document.getElementById ('pageTitle').innerHTML = (new Date().getSeconds());
}
