

// -----------------------------------------------------------------------------
function askDeleteDevice() {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Ask delete device
  showModalWarning(
    getString("DevDetail_button_Delete"),
    getString("DevDetail_button_Delete_ask"),
    getString('Gen_Cancel'), 
    getString('Gen_Delete'), 
    'deleteDevice');
}

// -----------------------------------------------------------------------------
function askDelDevDTInline(mac) {
  // Check MAC
  if (mac == '') {
    return;
  }

  showModalWarning(
    getString("DevDetail_button_Delete"), 
    getString("DevDetail_button_Delete_ask"),
    getString('Gen_Cancel'), 
    getString('Gen_Delete'), 
    () => deleteDeviceByMac(mac))
}


// -----------------------------------------------------------------------------
function deleteDevice() {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Delete device
  $.get('php/server/devices.php?action=deleteDevice&mac=' + mac, function (msg) {
    showMessage(msg);
  });

  // refresh API
  updateApi("devices,appevents")
}

// -----------------------------------------------------------------------------
function deleteDeviceByMac(mac) {
  // Check MAC
  if (mac == '') {
    return;
  }

  // alert(mac)
  // return;

  // Delete device
  $.get('php/server/devices.php?action=deleteDevice&mac=' + mac, function (msg) {
    showMessage(msg);
  });

  // refresh API
  updateApi("devices,appevents")
}


