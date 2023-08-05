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

?>
<?php
  error_reporting(0);// Turn off php errors
  require 'php/templates/header.php';
?>
<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
       <!--  <?= lang('System_Title') ;?> -->
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
//cpu stat
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
//memory stat
$total_memory = shell_exec("cat /proc/meminfo | grep MemTotal | cut -d' ' -f2-") / 1024 | bc;
$mem_result = shell_exec("cat /proc/meminfo | grep MemTotal");
$stat['mem_total'] = round(preg_replace("#[^0-9]+(?:\.[0-9]*)?#", "", $mem_result) / 1024 / 1024, 3);
$stat['mem_used'] = round(memory_get_usage() / 1048576, 2);
$memory_usage_percent = round($mem_used * 100, 2);
//Load System
$load_average = sys_getloadavg();
//Date & Time
$date = new DateTime();
$formatted_date = $date->format('l, F j, Y H:i:s');
$formatted_date2 = $date->format('d/m/Y H:i:s');
$formatted_date3 = $date->format('Y/m/d H:i:s');
//hdd stat
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
				<div class="row">
				  <div class="col-sm-3 sysinfo_gerneral_a">Uptime</div>
				  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['uptime'] . '</div>
				</div>
				<div class="row">
				  <div class="col-sm-3 sysinfo_gerneral_a">Operating System</div>
				  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['os_version'] . '</div>
				</div>
				<div class="row">
				  <div class="col-sm-3 sysinfo_gerneral_a">CPU Name:</div>
				  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['cpu_model'] . '</div>
				</div>
				<div class="row">
				  <div class="col-sm-3 sysinfo_gerneral_a">CPU Cores:</div>
				  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['cpu'] . ' @ ' . $stat['cpu_frequ'] . ' MHz</div>
				</div>
				<div class="row">
				  <div class="col-sm-3 sysinfo_gerneral_a">Memory:</div>
				  <div class="col-sm-9 sysinfo_gerneral_b">' . $stat['mem_used'] . ' MB / ' . $stat['mem_total'] . ' MB</div>
				</div>
				<div class="row">
				  <div class="col-sm-3 sysinfo_gerneral_a">Memory %:</div>
				  <div class="col-sm-9 sysinfo_gerneral_b">' . $memory_usage_percent . ' %</div>
				</div>				
				<div class="row">
				  <div class="col-sm-3 sysinfo_gerneral_a">Total memory:</div>
				  <div class="col-sm-9 sysinfo_gerneral_b">' . $total_memory  . ' MB</div>
				</div>
				<div class="row">
				  <div class="col-sm-3 sysinfo_gerneral_a">Load AVG:</div>
				  <div class="col-sm-9 sysinfo_gerneral_b">'. $load_average[0] .' '. $load_average[1] .' '. $load_average[2] .'</div>
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
