// -----------------------------------------------------------------------------
// General utilities to interact with the database
// -----------------------------------------------------------------------------


// --------------------------------------------------
// Read data and place intotarget location, callback processies the results
function readData(sqlQuery, processDataCallback, valuesArray, targetLocation, targetField, nameTransformer) {
    var apiUrl = `php/server/dbHelper.php?action=read&rawSql=${encodeURIComponent(sqlQuery)}`;
    $.get(apiUrl, function(data) {
        // Process the JSON data using the provided callback function

        data = JSON.parse(data)

        var htmlResult = processDataCallback(data, valuesArray, targetField, nameTransformer);

        // Place the resulting HTML into the specified placeholder div
        $("#" + targetLocation).replaceWith(htmlResult);
    });
}

// --------------------------------------------------
// Check if database is locked
function checkDbLock() {
    $.ajax({
        url: 'php/server/dbHelper.php', // Replace with the actual path to your PHP file
        type: 'GET',
        data: { action: 'checkLock' },
        success: function(response) {
            if (response == 1) {
                console.log('🟥 Database is locked');            
                $(".header-status-locked-db").show()    
            } else {
                // console.log('Database is not locked');
                $(".header-status-locked-db").hide()  
            }
        },
        error: function() {
            console.log('🟥 Error checking database lock status');
            $(".header-status-locked-db").show()
        }
    });
}

// Start the loop
setInterval(() => {
    checkDbLock();
}, 1000);
