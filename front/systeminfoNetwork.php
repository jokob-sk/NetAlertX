<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/server/db.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/language/lang.php';
?>


<?php

function getExternalIp() {
  $ch = curl_init('https://api64.ipify.org?format=json');
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
  curl_setopt($ch, CURLOPT_TIMEOUT, 10);
  $response = curl_exec($ch);
  if (curl_errno($ch)) {
      curl_close($ch);
      return 'ERROR: ' . curl_error($ch);
  }
  curl_close($ch);

  $data = json_decode($response, true);
  if (isset($data['ip'])) {
      return htmlspecialchars($data['ip']);
  }
  return 'ERROR: Invalid response';
}

// ----------------------------------------------------------
// Network
// ----------------------------------------------------------



// ----------------------------------------------------
// Network Stats (General)
// ----------------------------------------------------

// External IP
$externalIp = getExternalIp();

// Server Name
$network_NAME = gethostname() ?: lang('Systeminfo_Network_Server_Name_String');

// HTTPS Check
$network_HTTPS = isset($_SERVER['HTTPS']) ? 'Yes (HTTPS)' : lang('Systeminfo_Network_Secure_Connection_String');

// Query String
$network_QueryString = !empty($_SERVER['QUERY_STRING'])
    ? $_SERVER['QUERY_STRING']
    : lang('Systeminfo_Network_Server_Query_String');

// Referer
$network_referer = !empty($_SERVER['HTTP_REFERER'])
    ? $_SERVER['HTTP_REFERER']
    : lang('Systeminfo_Network_HTTP_Referer_String');


// ----------------------------------------------------
// Network Hardware Stats (FAST VERSION)
// ----------------------------------------------------

// ----------------------------------------------------
// Network Stats (General)
// ----------------------------------------------------

// External IP
$externalIp = getExternalIp();

// Server Name
$network_NAME = gethostname() ?: lang('Systeminfo_Network_Server_Name_String');

// HTTPS Check
$network_HTTPS = isset($_SERVER['HTTPS']) ? 'Yes (HTTPS)' : lang('Systeminfo_Network_Secure_Connection_String');

// Query String
$network_QueryString = !empty($_SERVER['QUERY_STRING'])
    ? $_SERVER['QUERY_STRING']
    : lang('Systeminfo_Network_Server_Query_String');

// Referer
$network_referer = !empty($_SERVER['HTTP_REFERER'])
    ? $_SERVER['HTTP_REFERER']
    : lang('Systeminfo_Network_HTTP_Referer_String');



// ----------------------------------------------------
// Network Stats (General)
// ----------------------------------------------------

// External IP
$externalIp = getExternalIp();

// Server Name
$network_NAME = gethostname() ?: lang('Systeminfo_Network_Server_Name_String');

// HTTPS Check
$network_HTTPS = isset($_SERVER['HTTPS']) ? 'Yes (HTTPS)' : lang('Systeminfo_Network_Secure_Connection_String');

// Query String
$network_QueryString = !empty($_SERVER['QUERY_STRING'])
    ? $_SERVER['QUERY_STRING']
    : lang('Systeminfo_Network_Server_Query_String');

// Referer
$network_referer = !empty($_SERVER['HTTP_REFERER'])
    ? $_SERVER['HTTP_REFERER']
    : lang('Systeminfo_Network_HTTP_Referer_String');

echo '
    <div class="box box-solid">
  <div class="box-header">
    <h3 class="box-title sysinfo_headline">
      <i class="fa fa-sitemap fa-rotate-270"></i>' . lang('Systeminfo_Network_Hardware') .'
    </h3>
  </div>
  <div class="box-body">
    <table id="networkTable" class="table table-bordered table-hover">
      <thead>
        <tr>
                <th>' . lang('Systeminfo_Network_Hardware_Interface_Name') . '</th>
                <th>' . lang('Systeminfo_Network_Hardware_Interface_Mask') . '</th>
                <th>' . lang('Systeminfo_Network_Hardware_Interface_RX') . '</th>
                <th>' . lang('Systeminfo_Network_Hardware_Interface_TX') . '</th>
        </tr>
      </thead>
      <tbody>
        <tr><td colspan="4">Loading...</td></tr>
      </tbody>
    </table>
  </div>
</div>';

// Available IPs ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title availableips_headline"><i class="fa fa-list"></i> ' . lang('Systeminfo_AvailableIps') . '</h3>
            </div>
            <div class="box-body">
               <table id="availableIpsTable" class="display table table-bordered table-hover dataTable no-footer" style="width:100%"></table>
            </div>
      </div>';



