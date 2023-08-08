<?php

//------------------------------------------------------------------------------
//  Pi.Alert
//  Open Source Network Guard / WIFI & LAN intrusion detector 
//
//  devices.php - Front module. Server side. Manage Devices
//------------------------------------------------------------------------------
//  Puche      2021        pi.alert.application@gmail.com   GNU GPLv3
//  jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3
//  leiweibau  2022        https://github.com/leiweibau     GNU GPLv3
//  cvc90      2023        https://github.com/cvc90         GNU GPLv3
//------------------------------------------------------------------------------

  require 'php/templates/header.php';
?>
<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
       <?= lang('SYSTEM_TITLE') ;?>
      </h1>
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">	

<?php
// OS-Version
$os_version = '';
// Raspbian
if ($os_version == '') {$os_version = exec('cat /etc/os-release | grep PRETTY_NAME');}
// Dietpi
if ($os_version == '') {$os_version = exec('uname -o');}
//$os_version_arr = explode("\n", trim($os_version));
$stat['os_version'] = str_replace('"', '', str_replace('PRETTY_NAME=', '', $os_version));
$stat['uptime'] = str_replace('up ', '', shell_exec("uptime -p"));
//CPU stat
$prevVal = shell_exec("cat /proc/cpuinfo | grep processor");
$prevArr = explode("\n", trim($prevVal));
$stat['cpu'] = sizeof($prevArr);
$cpu_result = shell_exec("cat /proc/cpuinfo | grep Model");
$stat['cpu_model'] = strstr($cpu_result, "\n", true);
$stat['cpu_model'] = str_replace(":", "", trim(str_replace("Model", "", $stat['cpu_model'])));
if ($stat['cpu_model'] == '') {
	$cpu_result = shell_exec("cat /proc/cpuinfo | grep model\ name");
	$stat['cpu_model'] = strstr($cpu_result, "\n", true);
	$stat['cpu_model'] = str_replace(":", "", trim(str_replace("model name", "", $stat['cpu_model'])));
}
if (file_exists('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq')) {
	// RaspbianOS
	$stat['cpu_frequ'] = exec('cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq') / 1000;
} elseif (is_numeric(str_replace(',', '.', exec('lscpu | grep "MHz" | awk \'{print $3}\'')))) {
	// Ubuntu Server, DietPi event. others
	$stat['cpu_frequ'] = round(exec('lscpu | grep "MHz" | awk \'{print $3}\''), 0);
} elseif (is_numeric(str_replace(',', '.', exec('lscpu | grep "max MHz" | awk \'{print $4}\'')))) {
	// RaspbianOS and event. others
	$stat['cpu_frequ'] = round(str_replace(',', '.', exec('lscpu | grep "max MHz" | awk \'{print $4}\'')), 0);
} else {
	// Fallback
	$stat['cpu_frequ'] = "unknown";
}
$cpu_temp = shell_exec('cat /sys/class/thermal/thermal_zone0/temp'); // Get the CPU temperature
$cpu_temp = floatval($cpu_temp) / 1000; // Convert the temperature to degrees Celsius
//Memory stats
$total_memorykb = shell_exec("cat /proc/meminfo | grep MemTotal | awk '{print $2}'");
$total_memorykb = number_format($total_memorykb, 0, '.', '.');
$total_memorymb = shell_exec("cat /proc/meminfo | grep MemTotal | awk '{print $2/1024}'");
$total_memorymb = number_format($total_memorymb, 0, '.', '.');
$mem_used = round(memory_get_usage() / 1048576 * 100, 2);
$memory_usage_percent = round(($mem_used / $total_memorymb), 2);
//Load System
$load_average = sys_getloadavg();
//Date & Time
$date = new DateTime();
$formatted_date = $date->format('l, F j, Y H:i:s');
$formatted_date2 = $date->format('d/m/Y H:i:s');
$formatted_date3 = $date->format('Y/m/d H:i:s');
//Network Hardware stat
$network_result = shell_exec("cat /proc/net/dev | tail -n +3 | awk '{print $1}'");
$net_interfaces = explode("\n", trim($network_result));
$network_result = shell_exec("cat /proc/net/dev | tail -n +3 | awk '{print $2}'");
$net_interfaces_rx = explode("\n", trim($network_result));
$network_result = shell_exec("cat /proc/net/dev | tail -n +3 | awk '{print $10}'");
$net_interfaces_tx = explode("\n", trim($network_result));
//HDD stats
$hdd_result = shell_exec("df | awk '{print $1}'");
$hdd_devices = explode("\n", trim($hdd_result));
$hdd_result = shell_exec("df | awk '{print $2}'");
$hdd_devices_total = explode("\n", trim($hdd_result));
$hdd_result = shell_exec("df | awk '{print $3}'");
$hdd_devices_used = explode("\n", trim($hdd_result));
$hdd_result = shell_exec("df | awk '{print $4}'");
$hdd_devices_free = explode("\n", trim($hdd_result));
$hdd_result = shell_exec("df | awk '{print $5}'");
$hdd_devices_percent = explode("\n", trim($hdd_result));
$hdd_result = shell_exec("df | awk '{print $6}'");
$hdd_devices_mount = explode("\n", trim($hdd_result));
//USB devices
$usb_result = shell_exec("lsusb");
$usb_devices_mount = explode("\n", trim($usb_result));

