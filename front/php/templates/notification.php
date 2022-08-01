<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  notificacion.php - Front module. Common notification & modal window
#-------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
#--------------------------------------------------------------------------- -->


<!-- Modal Default -->
<div class="modal fade" id="modal-default" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header" style="background-color: #d0d0d0;">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-default-title" class="modal-title"> Modal Default Title </h4>
      </div>

      <div id="modal-default-message" class="modal-body"> Modal Default message </div>

      <div class="modal-footer">
        <button id="modal-default-cancel" type="button" class="btn btn-default pull-left" style="min-width: 80px;" data-dismiss="modal">       Cancel </button>
        <button id="modal-default-OK"     type="button" class="btn btn-primary"           style="min-width: 80px;" onclick="modalDefaultOK()"> OK     </button>
      </div>
    </div>
    <!-- /.modal-content -->
  </div>
  <!-- /.modal-dialog -->
</div>
          

<!-- Modal warning -->
<div class="modal modal-warning fade" id="modal-warning" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-warning-title" class="modal-title"> Modal Title </h4>
      </div>

      <div id="modal-warning-message" class="modal-body"> Modal message </div>

      <div class="modal-footer">
        <button id="modal-warning-cancel" type="button" class="btn btn-outline pull-left" style="min-width: 80px;" data-dismiss="modal">       Cancel </button>
        <button id="modal-warning-OK"     type="button" class="btn btn-outline"           style="min-width: 80px;" onclick="modalWarningOK()"> OK     </button>
      </div>

    </div>
  </div>
</div>


<!-- Alert float -->
<div id="notification" class="alert alert-dimissible pa_alert_notification">
  <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
  <div id="alert-message"> Alert message </div>
</div>

