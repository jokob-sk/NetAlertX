

// -----------------------------------------------------------------------------
function askDeleteDevice() {

  mac = getMac()

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
  mac = getMac()

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
  mac = getMac()

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
  mac = getMac()

  // alert(mac)
  // return;

  // Delete device
  $.get('php/server/devices.php?action=deleteDevice&mac=' + mac, function (msg) {
    showMessage(msg);
  });

  // refresh API
  updateApi("devices,appevents")
}


