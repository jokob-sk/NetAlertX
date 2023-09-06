<?php
#---------------------------------------------------------------------------------#
#  Pi.Alert                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #  
#                                                                                 #
#  systeminfo.php - Front module. Server side. System Information                 #
#---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
#---------------------------------------------------------------------------------#

  require 'php/templates/header.php';
?>
<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
       <i class="fa fa-microchip"></i>
       <?= lang('SYSTEM_TITLE') ;?>
      </h1>
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">	

<?php
//General stats
// Date & Time
$date = new DateTime();
$formatted_date = $date->format('l, F j, Y H:i:s'); // Get date
$formatted_date2 = $date->format('d/m/Y H:i:s'); // Get date2
$formatted_date3 = $date->format('Y/m/d H:i:s'); // Get date3
//System stats
// OS-Version
$os_version = '';
// Raspbian
if ($os_version == '') {$os_version = exec('cat /etc/os-release | grep PRETTY_NAME');}
// Dietpi
if ($os_version == '') {$os_version = exec('uname -o');}
//$os_version_arr = explode("\n", trim($os_version));
$stat['os_version'] = str_replace('"', '', str_replace('PRETTY_NAME=', '', $os_version));
$stat['uptime'] = str_replace('up ', '', shell_exec("uptime -p")); // Get system uptime
$system_namekernel = shell_exec("uname");  // Get system name kernel 
$system_namesystem = shell_exec("uname -o");  // Get name system
$system_full = shell_exec("uname -a");  // Get system full
$system_architecture = shell_exec("uname -m"); // Get system Architecture
$load_average = sys_getloadavg(); // Get load average
$system_process_count = shell_exec("ps -e --no-headers | wc -l"); // Count processes
//Motherboard stats
$motherboard_name = shell_exec('cat /sys/class/dmi/id/board_name'); // Get the Motherboard name
$motherboard_manufactured = shell_exec('cat /sys/class/dmi/id/board_vendor'); // Get the Motherboard manufactured
$motherboard_revision = shell_exec('cat /sys/class/dmi/id/board_version'); // Get the Motherboard revision
$motherboard_bios = shell_exec('cat /sys/class/dmi/id/bios_version'); // Get the Motherboard BIOS
$motherboard_biosdate = shell_exec('cat /sys/class/dmi/id/bios_date'); // Get the Motherboard BIOS date
$motherboard_biosvendor = shell_exec('cat /sys/class/dmi/id/bios_vendor'); // Get the Motherboard BIOS vendor
//CPU stats
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
$cpu_temp = shell_exec('cat /sys/class/hwmon/hwmon0/temp1_input'); // Get the CPU temperature
$cpu_temp = floatval($cpu_temp) / 1000; // Convert the temperature to degrees Celsius
$cpu_vendor = exec('cat /proc/cpuinfo | grep "vendor_id" | cut -d ":" -f 2' ); // Get the CPU vendor
//Memory stats
$total_memorykb = shell_exec("cat /proc/meminfo | grep MemTotal | awk '{print $2}'");
$total_memorykb = trim($total_memorykb);
$total_memorykb = number_format($total_memorykb, 0, '.', '.');
$total_memorymb = shell_exec("cat /proc/meminfo | grep MemTotal | awk '{print $2/1024}'");
$total_memorymb = trim($total_memorymb);
$total_memorymb = number_format($total_memorymb, 0, '.', '.');
$mem_used = round(memory_get_usage() / 1048576 * 100, 2);
$memory_usage_percent = round(($mem_used / $total_memorymb), 2);
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
//Network stats
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
//USB devices
$usb_result = shell_exec("lsusb");
$usb_devices_mount = explode("\n", trim($usb_result));

// General ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-info-circle"></i> ' . lang('Systeminfo_General') . '</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_general_a">' . lang('Systeminfo_General_Full_Date') . '</div>
                  <div class="col-sm-9 sysinfo_general_b">' . $formatted_date . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_general_a">' . lang('Systeminfo_General_Date') . '</div>
                  <div class="col-sm-9 sysinfo_general_b">' . $formatted_date2 . '</div>
                </div>            
                <div class="row">
                  <div class="col-sm-3 sysinfo_general_a">' . lang('Systeminfo_General_Date2') . '</div>
                  <div class="col-sm-9 sysinfo_general_b">' . $formatted_date3 . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_general_a">' . lang('Systeminfo_General_TimeZone') . '</div>
                  <div class="col-sm-9 sysinfo_general_b">' . $timeZone . '</div>
                </div>                                        
            </div>
      </div>';

