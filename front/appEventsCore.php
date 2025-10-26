<span class="helpIcon"> 
    <a target="_blank" href="https://github.com/jokob-sk/NetAlertX/blob/main/docs/WORKFLOWS_DEBUGGING.md">
      <i class="fa fa-circle-question"></i>
    </a>
  </span>
<section class="content">
  <div class="nav-tabs-custom app-event-content" style="margin-bottom: 0px;">
    <ul id="tabs-location" class="nav nav-tabs col-sm-2 hidden">
      <li class="left-nav"><a class="col-sm-12" href="#" id="" data-toggle="tab">Events</a></li>
    </ul>
    <div id="tabs-content-location" class="tab-content col-sm-12">
      <table class="table table-striped" id="appevents-table" data-my-dbtable="AppEvents"></table>
    </div>
  </div>
</section>



<script>

// show loading dialog
showSpinner()

$(document).ready(function() {

  // Load JSON data from the provided URL
  $.getJSON('php/server/query_json.php?file=table_appevents.json', function(data) {
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

  console.log(allData);
  

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
      { data: 'AppEventProcessed', title: getString('AppEvents_AppEventProcessed') },
      { data: 'AppEventType', title: getString('AppEvents_Type') }, 
      { data: 'ObjectType', title: getString('AppEvents_ObjectType') },
      { data: 'ObjectPrimaryID', title: getString('AppEvents_ObjectPrimaryID') },
      { data: 'ObjectSecondaryID', title: getString('AppEvents_ObjectSecondaryID') },
      { data: 'ObjectStatus', title: getString('AppEvents_ObjectStatus') },            
      { data: 'ObjectPlugin', title: getString('AppEvents_Plugin') },  
      { data: 'ObjectGUID', title: "Object GUID" },  
      { data: 'GUID', title: "Event GUID" },  
      // Add other columns as needed
    ],
    // Add column-specific configurations if needed
    columnDefs: [
      { className: 'text-center', targets: [4] },
      { width: '80px', targets: [7] },
      // ... Add other columnDefs as needed
      // Full MAC    
      {targets: [4, 5],
      'createdCell': function (td, cellData, rowData, row, col) {
        if (!emptyArr.includes(cellData)){
          $(td).html (createDeviceLink(cellData));
        } else {
          $(td).html ('');
        }
      } },
      // Processed 
      {targets: [1],
        'createdCell': function (td, cellData, rowData, row, col) {
          // console.log(cellData);
          $(td).html (cellData);          
        } 
      },
      // Datetime
      {targets: [0],
        'createdCell': function (td, cellData, rowData, row, col) {
          let timezone = $("#NAX_TZ").html(); // e.g., 'Europe/Berlin'
          let utcDate = new Date(cellData + ' UTC'); // Adding ' UTC' makes it interpreted as UTC time

          // Format the date in the desired timezone
          let options = {
              year: 'numeric',
              month: 'short',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false, // Use 24-hour format
              timeZone: timezone // Use the specified timezone
          };

          let localDate = new Intl.DateTimeFormat('en-GB', options).format(utcDate);

          // Update the table cell
          $(td).html(localDate);    
        } 
      },
    ]
  });


  // Activate the first tab
  $('#tabs-location li:first-child').addClass('active');
  $('#tabs-content-location .tab-pane:first-child').addClass('active');
}

</script>

