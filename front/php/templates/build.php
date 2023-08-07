<?php
	$file = "/home/pi/pialert/front/buildtimestamp.txt";
	if (file_exists($file)) {
		echo date("Y-m-d", ((int)file_get_contents($file)));
	} else {
		echo "File not found";
	}
?>
