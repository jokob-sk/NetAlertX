

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

  const apiBase = getApiBase();
  const apiToken = getSetting("API_TOKEN");
  const url = `${apiBase}/device/${mac}/delete`;

  $.ajax({
    url,
    method: "DELETE",
    headers: { "Authorization": `Bearer ${apiToken}` },
    success: function(response) {
      showMessage(response.success ? "Device deleted successfully" : (response.error || "Unknown error"));
      updateApi("devices,appevents");
    },
    error: function(xhr, status, error) {
      console.error("Error deleting device:", status, error);
      showMessage("Error: " + (xhr.responseJSON?.error || error));
    }
  });
}

// -----------------------------------------------------------------------------
function deleteDeviceByMac(mac) {
  // Check MAC
  mac = getMac()

  const apiBase = getApiBase();
  const apiToken = getSetting("API_TOKEN");
  const url = `${apiBase}/device/${mac}/delete`;

  $.ajax({
    url,
    method: "DELETE",
    headers: { "Authorization": `Bearer ${apiToken}` },
    success: function(response) {
      showMessage(response.success ? "Device deleted successfully" : (response.error || "Unknown error"));
      updateApi("devices,appevents");
    },
    error: function(xhr, status, error) {
      console.error("Error deleting device:", status, error);
      showMessage("Error: " + (xhr.responseJSON?.error || error));
    }
  });
}


