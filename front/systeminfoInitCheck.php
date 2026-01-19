<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/server/db.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/language/lang.php';
  require_once $_SERVER['DOCUMENT_ROOT'] . '/php/templates/globals.php';
?>

    <div class="col-md-12">
      <div class="py-5">
        <div class="mt-4 text-center" id="check-status-plc" >
          <div class="alert alert-warning">
            <i class="fa-solid fa-spinner fa-spin text-secondary"></i> <?= lang('Maintenance_InitCheck_Checking');?>
          </div>
        </div>
        <div class="mt-4 text-center" id="check-status" style="display: none;">
          <div class="alert alert-success">
            <i class="fa-solid fa-check text-success"></i> <?= lang('Maintenance_InitCheck_Success');?>
          </div>
        </div>

        <div class="row">
          <div class="col-12">
            <div class="d-flex flex-wrap gap-2 w-100" id="file-check-list"></div>
          </div>
        </div>
        <div class="row">
          <div class="text-center box box-secondary col-md-6">
            <p class="text-muted"><?= lang('Maintenance_InitCheck_QuickSetupGuide');?></p>
          </div>
        </div>
        <div class="row">
          <div class="col-md-12 center text-center" >
              <button type="button" class=" col-md-12 btn btn-default bg-green " onclick="retryCheck()"><?= lang('Maintenance_ReCheck');?></button>
            </div>
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