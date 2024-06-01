<?php
require 'php/templates/header.php';
?>

<!-- Datatable -->
<link rel="stylesheet" href="lib/AdminLTE/bower_components/datatables.net-bs/css/dataTables.bootstrap.min.css">
<link rel="stylesheet" href="lib/AdminLTE/bower_components/datatables.net/css/select.dataTables.min.css">
<script src="lib/AdminLTE/bower_components/datatables.net/js/jquery.dataTables.min.js"></script>
<script src="lib/AdminLTE/bower_components/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>
<script src="lib/AdminLTE/bower_components/datatables.net/js/dataTables.select.min.js"></script>

<div id="notifications" class="content-wrapper">
    <table id="notificationsTable" class="table table-bordered table-hover table-striped display">
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>GUID</th>
                <th>Read</th>
                <th>Level</th>
                <th>Content</th>
            </tr>
        </thead>
        <tbody>
            <!-- Data will be inserted here by DataTables -->
        </tbody>
    </table>
</div>
<script>
    function fetchData(callback) {
        $.ajax({
            url: '/api/user_notifications.json',
            method: 'GET',
            dataType: 'json',
            success: function(response) {
                console.log(response);
                if (response == "[]" || response == "") {
                    callback([]);
                } else if (response.error) {
                    alert("Error: " + response.error);
                    callback([]);
                } else if (!Array.isArray(response)) {
                    alert("Unexpected response format");
                    callback([]);
                } else {
                    callback(response);
                }
            },
            error: function(xhr, status, error) {
                console.log("An error occurred while fetching data: " + error);
                callback([]);
            }
        });
    }

    $(document).ready(function() {
        const table = $('#notificationsTable').DataTable({
            "columns": [
                { "data": "timestamp" },
                { "data": "guid" },
                { "data": "read" },
                { "data": "level" },
                {
                    "data": "content",
                    "render": function(data, type, row) {
                        return `<span class="btn-show-message">${data}</span>`;
                    }
                }
            ],
            "columnDefs": [
                { "width": "10%", "targets": [0] }, // Set width of the first four columns to 10%
                { "width": "20%", "targets": [1] }, // Set width of the first four columns to 10%
                { "width": "5%", "targets": [2, 3] }, // Set width of the first four columns to 10%
                { "width": "60%", "targets": 4 } // Set width of the "Content" column to 60%
            ]
        });

        fetchData(function(data) {
            table.clear().rows.add(data).draw();
        });
    });
</script>

<?php
require 'php/templates/footer.php';
?>
