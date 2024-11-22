<section class="content">
    <div class="nav-tabs-custom app-event-content" style="margin-bottom: 0px;">
        <ul id="tabs-location" class="nav nav-tabs col-sm-2">
        <li class="left-nav"><a class="col-sm-12" href="#" id="" data-toggle="tab">Events</a></li>
        </ul>
        <div id="tabs-content-location" class="tab-content col-sm-10">
            <table class="table table-striped" id="appevents-table" data-my-dbtable="AppEvents"></table>
        </div>
    </div>
</section>

<script>

// show loading dialog
showSpinner()

$(document).ready(function() {

    // Load JSON data from the provided URL
    $.getJSON('api/table_appevents.json', function(data) {
        // Process the JSON data and generate UI dynamically        
        processData(data)

        // hide loading dialog
        hideSpinner()
    });
});

function processData(data) {
    // Create an object to store unique ObjectType values as app event identifiers
    var appEventIdentifiers = {};

    // Array to accumulate data for DataTable
    var allData = [];

    // Iterate through the data and generate tabs and content dynamically
    $.each(data.data, function(index, item) {
        
        // Accumulate data for DataTable
        allData.push(item);
        
    });

    // Initialize DataTable for all app events
    
    $('#appevents-table').DataTable({
        data: allData,
        paging: true,
        lengthChange: true,
        lengthMenu: [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, 'All']],
        searching: true,
        ordering: true,
        info: true,
        autoWidth: false,
        pageLength: 25, // Set the default paging to 25
        columns: [
            { data: 'DateTimeCreated', title: getString('AppEvents_DateTimeCreated') },
            { data: 'AppEventType', title: getString('AppEvents_Type') }, 
            { data: 'ObjectType', title: getString('AppEvents_ObjectType') },
            { data: 'ObjectPrimaryID', title: getString('AppEvents_ObjectPrimaryID') },
            { data: 'ObjectSecondaryID', title: getString('AppEvents_ObjectSecondaryID') },
            { data: 'ObjectStatus', title: getString('AppEvents_ObjectStatus') },            
            { data: 'Extra', title: getString('AppEvents_Extra') },    
            { data: 'ObjectPlugin', title: getString('AppEvents_Plugin') },    
            // Add other columns as needed
        ],
        // Add column-specific configurations if needed
        columnDefs: [
            { className: 'text-center', targets: [3] },
            { width: '80px', targets: [6] },
            // ... Add other columnDefs as needed
            // Full MAC      
            {targets: [3, 4],
            'createdCell': function (td, cellData, rowData, row, col) {
                if (!emptyArr.includes(cellData)){
                $(td).html (createDeviceLink(cellData));
                } else {
                $(td).html ('');
                }
            } },
        ]
    });


    // Activate the first tab
    $('#tabs-location li:first-child').addClass('active');
    $('#tabs-content-location .tab-pane:first-child').addClass('active');
}

</script>

<!-- Datatable -->
<link rel="stylesheet" href="lib/datatables.net-bs/css/dataTables.bootstrap.min.css"/>
<script src="lib/datatables.net/js/jquery.dataTables.min.js"></script>
<script src="lib/datatables.net-bs/js/dataTables.bootstrap.min.js"></script>