// General ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-info-circle"></i> General</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Full Date</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $formatted_date . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Date</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $formatted_date2 . '</div>
                </div>            
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Date2</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $formatted_date3 . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Timezone</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $timeZone . '</div>
                </div>                                        
            </div>
      </div>';

// Client ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-globe"></i> This Client</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">User Agent</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['HTTP_USER_AGENT'] . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Browser Resolution:</div>
                  <div class="col-sm-9 sysinfo_gerneral_b" id="resolution"></div>
                </div>
            </div>
      </div>';

echo '<script>
    var ratio = window.devicePixelRatio || 1;
    var w = window.innerWidth;
    var h = window.innerHeight;
    var rw = window.innerWidth * ratio;
    var rh = window.innerHeight * ratio;

    var resolutionDiv = document.getElementById("resolution");
    resolutionDiv.innerHTML = "Width: " + w + "px / Height: " + h + "px<br> " + "Width: " + rw + "px / Height: " + rh + "px (native)";
</script>';

// System ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-computer"></i> System</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Uptime</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['uptime'] . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Operating System</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['os_version'] . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Load AVG:</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">'. $load_average[0] .' '. $load_average[1] .' '. $load_average[2] .'</div>
                </div>
            </div>
      </div>';

// CPU ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-microchip"></i> CPU</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">CPU Name:</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['cpu_model'] . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">CPU Cores:</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['cpu'] . ' @ ' . $stat['cpu_frequ'] . ' MHz</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">CPU Temp:</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">'. $cpu_temp .' °C</div>
                </div>
            </div>
      </div>';
      
// Memory ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-memory"></i> Memory</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Memory:</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $mem_used . ' MB / ' . $total_memorymb . ' MB</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Memory %:</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $memory_usage_percent . ' %</div>
                </div>                
                <div class="row">
                  <div class="col-sm-3 sysinfo_gerneral_a">Total memory:</div>
                  <div class="col-sm-9 sysinfo_gerneral_b">' . $total_memorymb  . ' MB (' . $total_memorykb . ' KB)</div>
                </div>
            </div>
      </div>';

echo '<script>
	var ratio = window.devicePixelRatio || 1;
	var w = window.innerWidth;
	var h = window.innerHeight;
	var rw = window.innerWidth * ratio;
	var rh = window.innerHeight * ratio;

	var resolutionDiv = document.getElementById("resolution");
	resolutionDiv.innerHTML = "Width: " + w + "px / Height: " + h + "px<br> " + "Width: " + rw + "px / Height: " + rh + "px (native)";
</script>';

// Storage ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-hdd"></i> Storage</h3>
            </div>
            <div class="box-body">';

$storage_lsblk = shell_exec("lsblk -io NAME,SIZE,TYPE,MOUNTPOINT,MODEL --list | tail -n +2 | awk '{print $1\"#\"$2\"#\"$3\"#\"$4\"#\"$5}'");
$storage_lsblk_line = explode("\n", $storage_lsblk);
$storage_lsblk_line = array_filter($storage_lsblk_line);

for ($x = 0; $x < sizeof($storage_lsblk_line); $x++) {
	$temp = array();
	$temp = explode("#", $storage_lsblk_line[$x]);
	$storage_lsblk_line[$x] = $temp;
}
// echo '<pre>';
// print_r($storage_lsblk_line);
// echo '</pre>';

