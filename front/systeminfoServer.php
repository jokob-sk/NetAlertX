<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/server/db.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/language/lang.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/globals.php';
?>

<?php

// ----------------------------------------------------------
// Server
// ----------------------------------------------------------

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

    if ($table_color == 'odd') 
    {
      $table_color = 'even';
    } else 
    { 
      $table_color = 'odd';
    }
    echo '<tr class="' . $table_color . '"><td style="padding: 3px; padding-left: 10px;">' . substr($servives_name, 0, -8) . '</td><td style="padding: 3px; padding-left: 10px;">' . $servives_description . '</td></tr>';
  }
}
    echo '</table>';
  echo '</div>';
echo '      </div>
  </div>';


?>

<script>
  hideSpinner();
</script>