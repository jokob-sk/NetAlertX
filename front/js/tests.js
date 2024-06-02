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






