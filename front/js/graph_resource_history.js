// Chart.js instances, kept so a range switch destroys the old chart before
// building a new one on the same canvas (Chart.js throws otherwise).
var resourceHistoryChartInstances = {};

// Monotonically increasing id, bumped on every initResourceHistoryGraphs()
// call. A fast double-click across two range buttons fires two overlapping
// AJAX requests; without this, whichever response lands last wins regardless
// of click order, so a stale response can silently overwrite newer data.
var resourceHistoryRequestId = 0;

// Chart axis labels: time only - date/year are dropped entirely to keep the
// axis readable; the full date (including year) is still available on
// hover via each chart's tooltip title callback below. Passed as
// localizeTimestamp()'s options override so parsing/timezone/locale logic
// stays in one shared place (common.js).
var CHART_TIMESTAMP_OPTIONS_AXIS = {
  hour: '2-digit', minute: '2-digit',
  hour12: false
};

// Full timestamp (including year) shown in the tooltip title on hover.
var CHART_TIMESTAMP_OPTIONS_TOOLTIP = {
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', second: '2-digit',
  hour12: false
};

/**
 * Fetches Resource_History data for the given range ('hour'/'day'/'week'/'month')
 * and renders the four Performance-tab charts, or shows the disabled-state
 * message when no rows exist yet (collection off, or just enabled).
 */
function initResourceHistoryGraphs(range) {
  var requestId = ++resourceHistoryRequestId;

  $.get('php/server/query_json.php', { file: `table_resource_history_${range}.json`, nocache: Date.now() }, function (res) {
    if (requestId !== resourceHistoryRequestId) {
      return; // a newer range request has since started - discard this stale response
    }

    var rows = (res && res.data) ? res.data : [];

    if (rows.length === 0) {
      $('#resourceHistoryCharts').addClass('myhidden');
      $('#resourceHistoryDisabledMessage').removeClass('myhidden');
      return;
    }

    $('#resourceHistoryDisabledMessage').addClass('myhidden');
    $('#resourceHistoryCharts').removeClass('myhidden');

    var labels = [];
    var fullLabels = [];
    var cpuData = [];
    var rssData = [];
    var ioReadData = [];
    var ioWriteData = [];
    var durationData = [];
    var tickFailed = [];

    function round2(n) {
      return n == null ? null : Math.round(n * 100) / 100;
    }

    rows.forEach(function (entry) {
      // hour/day rows carry resDateTime (raw); week/month rows carry bucket
      // (hourly rollup) instead - see const.py's sql_resource_history_* queries.
      var ts = entry.resDateTime || entry.bucket;
      labels.push(localizeTimestamp(ts, CHART_TIMESTAMP_OPTIONS_AXIS));
      fullLabels.push(localizeTimestamp(ts, CHART_TIMESTAMP_OPTIONS_TOOLTIP));
      cpuData.push(round2(entry.resCpuPercent));
      rssData.push(round2(entry.resRssMb));
      // Bytes -> MB and ms -> s: raw units from the DB aren't a readable axis scale.
      ioReadData.push(entry.resIoReadBytes != null ? round2(entry.resIoReadBytes / (1024 * 1024)) : null);
      ioWriteData.push(entry.resIoWriteBytes != null ? round2(entry.resIoWriteBytes / (1024 * 1024)) : null);
      durationData.push(entry.resScanDurationMs != null ? round2(entry.resScanDurationMs / 1000) : null);
      tickFailed.push(entry.resTickFailed == 1);
    });

    renderResourceHistoryCharts(labels, fullLabels, cpuData, rssData, ioReadData, ioWriteData, durationData, tickFailed);
  }).fail(function () {
    console.error('Error fetching resource history data.');
  });
}

/**
 * Builds/replaces the four small-multiple Resource_History charts (CPU%,
 * memory usage MB, IO read+write MB, scan duration seconds) on the same time
 * axis. Rows written from the tick-failure `finally` path (resTickFailed = 1)
 * are rendered as visually distinct points rather than plain data, since
 * their numbers may reflect a truncated, crash-adjacent sample. `labels`
 * (time-only, used for the axis) and `fullLabels` (full date+year, used for
 * the hover tooltip title) are parallel arrays over the same rows.
 */