// Network ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fas fa-ethernet"></i> ' . lang('Systeminfo_Network') . '</h3>
            </div>
            <div class="box-body">
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_IP') . '</div>
			  <div class="col-sm-9 sysinfo_network_b" id="external-ip">' .$externalIp. '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_IP_Connection') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['REMOTE_ADDR'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_IP_Server') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['SERVER_ADDR'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Server_Name') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $network_NAME . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Connection_Port') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['REMOTE_PORT'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Secure_Connection') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $network_HTTPS . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Server_Version') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['SERVER_SOFTWARE'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">' . lang('Systeminfo_Network_Request_URI') . '</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['REQUEST_URI'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Server_Query') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $network_QueryString . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_HTTP_Host') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['HTTP_HOST'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_HTTP_Referer') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $network_referer . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_MIME') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['HTTP_ACCEPT'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Accept_Language') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['HTTP_ACCEPT_LANGUAGE'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Accept_Encoding') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['HTTP_ACCEPT_ENCODING'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Request_Method') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['REQUEST_METHOD'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_Request_Time') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . $_SERVER['REQUEST_TIME'] . '</div>
			</div>
		</div>
      </div>';


?>



<script>

// --------------------------------------------------------
//  Available free IPS functionality
function inferNetworkRange(usedIps) {
  if (!usedIps || usedIps.length === 0) return [];

  const subnetMap = {};

  // Group IPs by /24 subnet
  for (const ip of usedIps) {
    const parts = ip.split('.');
    if (parts.length !== 4) continue;
    const subnet = `${parts[0]}.${parts[1]}.${parts[2]}`;
    if (!subnetMap[subnet]) subnetMap[subnet] = [];
    subnetMap[subnet].push(ip);
  }

  const result = [];

  for (const [subnet, ips] of Object.entries(subnetMap)) {
    if (ips.length > 5) {
      for (let i = 2; i < 255; i++) {
        const ip = `${subnet}.${i}`;
        result.push({ subnet, ip });
      }
    }
  }

  return result;
}

function fetchUsedIps(callback) {
  $.ajax({
    url: 'php/server/query_graphql.php',
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
      query: `
        query devices($options: PageQueryOptionsInput) {
          devices(options: $options) {
            devices {
              devLastIP
            }
          }
        }
      `,
      variables: {
        options: {
          status: "all_devices"
        }
      }
    }),
    success: function(response) {

      console.log(response);

      const usedIps = (response?.data?.devices?.devices || [])
        .map(d => d.devLastIP)
        .filter(ip => ip && ip.includes('.'));
      callback(usedIps);
    },
    error: function(err) {
      console.error("Error fetching IPs:", err);
      callback([]);
    }
  });
}

function renderAvailableIpsTable(allIps, usedIps) {
  const availableIps = allIps.filter(row => !usedIps.includes(row.ip));

  console.log(availableIps);

  $('#availableIpsTable').DataTable({
    destroy: true,
    data: availableIps,
    columns: [
      {
        title: getString("Gen_Subnet"),
        data: "subnet"
      },
      {
        title: getString("Systeminfo_AvailableIps"),
        data: "ip",
        render: function (data, type, row, meta) {
          return `
            <span>${data}</span>
            <button class="copy-btn btn btn-sm btn-info ml-2 alignRight" data-text="${data}" title="${getString("Gen_CopyToClipboard")}" onclick="copyToClipboard(this)">
              <i class="fa-solid fa-copy"></i>
            </button>
          `;
        }
      }
    ],
    pageLength: 10
  });

}


// Helper: Convert CIDR to subnet mask
function cidrToMask(cidr) {
    return ((0xFFFFFFFF << (32 - cidr)) >>> 0)
        .toString(16)
        .match(/.{1,2}/g)
        .map(h => parseInt(h, 16))
        .join('.');
}

function formatDataSize(bytes) {
    if (!bytes) bytes = 0;  // ensure it's a number

    const mb = bytes / 1024 / 1024; // convert bytes to MB

    // Format number with 2 decimals and thousands separators
    return mb.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " MB";
}



function loadInterfaces() {
    const apiToken = getSetting("API_TOKEN"); 
    const host = window.location.hostname;
    const port = getSetting("GRAPHQL_PORT");

    $.ajax({
        url: "http://" + host + ":" + port + "/nettools/interfaces",
        type: "GET",
        headers: {
            "Authorization": "Bearer " + apiToken,
            "Content-Type": "application/json"
        },
        success: function(data) {
            const tbody = $("#networkTable tbody");
            tbody.empty();

            console.log(data);


            if (!data.success || !data.interfaces || Object.keys(data.interfaces).length === 0) {
                tbody.append('<tr><td colspan="4">No interfaces found</td></tr>');
                return;
            }

            $.each(data.interfaces, function(iface_name, iface) {

                const rx_mb = formatDataSize(iface.rx_bytes);
                const tx_mb = formatDataSize(iface.tx_bytes);

                // const rx_mb = (iface.rx_bytes ?? 0) / 1024 / 1024;
                // const tx_mb = (iface.tx_bytes ?? 0) / 1024 / 1024;

                let cidr_display = "";
                if (iface.ipv4 && iface.ipv4.length > 0) {
                    const ip_info = iface.ipv4[0];
                    const ip = ip_info.ip || "--";
                    const mask = cidrToMask(ip_info.cidr || 24);
                    cidr_display = mask + " / " + iface.ipv4;
                }

                tbody.append(`
                    <tr>
                        <td>${iface_name}</td>
                        <td>${cidr_display}</td>
                        <td>${rx_mb}</td>
                        <td>${tx_mb}</td>
                    </tr>
                `);
            });
        },
        error: function(xhr) {
            const tbody = $("#networkTable tbody");
            tbody.empty();
            tbody.append('<tr><td colspan="4">Failed to fetch interfaces</td></tr>');
            console.error("Error fetching interfaces:", xhr.responseText);
        }
    });
}

// INIT
$(document).ready(function() {

  // available IPs
  fetchUsedIps(usedIps => {
    const allIps = inferNetworkRange(usedIps);
    renderAvailableIpsTable(allIps, usedIps);
  });

  loadInterfaces();

  setTimeout(() => {
    // Available IPs datatable
    $('#networkTable').DataTable({
      searching: true,
      order: [[0, "desc"]],
      initComplete: function(settings, json) {
          hideSpinner(); // Called after the DataTable is fully initialized
      }
    });
  }, 200);
});

</script>