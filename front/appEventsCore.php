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

$(document).ready(function () {

  const protocol = window.location.protocol.replace(':', '');
  const host = window.location.hostname;
  const apiToken = getSetting("API_TOKEN");
  const port = getSetting("GRAPHQL_PORT");
  const graphqlUrl = `${protocol}://${host}:${port}/graphql`;

  $('#appevents-table').DataTable({
    processing: true,
    serverSide: true,
    paging: true,
    searching: true,
    ordering: true,
    pageLength: 25,
    lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],

    ajax: function (dtRequest, callback) {

      const page = Math.floor(dtRequest.start / dtRequest.length) + 1;
      const limit = dtRequest.length;

      // ---- SEARCH ----
      const searchValue = dtRequest.search?.value || null;

      // ---- SORTING ----
      let sort = [];
      if (dtRequest.order && dtRequest.order.length > 0) {
        const order = dtRequest.order[0];
        const columnName = dtRequest.columns[order.column].data;

        sort.push({
          field: columnName,
          order: order.dir
        });
      }

      const query = `
        query AppEvents($options: PageQueryOptionsInput) {
          appEvents(options: $options) {
            count
            appEvents {
              DateTimeCreated
              AppEventProcessed
              AppEventType
              ObjectType
              ObjectPrimaryID
              ObjectSecondaryID
              ObjectStatus
              ObjectPlugin
              ObjectGUID
              GUID
            }
          }
        }
      `;

      const variables = {
        options: {
          page: page,
          limit: limit,
          search: searchValue,
          sort: sort
        }
      };

      $.ajax({
        method: "POST",
        url: graphqlUrl,
        headers: {
          "Authorization": "Bearer " + apiToken,
          "Content-Type": "application/json"
        },
        data: JSON.stringify({
          query: query,
          variables: variables
        }),
        success: function (response) {
          if (response.errors) {
            console.error(response.errors);
            callback({
              data: [],
              recordsTotal: 0,
              recordsFiltered: 0
            });
            return;
          }

          const result = response.data.appEvents;

          callback({
            data: result.appEvents,
            recordsTotal: result.count,
            recordsFiltered: result.count
          });

          hideSpinner();
        },
        error: function () {
          callback({
            data: [],
            recordsTotal: 0,
            recordsFiltered: 0
          });
        }
      });
    },

    columns: [
      { data: 'DateTimeCreated', title: getString('AppEvents_DateTimeCreated') },
      { data: 'AppEventProcessed', title: getString('AppEvents_AppEventProcessed') },
      { data: 'AppEventType', title: getString('AppEvents_Type') },
      { data: 'ObjectType', title: getString('AppEvents_ObjectType') },
      { data: 'ObjectPrimaryID', title: getString('AppEvents_ObjectPrimaryID') },
      { data: 'ObjectSecondaryID', title: getString('AppEvents_ObjectSecondaryID') },
      { data: 'ObjectStatus', title: getString('AppEvents_ObjectStatus') },
      { data: 'ObjectPlugin', title: getString('AppEvents_Plugin') },
      { data: 'ObjectGUID', title: 'Object GUID' },
      { data: 'GUID', title: 'Event GUID' }
    ],

    columnDefs: [
      { className: 'text-center', targets: [1, 4] },
      { width: '90px', targets: [7] },

      // Device links
      {
        targets: [4, 5],
        createdCell: function (td, cellData) {
          if (!emptyArr.includes(cellData)) {
            $(td).html(createDeviceLink(cellData));
          } else {
            $(td).html('');
          }
        }
      },

      // Date formatting
      {
        targets: [0],
        createdCell: function (td, cellData) {
          let timezone = $("#NAX_TZ").html();
          let utcDate = new Date(cellData + ' UTC');

          let options = {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            timeZone: timezone
          };

          $(td).html(
            new Intl.DateTimeFormat('en-GB', options).format(utcDate)
          );
        }
      }
    ]
  });


});


</script>