// Client ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-globe"></i> ' . lang('Systeminfo_This_Client') . '</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_client_a">' . lang('Systeminfo_Client_User_Agent') . '</div>
                  <div class="col-sm-9 sysinfo_client_b">' . $_SERVER['HTTP_USER_AGENT'] . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_client_a">' . lang('Systeminfo_Client_Resolution') . '</div>
                  <div class="col-sm-9 sysinfo_client_b" id="resolution"></div>
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
              <h3 class="box-title sysinfo_headline"><i class="fa fa-computer"></i> ' . lang('Systeminfo_System') . '</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_system_a">' . lang('Systeminfo_System_Uptime') . '</div>
                  <div class="col-sm-9 sysinfo_system_b">' . $stat['uptime'] . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_system_a">' . lang('Systeminfo_System_Kernel') . '</div>
                  <div class="col-sm-9 sysinfo_system_b">' . $system_namekernel . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_system_a">' . lang('Systeminfo_System_System') . '</div>
                  <div class="col-sm-9 sysinfo_system_b">' . $system_namesystem . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_system_a">' . lang('Systeminfo_System_OSVersion') . '</div>
                  <div class="col-sm-9 sysinfo_system_b">' . $stat['os_version'] . '</div>
                </div>				
                <div class="row">
                  <div class="col-sm-3 sysinfo_system_a">' . lang('Systeminfo_System_Uname') . '</div>
                  <div class="col-sm-9 sysinfo_system_b">' . $system_full . '</div>
                </div>	
                <div class="row">
                  <div class="col-sm-3 sysinfo_system_a">' . lang('Systeminfo_System_Architecture') . '</div>
                  <div class="col-sm-9 sysinfo_system_b">' . $system_architecture . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_system_a">' . lang('Systeminfo_System_AVG') . '</div>
                  <div class="col-sm-9 sysinfo_system_b">'. $load_average[0] .' '. $load_average[1] .' '. $load_average[2] .'</div>
                </div>
		<div class="row">
  		  <div class="col-sm-3 sysinfo_system_a">' . lang('Systeminfo_System_Running_Processes') . '</div>
		  <div class="col-sm-9 sysinfo_system_b">' . $system_process_count . '</div>
		</div>		
            </div>
      </div>';

// Motherboard ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-laptop-code"></i> ' . lang('Systeminfo_Motherboard') . '</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_motherboard_a">' . lang('Systeminfo_Motherboard_Name') . '</div>
                  <div class="col-sm-9 sysinfo_motherboard_b">' . $motherboard_name . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_motherboard_a">' . lang('Systeminfo_Motherboard_Manufactured') . '</div>
                  <div class="col-sm-9 sysinfo_motherboard_b">' . $motherboard_manufactured . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_motherboard_a">' . lang('Systeminfo_Motherboard_Revision') . '</div>
                  <div class="col-sm-9 sysinfo_motherboard_b">' . $motherboard_revision. '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_motherboard_a">' . lang('Systeminfo_Motherboard_BIOS') . '</div>
                  <div class="col-sm-9 sysinfo_motherboard_b">' . $motherboard_bios . '</div>
                </div>				
                <div class="row">
                  <div class="col-sm-3 sysinfo_motherboard_a">' . lang('Systeminfo_Motherboard_BIOS_Date') . '</div>
                  <div class="col-sm-9 sysinfo_motherboard_b">' . $motherboard_biosdate . '</div>
                </div>	
                <div class="row">
                  <div class="col-sm-3 sysinfo_motherboard_a">' . lang('Systeminfo_Motherboard_BIOS_Vendor') . '</div>
                  <div class="col-sm-9 sysinfo_motherboard_b">' . $motherboard_biosvendor . '</div>
                </div>
            </div>
      </div>';