for ($x = 0; $x < sizeof($storage_lsblk_line); $x++) {
	//if (stristr($hdd_devices[$x], '/dev/')) {
	echo '<div class="row">';
	if (preg_match('~[0-9]+~', $storage_lsblk_line[$x][0])) {
		echo '<div class="col-sm-4 sysinfo_gerneral_a">Mount point "' . $storage_lsblk_line[$x][3] . '"</div>';
	} else {
		echo '<div class="col-sm-4 sysinfo_gerneral_a">"' . str_replace('_', ' ', $storage_lsblk_line[$x][3]) . '"</div>';
	}
	echo '<div class="col-sm-3 sysinfo_gerneral_b">Device: /dev/' . $storage_lsblk_line[$x][0] . '</div>';
	echo '<div class="col-sm-2 sysinfo_gerneral_b">Size: ' . $storage_lsblk_line[$x][1] . '</div>';
	echo '<div class="col-sm-2 sysinfo_gerneral_b">Type: ' . $storage_lsblk_line[$x][2] . '</div>';
	echo '</div>';
	//}
}
echo '      </div>
      </div>';

// Storage usage ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-hdd"></i> Storage usage</h3>
            </div>
            <div class="box-body">';
for ($x = 0; $x < sizeof($hdd_devices); $x++) {
	if (stristr($hdd_devices[$x], '/dev/')) {
		if ($hdd_devices_total[$x] == 0) {$temp_total = 0;} else { $temp_total = number_format(round(($hdd_devices_total[$x] / 1024 / 1024), 2), 2, ',', '.');}
		if ($hdd_devices_used[$x] == 0) {$temp_used = 0;} else { $temp_used = number_format(round(($hdd_devices_used[$x] / 1024 / 1024), 2), 2, ',', '.');}
		if ($hdd_devices_free[$x] == 0) {$temp_free = 0;} else { $temp_free = number_format(round(($hdd_devices_free[$x] / 1024 / 1024), 2), 2, ',', '.');}
		echo '<div class="row">';
		echo '<div class="col-sm-4 sysinfo_gerneral_a">Mount point "' . $hdd_devices_mount[$x] . '"</div>';
		echo '<div class="col-sm-2 sysinfo_gerneral_b">Total: ' . $temp_total . ' GB</div>';
		echo '<div class="col-sm-3 sysinfo_gerneral_b">Used: ' . $temp_used . ' GB (' . number_format($hdd_devices_percent[$x], 1, ',', '.') . '%)</div>';
		echo '<div class="col-sm-2 sysinfo_gerneral_b">Free: ' . $temp_free . ' GB</div>';
		echo '</div>';
	}
}
echo '<br>' . $pia_lang['SysInfo_storage_note'];
echo '      </div>
      </div>';

