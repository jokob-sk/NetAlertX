<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/server/db.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/language/lang.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/globals.php';
?>

    <div class="col-lg-12 col-sm-12 col-xs-12">

        <div class="col-lg-12 col-sm-12 col-xs-12 text-center" id="check-status-plc" >
          <div class="alert alert-warning">
            <i class="fa-solid fa-spinner fa-spin text-secondary"></i> <?= lang('Maintenance_InitCheck_Checking');?>
          </div>
        </div>
        <div class="col-lg-12 col-sm-12 col-xs-12 text-center" id="check-status" style="display: none;">
          <div class="alert alert-success">
            <i class="fa-solid fa-check text-success"></i> <?= lang('Maintenance_InitCheck_Success');?>
          </div>
        </div>       
        <div class="col-lg-12 col-sm-12 col-xs-12">
          <div class="flex-wrap" id="file-check-list"></div>
        </div>
        <div class="col-lg-12 col-sm-12 col-xs-12">
          <div class="text-center">
            <p class="text-muted"><?= lang('Maintenance_InitCheck_QuickSetupGuide');?></p>
          </div>
        </div>
        <div class="col-lg-12 col-sm-12 col-xs-12 init-check-button">
          <div class="col-lg-12 col-sm-12 col-xs-12 " >
            <button type="button" class="col-lg-12 col-sm-12 col-xs-12  btn btn-default bg-green " onclick="retryCheck()"><?= lang('Maintenance_ReCheck');?></button>
          </div>
        </div>

    </div>

<script>

  function retryCheck() {
    // re-set page
    $('#file-check-list').empty();
    $('#check-status').hide();
    $('#check-status-plc').show();
    // re-run check
    checkAppInitializedJsonInit();
  }

  $(document).ready(() => {
    checkAppInitializedJsonInit();
    hideSpinner();
  });
</script>