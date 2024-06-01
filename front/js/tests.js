// --------------------------------------------------
// Check if database is locked
function lockDatabase(delay=20) {
    $.ajax({
        url: 'php/server/dbHelper.php', // Replace with the actual path to your PHP file
        type: 'GET',
        data: { action: 'lockDatabase', delay: delay },
        success: function(response) { 
            console.log('Executed');      
        },
        error: function() {
            console.log('Error ocurred');            
        }
    });

    let times = delay; 
    let countdownInterval = setInterval(() => {
        times--;
        console.log(`Remaining time: ${times} seconds`);
        
        if (times <= 0) {
            clearInterval(countdownInterval);
            console.log('Countdown finished');
        }
    }, 1000);
}


function writeNotification(content, level) {

    const phpEndpoint = 'php/server/utilNotification.php';

    $.ajax({
        url: phpEndpoint, // Change this to the path of your PHP script
        type: 'GET',
        data: {
            action: 'write_notification',
            content: content,
            level: level
        },
        success: function(response) {
            alert('Notification written successfully.');
        },
        error: function(xhr, status, error) {
            console.error('Error writing notification:', error);
        }
    });
}