// CPU ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-microchip"></i> ' . lang('Systeminfo_CPU') . '</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_cpu_a">' . lang('Systeminfo_CPU_Vendor') . '</div>
                  <div class="col-sm-9 sysinfo_cpu_b">' . $cpu_vendor . '</div>
                </div>			
                <div class="row">
                  <div class="col-sm-3 sysinfo_cpu_a">' . lang('Systeminfo_CPU_Name') . '</div>
                  <div class="col-sm-9 sysinfo_cpu_b">' . $stat['cpu_model'] . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_cpu_a">' . lang('Systeminfo_CPU_Cores') . '</div>
                  <div class="col-sm-9 sysinfo_cpu_b">' . $stat['cpu'] . '</div>
                </div>
                <div class="row">
                  <div class="col-sm-3 sysinfo_cpu_a">' . lang('Systeminfo_CPU_Speed') . '</div>
                  <div class="col-sm-9 sysinfo_cpu_b">' . $stat['cpu_frequ'] . ' MHz</div>
                </div>				
                <div class="row">
                  <div class="col-sm-3 sysinfo_cpu_a">' . lang('Systeminfo_CPU_Temp') . '</div>
                  <div class="col-sm-9 sysinfo_cpu_b">'. $cpu_temp .' °C</div>
                </div>';
				  // Get the number of CPU cores
				  $num_cpus = $stat['cpu'];
				  $num_cpus = $num_cpus +2;

				  // Iterate over the CPU cores
				  for ($i = 2,$a = 0; $i < $num_cpus; $i++,$a++) {

					// Get the CPU temperature
					$cpu_tempxx = shell_exec('cat /sys/class/hwmon/hwmon0/temp' . $i . '_input');

					// Convert the temperature to degrees Celsius
					$cpu_tempxx = floatval($cpu_tempxx) / 1000;

					// Print the CPU temperature
					echo '<div class="row">
					  <div class="col-sm-3 sysinfo_cpu_a">CPU Temp ' . $a . ':</div>
					  <div class="col-sm-9 sysinfo_cpu_b">' . $cpu_tempxx . ' °C</div>
					</div>';
				}
			echo '				
            </div>
      </div>';
      
// Memory ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-memory"></i> ' . lang('Systeminfo_Memory') . '</h3>
            </div>
            <div class="box-body">
                <div class="row">
                  <div class="col-sm-3 sysinfo_memory_a">' . lang('Systeminfo_Memory_Usage_Percent') . '</div>
                  <div class="col-sm-9 sysinfo_memory_b">' . $memory_usage_percent . ' %</div>
                </div>                 
				<div class="row">
                  <div class="col-sm-3 sysinfo_memory_a">' . lang('Systeminfo_Memory_Usage') . '</div>
                  <div class="col-sm-9 sysinfo_memory_b">' . $mem_used . ' MB / ' . $total_memorymb . ' MB</div>
                </div>               
                <div class="row">
                  <div class="col-sm-3 sysinfo_memory_a">' . lang('Systeminfo_Memory_Total_Memory') . '</div>
                  <div class="col-sm-9 sysinfo_memory_b">' . $total_memorymb  . ' MB (' . $total_memorykb . ' KB)</div>
                </div>
            </div>
      </div>';

// Storage ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-hdd"></i> ' . lang('Systeminfo_Storage') . '</h3>
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

for ($x = 0; $x < sizeof($storage_lsblk_line); $x++) {
	echo '<div class="row">';
	if (preg_match('~[0-9]+~', $storage_lsblk_line[$x][0])) {
		echo '<div class="col-sm-4 sysinfo_storage_a">"' . lang('Systeminfo_Storage_Mount') . ' ' . $storage_lsblk_line[$x][3] . '"</div>';
	} else {
		echo '<div class="col-sm-4 sysinfo_storage_a">"' . str_replace('_', ' ', $storage_lsblk_line[$x][3]) . '"</div>';
	}
	echo '<div class="col-sm-3 sysinfo_storage_b">' . lang('Systeminfo_Storage_Device') . ' /dev/' . $storage_lsblk_line[$x][0] . '</div>';
	echo '<div class="col-sm-2 sysinfo_storage_b">' . lang('Systeminfo_Storage_Size') . ' ' . $storage_lsblk_line[$x][1] . '</div>';
	echo '<div class="col-sm-2 sysinfo_storage_b">' . lang('Systeminfo_Storage_Type') . ' ' . $storage_lsblk_line[$x][2] . '</div>';
	echo '</div>';
}
echo '      </div>
      </div>';

// Storage usage ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-hdd"></i> ' . lang('Systeminfo_Storage_Usage') . '</h3>
            </div>
            <div class="box-body">';