// Network ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fas fa-ethernet"></i> Network</h3>
            </div>
            <div class="box-body">
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">IP Internet:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . shell_exec("curl https://ifconfig.co") . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">IP connection:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['REMOTE_ADDR'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Server IP:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['SERVER_ADDR'] . '</div>
			</div>	
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Server name:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['SERVER_NAME'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Connection port:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['REMOTE_PORT'] . '</div>
			</div>			
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Secure connection:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['HTTPS'] . '</div>
			</div>	
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Server Version:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['SERVER_SOFTWARE'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Request URI:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['REQUEST_URI'] . '</div>
			</div>		
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Server query:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['QUERY_STRING'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">HTTP_host:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['HTTP_HOST'] . '</div>
			</div>	
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">HTTP_referer:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['HTTP_REFERER'] . '</div>
			</div>	
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">MIME:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['HTTP_ACCEPT'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Accept language:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['HTTP_ACCEPT_LANGUAGE'] . '</div>
			</div>				
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Accept encoding:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['HTTP_ACCEPT_ENCODING'] . '</div>
			</div>			
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Request_Method:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['REQUEST_METHOD'] . '</div>
			</div>
			<div class="row">
			  <div class="col-sm-3 sysinfo_gerneral_a">Request_time:</div>
			  <div class="col-sm-9 sysinfo_gerneral_b">' . $_SERVER['REQUEST_TIME'] . '</div>
			</div>						
		</div>
      </div>';


// Network Hardware ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fas fa-network-wired"></i> Network Hardware</h3>
            </div>
            <div class="box-body">';

for ($x = 0; $x < sizeof($net_interfaces); $x++) {
	$interface_name = str_replace(':', '', $net_interfaces[$x]);
	$interface_ip_temp = exec('ip addr show ' . $interface_name . ' | grep inet');
	$interface_ip_arr = explode(' ', trim($interface_ip_temp));

	if (!isset($interface_ip_arr[1])) {$interface_ip_arr[1] = '--';}

	if ($net_interfaces_rx[$x] == 0) {$temp_rx = 0;} else { $temp_rx = number_format(round(($net_interfaces_rx[$x] / 1024 / 1024), 2), 2, ',', '.');}
	if ($net_interfaces_tx[$x] == 0) {$temp_tx = 0;} else { $temp_tx = number_format(round(($net_interfaces_tx[$x] / 1024 / 1024), 2), 2, ',', '.');}
	echo '<div class="row">';
	echo '<div class="col-sm-2 sysinfo_network_a">' . $interface_name . '</div>';
	echo '<div class="col-sm-2 sysinfo_network_b">' . $interface_ip_arr[1] . '</div>';
	echo '<div class="col-sm-3 sysinfo_network_b">RX: <div class="sysinfo_network_value">' . $temp_rx . ' MB</div></div>';
	echo '<div class="col-sm-3 sysinfo_network_b">TX: <div class="sysinfo_network_value">' . $temp_tx . ' MB</div></div>';
	echo '</div>';

}
echo '      </div>
      </div>';

// Services ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-database"></i> Services (running)</h3>
            </div>
            <div class="box-body">';
echo '<div style="height: 300px; overflow: scroll;">';
exec('systemctl --type=service --state=running', $running_services);
echo '<table class="table table-bordered table-hover table-striped dataTable no-footer" style="margin-bottom: 10px;">';
echo '<thead>
		<tr role="row">
			<th style="padding: 8px;">Service Name</th>
			<th style="padding: 8px;">Service Description</th>
		</tr>
	  </thead>';
$table_color = 'odd';
for ($x = 0; $x < sizeof($running_services); $x++) {
	if (stristr($running_services[$x], '.service')) {
		$temp_services_arr = array_values(array_filter(explode(' ', trim($running_services[$x]))));
		$servives_name = $temp_services_arr[0];
		unset($temp_services_arr[0], $temp_services_arr[1], $temp_services_arr[2], $temp_services_arr[3]);
		$servives_description = implode(" ", $temp_services_arr);
		if ($table_color == 'odd') {$table_color = 'even';} else { $table_color = 'odd';}

		echo '<tr class="' . $table_color . '"><td style="padding: 3px; padding-left: 10px;">' . substr($servives_name, 0, -8) . '</td><td style="padding: 3px; padding-left: 10px;">' . $servives_description . '</td></tr>';
	}
}
echo '</table>';
echo '</div>';
echo '      </div>
      </div>';

// USB ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
               <h3 class="box-title sysinfo_headline"><i class="fab fa-usb"></i> USB Devices</h3>
            </div>
            <div class="box-body">';
echo '         <table class="table table-bordered table-hover table-striped dataTable no-footer" style="margin-bottom: 10px;">';

$table_color = 'odd';
sort($usb_devices_mount);
for ($x = 0; $x < sizeof($usb_devices_mount); $x++) {
	$cut_pos = strpos($usb_devices_mount[$x], ':');
	$usb_bus = substr($usb_devices_mount[$x], 0, $cut_pos);
	$usb_dev = substr($usb_devices_mount[$x], $cut_pos + 1);

	if ($table_color == 'odd') {$table_color = 'even';} else { $table_color = 'odd';}
	echo '<tr class="' . $table_color . '"><td style="padding: 3px; padding-left: 10px; width: 150px;"><b>' . str_replace('Device', 'Dev.', $usb_bus) . '</b></td><td style="padding: 3px; padding-left: 10px;">' . $usb_dev . '</td></tr>';
}
echo '         </table>';
echo '      </div>
      </div>';

// ----------------------------------------------------------

echo '<br>';

?>

</div>
</section>

    <!-- /.content -->
    <?php
      require 'php/templates/footer.php';
    ?>
  </div>
  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->
