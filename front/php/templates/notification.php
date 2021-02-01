<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  notificacion.php - Front module. Common notification & modal window
#-------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
#--------------------------------------------------------------------------- -->

<!-- Modal warning -->
<div class="modal modal-warning fade" id="modal-warning" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-title" class="modal-title"> Modal Title </h4>
      </div>

      <div id="modal-message" class="modal-body"> Modal message </div>

      <div class="modal-footer">
        <button id="modal-cancel" type="button" class="btn btn-outline pull-left" data-dismiss="modal"> Cancel </button>
        <button id="modal-OK"     type="button" class="btn btn-outline"           onclick="modalOK()">  OK     </button>
      </div>

    </div>
  </div>
</div>

<!-- Alert float -->
<div id="notification" class="alert alert-dimissible pa_alert_notification">
  <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
  <div id="alert-message"> Alert message </div>
</div>
