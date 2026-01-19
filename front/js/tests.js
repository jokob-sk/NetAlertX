const requiredFiles = [
    'app_state.json',
    'plugins.json',
    'table_devices.json',
    'table_devices_filters.json',
    'table_devices_tiles.json',
    'table_notifications.json',
    'table_online_history.json',
    'table_appevents.json',
    'table_custom_endpoint.json',
    'table_events_pending_alert.json',
    'table_plugins_events.json',
    'table_plugins_history.json',
    'table_plugins_language_strings.json',
    'table_plugins_objects.json',
    'table_settings.json',
    'user_notifications.json'
  ];

  const internalChecks = ['isAppInitialized', 'isGraphQLServerRunning'];

  const fileStatus = {}; // Track file check results

  function updateFileStatusUI(file, status) {
    const item = $(`#file-${file.replace(/[^a-z0-9]/gi, '-')}`);
    const icon = item.find('span.icon-wrap');

    if (status === 'ok') {
      icon.html('<i class="fa-solid fa-check "></i>');
    } else if (status === 'fail') {
      icon.html('<i class="fa-solid fa-xmark "></i>');
    } else {
      icon.html('<i class="fa-solid fa-spinner fa-spin text-secondary"></i>');
    }
  }


  function checkAppInitializedJson() {
    requiredFiles.forEach(file => {
      $.get('php/server/query_json.php', { file, nocache: Date.now() })
        .done(() => {
          if (fileStatus[file] !== 'ok') {
            fileStatus[file] = 'ok';
            updateFileStatusUI(file, 'ok');
          }
        })
        .fail(() => {
          fileStatus[file] = 'fail';
          updateFileStatusUI(file, 'fail');
        });
    });

    const allOk = requiredFiles.every(file => fileStatus[file] === 'ok');

    if (allOk) {
      checkInternalStatusAfterFiles();
    } else {
      setTimeout(checkAppInitializedJson, 5000);
    }
  }


  function checkInternalStatusAfterFiles() {
    const promises = [
      waitForAppInitialized().then(() => {
        fileStatus['isAppInitialized'] = 'ok';
        updateFileStatusUI('isAppInitialized', 'ok');
      }).catch(() => {
        fileStatus['isAppInitialized'] = 'fail';
        updateFileStatusUI('isAppInitialized', 'fail');
      }),

      waitForGraphQLServer().then(() => {
        fileStatus['isGraphQLServerRunning'] = 'ok';
        updateFileStatusUI('isGraphQLServerRunning', 'ok');
      }).catch(() => {
        fileStatus['isGraphQLServerRunning'] = 'fail';
        updateFileStatusUI('isGraphQLServerRunning', 'fail');
      })
    ];

    Promise.allSettled(promises).then(() => {
      const allPassed = internalChecks.every(key => fileStatus[key] === 'ok');
      if (allPassed) {
        $('#check-status').show();
        $('#check-status-plc').hide();
      } else {
        setTimeout(checkInternalStatusAfterFiles, 5000);
      }
    });
  }
  function waitForAppInitialized() {
    return new Promise((resolve, reject) => {
      if (isAppInitialized()) {
        resolve();
      } else {
        reject();
      }
    });
  }

// Initial UI setup for all items
function checkAppInitializedJsonInit() {
  const allItems = [...requiredFiles, ...internalChecks];

  allItems.forEach(file => {


    $('#file-check-list').append(`
      <div class="panel panel-secondary col-xs-6 col-sm-4 col-md-3 col-lg-2 col-xxl-1 padding-5px">
        <div class="file-checking border rounded p-2 d-flex flex-column justify-content-between h-100" id="file-${file.replace(/[^a-z0-9]/gi, '-')}">
          <div class="d-flex align-items-center gap-2 mb-2">
            <span class="file-name-wrap flex-grow-1 text-truncate" title="${file}">${file}</span>
            <span class="icon-wrap align-items-center text-center"><i class="fa-solid fa-spinner fa-spin text-secondary"></i></span>
          </div>
        </div>
      </div>
    `);

    fileStatus[file] = 'checking';
  });

  checkAppInitializedJson();
}








