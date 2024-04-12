<?php require 'php/templates/notification.php'; ?>

<script>

var migrationNeeded = <?php
// Check if either file exists
$configFile = '/home/pi/pialert/conf/pialert.conf';
$databaseFile = '/home/pi/pialert/db/pialert.db';

if (file_exists($configFile) || file_exists($databaseFile)) {
    
    echo 'true';

} else {echo 'false'; }
?>

console.log(`migrationNeeded = ${migrationNeeded}`);


if(migrationNeeded == true)
{
    message = getString("TICKER_MIGRATE_TO_NETALERTX")

    setTimeout(() => {
        showTickerAnnouncement(message)
    },100);
}

</script>

