// -----------------------------------------------------------------------------
// General utilities to interact with teh database
// -----------------------------------------------------------------------------

// Read data and place intotarget location, callback processies the results
function readData(sqlQuery, processDataCallback, valuesArray, targetLocation) {
    var apiUrl = `php/server/dbHelper.php?action=read&rawSql=${encodeURIComponent(sqlQuery)}`;
    $.get(apiUrl, function(data) {
        // Process the JSON data using the provided callback function

        data = JSON.parse(data)

        var htmlResult = processDataCallback(data, valuesArray);

        // Place the resulting HTML into the specified placeholder div
        $("#" + targetLocation).replaceWith(htmlResult);
    });
}