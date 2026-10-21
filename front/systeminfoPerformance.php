<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/server/db.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/language/lang.php';
?>

<script src="js/graph_resource_history.js"></script>

<div class="box box-solid">
  <div class="box-header">
    <h3 class="box-title sysinfo_headline"><i class="fa fa-chart-line"></i> <?= lang('Systeminfo_Performance');?>
      <a href="https://docs.netalertx.com/PERFORMANCE" target="_blank"><i class="fa fa-circle-question" style="font-size: 14px;"></i></a>
    </h3>
  </div>
  <div class="box-body">

    <div class="btn-group" role="group" id="resourceHistoryRangeGroup" style="margin-bottom: 15px;">
      <button type="button" class="btn btn-default resource-history-range-btn" data-range="hour"><?= lang('Gen_Hour');?></button>
      <button type="button" class="btn btn-default resource-history-range-btn active" data-range="day"><?= lang('Gen_Day');?></button>
      <button type="button" class="btn btn-default resource-history-range-btn" data-range="week"><?= lang('Gen_Week');?></button>
      <button type="button" class="btn btn-default resource-history-range-btn" data-range="month"><?= lang('Gen_Month');?></button>
    </div>

    <div id="resourceHistoryDisabledMessage" class="myhidden" style="padding: 15px;">
      <?= lang('Systeminfo_Performance_Disabled');?>
    </div>

    <div id="resourceHistoryCharts">
      <div style="position: relative; height: 220px; width: 100%; margin-bottom: 25px;">
        <canvas id="ResourceCpuChart"></canvas>
      </div>
      <div style="position: relative; height: 220px; width: 100%; margin-bottom: 25px;">
        <canvas id="ResourceRssChart"></canvas>
      </div>
      <div style="position: relative; height: 220px; width: 100%; margin-bottom: 5px;">
        <canvas id="ResourceIoChart"></canvas>
      </div>
      <p class="text-muted" style="font-size: 12px; margin-bottom: 25px;"><?= lang('Systeminfo_Performance_IO_Caption');?></p>
      <div style="position: relative; height: 220px; width: 100%; margin-bottom: 15px;">
        <canvas id="ResourceDurationChart"></canvas>
      </div>
    </div>

  </div>
</div>

<script>

  if (isAppInitialized()) {
    initResourceHistoryGraphs('day');
  } else {
    callAfterAppInitialized(() => initResourceHistoryGraphs('day'));
  }

  $('#resourceHistoryRangeGroup .resource-history-range-btn').on('click', function () {
    $('#resourceHistoryRangeGroup .resource-history-range-btn').removeClass('active');
    $(this).addClass('active');
    initResourceHistoryGraphs($(this).data('range'));
  });

  hideSpinner();

</script>
