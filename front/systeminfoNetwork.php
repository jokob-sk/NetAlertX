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

//Network stats
// Server IP

$externalIp = getExternalIp();

// Check Server name
if (!empty(gethostname())) { $network_NAME = gethostname(); } else { $network_NAME = lang('Systeminfo_Network_Server_Name_String'); }
// Check HTTPS
if (isset($_SERVER['HTTPS'])) { $network_HTTPS = 'Yes (HTTPS)'; } else { $network_HTTPS = lang('Systeminfo_Network_Secure_Connection_String'); }
// Check Query String
if (empty($_SERVER['QUERY_STRING'])) { $network_QueryString = lang('Systeminfo_Network_Server_Query_String'); } else { $network_QueryString = $_SERVER['QUERY_STRING']; }
// Check HTTP referer
if (empty($_SERVER['HTTP_REFERER'])) { $network_referer = lang('Systeminfo_Network_HTTP_Referer_String'); } else { $network_referer = $_SERVER['HTTP_REFERER']; }
//Network Hardware stat
$network_result = shell_exec("cat /proc/net/dev | tail -n +3 | awk '{print $1}'");
$net_interfaces = explode("\n", trim($network_result));
$network_result = shell_exec("cat /proc/net/dev | tail -n +3 | awk '{print $2}'");
$net_interfaces_rx = explode("\n", trim($network_result));
$network_result = shell_exec("cat /proc/net/dev | tail -n +3 | awk '{print $10}'");
$net_interfaces_tx = explode("\n", trim($network_result));


// Network Hardware ----------------------------------------------------------
echo '<div class="box box-solid">
        <div class="box-header">
          <h3 class="box-title sysinfo_headline"><i class="fa fa-sitemap fa-rotate-270"></i> ' . lang('Systeminfo_Network_Hardware') . '</h3>
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
            <tbody>';

for ($x = 0; $x < sizeof($net_interfaces); $x++) {
    $interface_name = str_replace(':', '', $net_interfaces[$x]);
    $interface_ip_temp = exec('ip addr show ' . $interface_name . ' | grep "inet "');
    $interface_ip_arr = explode(' ', trim($interface_ip_temp));

    if (!isset($interface_ip_arr[1])) {
        $interface_ip_arr[1] = '--';
    }

    if ($net_interfaces_rx[$x] == 0) {
        $temp_rx = 0;
    } else {
        $temp_rx = number_format(round(($net_interfaces_rx[$x] / 1024 / 1024), 2), 2, ',', '.');
    }
    if ($net_interfaces_tx[$x] == 0) {
        $temp_tx = 0;
    } else {
        $temp_tx = number_format(round(($net_interfaces_tx[$x] / 1024 / 1024), 2), 2, ',', '.');
    }
    echo '<tr>';
    echo '<td>' . $interface_name . '</td>';
    echo '<td>' . $interface_ip_arr[1] . '</td>';
    echo '<td>' . $temp_rx . ' MB</td>';
    echo '<td>' . $temp_tx . ' MB</td>';
    echo '</tr>';
}

echo '        </tbody>
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

// INIT
$(document).ready(function() {

  // available IPs
  fetchUsedIps(usedIps => {
    const allIps = inferNetworkRange(usedIps);
    renderAvailableIpsTable(allIps, usedIps);
  });

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