for ($x = 0; $x < sizeof($hdd_devices); $x++) {
	if (stristr($hdd_devices[$x], '/dev/')) {
		if (!stristr($hdd_devices[$x], '/loop')) {
		if ($hdd_devices_total[$x] == 0 || $hdd_devices_total[$x] == '') {$temp_total = 0;} else { $temp_total = number_format(round(($hdd_devices_total[$x] / 1024 / 1024), 2), 2, ',', '.'); $temp_total = trim($temp_total);}
		if ($hdd_devices_used[$x] == 0 || $hdd_devices_used[$x] == '') {$temp_used = 0;} else { $temp_used = number_format(round(($hdd_devices_used[$x] / 1024 / 1024), 2), 2, ',', '.'); $temp_used = trim($temp_total);}
		if ($hdd_devices_free[$x] == 0 || $hdd_devices_free[$x] == '') {$temp_free = 0;} else { $temp_free = number_format(round(($hdd_devices_free[$x] / 1024 / 1024), 2), 2, ',', '.'); $temp_free = trim($temp_total);}
		echo '<div class="row">';
		echo '<div class="col-sm-4 sysinfo_storage_usage_a">"' . lang('Systeminfo_Storage_Usage_Mount') . ' ' . $hdd_devices_mount[$x] . '"</div>';
		echo '<div class="col-sm-2 sysinfo_storage_usage_b">' . lang('Systeminfo_Storage_Usage_Total') . ' ' . $temp_total . ' GB</div>';
		echo '<div class="col-sm-3 sysinfo_storage_usage_b">' . lang('Systeminfo_Storage_Usage_Used') . ' ' . $temp_used . ' GB (' . $hdd_devices_percent[$x]. ')</div>';
		echo '<div class="col-sm-2 sysinfo_storage_usage_b">' . lang('Systeminfo_Storage_Usage_Free') . ' ' . $temp_free . ' GB</div>';
		echo '</div>';
		}
	}
}
#echo '<br>' . $lang['SysInfo_storage_note'];
echo '      </div>
      </div>';

// Network ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fas fa-ethernet"></i> ' . lang('Systeminfo_Network') . '</h3>
            </div>
            <div class="box-body">
			<div class="row">
			  <div class="col-sm-3 sysinfo_network_a">' . lang('Systeminfo_Network_IP') . '</div>
			  <div class="col-sm-9 sysinfo_network_b">' . shell_exec("curl https://ifconfig.co") . '</div>
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

// Network Hardware ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fas fa-network-wired"></i> ' . lang('Systeminfo_Network_Hardware') . '</h3>
            </div>
            <div class="box-body">';

for ($x = 0; $x < sizeof($net_interfaces); $x++) {
	$interface_name = str_replace(':', '', $net_interfaces[$x]);
	$interface_ip_temp = exec('ip addr show ' . $interface_name . ' | grep "inet "');
	$interface_ip_arr = explode(' ', trim($interface_ip_temp));

	if (!isset($interface_ip_arr[1])) {$interface_ip_arr[1] = '--';}

	if ($net_interfaces_rx[$x] == 0) {$temp_rx = 0;} else { $temp_rx = number_format(round(($net_interfaces_rx[$x] / 1024 / 1024), 2), 2, ',', '.');}
	if ($net_interfaces_tx[$x] == 0) {$temp_tx = 0;} else { $temp_tx = number_format(round(($net_interfaces_tx[$x] / 1024 / 1024), 2), 2, ',', '.');}
	echo '<div class="row">';
	echo '<div class="col-sm-2 sysinfo_network_hardware_a">' . $interface_name . '</div>';
	echo '<div class="col-sm-2 sysinfo_network_hardware_b">' . $interface_ip_arr[1] . '</div>';
	echo '<div class="col-sm-3 sysinfo_network_hardware_b">RX: <div class="sysinfo_network_value">' . $temp_rx . ' MB</div></div>';
	echo '<div class="col-sm-3 sysinfo_network_hardware_b">TX: <div class="sysinfo_network_value">' . $temp_tx . ' MB</div></div>';
	echo '</div>';

}
echo '      </div>
      </div>';

// Services ----------------------------------------------------------
echo '<div class="box box-solid">
            <div class="box-header">
              <h3 class="box-title sysinfo_headline"><i class="fa fa-database"></i> ' . lang('Systeminfo_Services') . '</h3>
            </div>
            <div class="box-body">';
echo '<div style="height: 300px; overflow: scroll;">';
exec('systemctl --type=service --state=running', $running_services);
echo '<table class="table table-bordered table-hover table-striped dataTable no-footer" style="margin-bottom: 10px;">';
echo '<thead>
		<tr role="row">
			<th style="padding: 8px;">' . lang('Systeminfo_Services_Name') . '</th>
			<th style="padding: 8px;">' . lang('Systeminfo_Services_Description') . '</th>   
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
               <h3 class="box-title sysinfo_headline"><i class="fab fa-usb"></i> ' . lang('Systeminfo_USB_Devices') . '</h3>
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
