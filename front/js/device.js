

// -----------------------------------------------------------------------------
function askDeleteDevice () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Ask delete device
  showModalWarning ('Delete Device', 'Are you sure you want to delete this device?<br>(maybe you prefer to archive it)',
    getString('Gen_Cancel'), getString('Gen_Delete'), 'deleteDevice');
}


// -----------------------------------------------------------------------------
function deleteDevice () {
  // Check MAC
  if (mac == '') {
    return;
  }

  // Delete device
  $.get('php/server/devices.php?action=deleteDevice&mac='+ mac, function(msg) {
    showMessage (msg);
  });

  // refresh API
  updateApi("devices,appevents")
}

// -----------------------------------------------------------------------------
function deleteDeviceByMac (mac) {
  // Check MAC
  if (mac == '') {
      return;
  }

  // Delete device
  $.get('php/server/devices.php?action=deleteDevice&mac='+ mac, function(msg) {
      showMessage (msg);
  });

  // refresh API
  updateApi("devices,appevents")
}
    