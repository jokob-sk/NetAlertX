//--------------------------------------------------------------
// Pause / Resume automatic scans button
// Default pause duration (minutes) used for the single-click header button
function renderPauseResumeButton(pauseUntil) {
  const icon = document.getElementById('pause-resume-icon');
  const link = document.getElementById('pause-resume-button');
  if (!icon || !link) return;

  const isPaused = !!pauseUntil;
  icon.className = isPaused ? 'fa-solid fa-play' : 'fa-solid fa-pause';
  link.title = isPaused
    ? getString('Header_ResumeScans_Tooltip')
    : getString('Header_PauseScans_Tooltip');
}

// Updated whenever the SSE state manager receives a state_update event (see sse_manager.js)
document.addEventListener('nax:pauseStateUpdate', (e) => {
  renderPauseResumeButton(e.detail.pauseUntil);
});

function togglePauseScans() {
  const PAUSE_SCANS_DEFAULT_MINUTES = getSetting("UI_SCAN_PAUSE");
  const icon = document.getElementById('pause-resume-icon');
  const isPaused = icon && icon.classList.contains('fa-play');
  const apiBase = getApiBase();
  const apiToken = getSetting("API_TOKEN");
  const endpoint = isPaused ? '/scan/resume' : '/scan/pause';
  const success_msg = isPaused ? getString("Scans_Resumed") : getString("Scans_Paused");
  const payload = isPaused ? {} : { minutes: PAUSE_SCANS_DEFAULT_MINUTES };

  $.ajax({
    url: `${apiBase}${endpoint}`,
    method: "POST",
    contentType: "application/json",
    headers: { "Authorization": `Bearer ${apiToken}` },
    data: JSON.stringify(payload),
    error: function(xhr, status, error) {
      console.error("[Header] Error toggling scan pause:", status, error);
      showMessage(error, 5000, "modal_red");
    },
    success:function() {
      showMessage(success_msg);
    },
  });
}

