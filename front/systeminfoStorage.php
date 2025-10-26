<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/server/db.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/language/lang.php';
?>



<?php

// ----------------------------------------------------------
// Storage
// ----------------------------------------------------------

//HDD stats
$hdd_result = shell_exec(" df -P  | awk '{print $1}'");
$hdd_devices = explode("\n", trim($hdd_result));
$hdd_result = shell_exec(" df -P  | awk '{print $2}'");
$hdd_devices_total = explode("\n", trim($hdd_result));
$hdd_result = shell_exec(" df -P  | awk '{print $3}'");
$hdd_devices_used = explode("\n", trim($hdd_result));
$hdd_result = shell_exec(" df -P  | awk '{print $4}'");
$hdd_devices_free = explode("\n", trim($hdd_result));
$hdd_result = shell_exec(" df -P  | awk '{print $5}'");
$hdd_devices_percent = explode("\n", trim($hdd_result));
$hdd_result = shell_exec(" df -P  | awk '{print $6}'");
$hdd_devices_mount = explode("\n", trim($hdd_result));

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

// ----------------------------------------------------------
// USB devices
// ----------------------------------------------------------

$usb_result = shell_exec("lsusb");
$usb_devices_mount = explode("\n", trim($usb_result));

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

<script>
  hideSpinner();
</script>