function renderResourceHistoryCharts(labels, fullLabels, cpuData, rssData, ioReadData, ioWriteData, durationData, tickFailed) {
  var normalColor = "rgba(0, 166, 89, .8)";
  var failedColor = "#dd4b39";

  function pointColors(baseColor) {
    return tickFailed.map(function (failed) { return failed ? failedColor : baseColor; });
  }

  function destroyIfExists(key) {
    if (resourceHistoryChartInstances[key]) {
      resourceHistoryChartInstances[key].destroy();
    }
  }

  var commonScales = {
    yAxes: [{
      // maxTicksLimit caps how many labels Chart.js draws - without it, a
      // short/fixed-height chart crams in enough ticks that adjacent labels
      // visually overlap.
      ticks: { beginAtZero: true, fontColor: '#A0A0A0', maxTicksLimit: 5 },
      // Faint gridlines only at the (few, capped) main ticks - easier to
      // read a value off the chart without making it visually noisy.
      gridLines: { color: "rgba(160, 160, 160, 0.15)", zeroLineColor: "rgba(160, 160, 160, 0.3)" },
    }],
    xAxes: [{
      ticks: { fontColor: '#A0A0A0', maxTicksLimit: 10, autoSkip: true },
      gridLines: { color: "rgba(160, 160, 160, 0.15)", zeroLineColor: "rgba(160, 160, 160, 0.3)" },
    }],
  };

  // Axis labels are time-only (CHART_TIMESTAMP_OPTIONS_AXIS); show the full
  // date (including year) on hover instead, via fullLabels.
  var commonTooltips = {
    callbacks: {
      title: function (tooltipItems) {
        return fullLabels[tooltipItems[0].index];
      },
    },
  };

  destroyIfExists('cpu');
  resourceHistoryChartInstances.cpu = new Chart("ResourceCpuChart", {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: getString("Systeminfo_Performance_CPU"),
        data: cpuData,
        borderColor: normalColor,
        backgroundColor: "rgba(0, 166, 89, .2)",
        pointBackgroundColor: pointColors(normalColor),
        fill: true,
      }],
    },
    options: { legend: { display: true }, scales: commonScales, tooltips: commonTooltips, maintainAspectRatio: false, responsive: true },
  });

  destroyIfExists('rss');
  resourceHistoryChartInstances.rss = new Chart("ResourceRssChart", {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: getString("Systeminfo_Performance_Memory"),
        data: rssData,
        borderColor: "#3c8dbc",
        backgroundColor: "rgba(60, 141, 188, .2)",
        pointBackgroundColor: pointColors("#3c8dbc"),
        fill: true,
      }],
    },
    options: { legend: { display: true }, scales: commonScales, tooltips: commonTooltips, maintainAspectRatio: false, responsive: true },
  });

  destroyIfExists('io');
  resourceHistoryChartInstances.io = new Chart("ResourceIoChart", {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: getString("Systeminfo_Performance_IO_Read"),
          data: ioReadData,
          borderColor: "#00a65a",
          pointBackgroundColor: pointColors("#00a65a"),
          fill: false,
        },
        {
          label: getString("Systeminfo_Performance_IO_Write"),
          data: ioWriteData,
          borderColor: "#f39c12",
          pointBackgroundColor: pointColors("#f39c12"),
          fill: false,
        },
      ],
    },
    options: { legend: { display: true }, scales: commonScales, tooltips: commonTooltips, maintainAspectRatio: false, responsive: true },
  });

  destroyIfExists('duration');
  resourceHistoryChartInstances.duration = new Chart("ResourceDurationChart", {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: getString("Systeminfo_Performance_Duration"),
        data: durationData,
        borderColor: "#b2b6be",
        backgroundColor: "rgba(178, 182, 190, .2)",
        pointBackgroundColor: pointColors("#b2b6be"),
        fill: true,
      }],
    },
    options: { legend: { display: true }, scales: commonScales, tooltips: commonTooltips, maintainAspectRatio: false, responsive: true },
  });
}
