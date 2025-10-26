<!-- ---------------------------------------------------------------------------
#  NetAlertX
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  notificacion.php - Front module. Common notification & modal window
#-------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
#--------------------------------------------------------------------------- -->

<!-- Modal Ok -->
<div class="modal fade" id="modal-ok" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-ok-title" class="modal-title"> Modal Default Title </h4>
      </div>

      <div id="modal-ok-message" class="modal-body"> Modal Default message </div>

      <div class="modal-footer">
        <button id="modal-ok-OK" type="button" class="btn btn-primary btn-modal-submit" style="min-width: 80px;" data-dismiss="modal"> OK </button>
      </div>
    </div>
    <!-- /.modal-content -->
  </div>
  <!-- /.modal-dialog -->
</div>

<!-- Modal Default -->
<div class="modal fade" id="modal-default" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-default-title" class="modal-title"> Modal Default Title </h4>
      </div>

      <div id="modal-default-message" class="modal-body"> Modal Default message </div>

      <div class="modal-footer">
        <button id="modal-default-cancel" type="button" class="btn btn-default pull-left" style="min-width: 80px;" data-dismiss="modal"> Cancel </button>
        <button id="modal-default-OK" type="button" class="btn btn-primary btn-modal-submit" style="min-width: 80px;" onclick="modalDefaultOK()"> OK </button>
      </div>
    </div>
    <!-- /.modal-content -->
  </div>
  <!-- /.modal-dialog -->
</div>

<!-- Modal Default Str -->
<div class="modal fade" id="modal-str" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-str-title" class="modal-title"> Modal Default Title </h4>
      </div>

      <div id="modal-str-message" class="modal-body"> Modal Default message </div>

      <div class="modal-footer">
        <button id="modal-str-cancel" type="button" class="btn btn-default pull-left" style="min-width: 80px;" data-dismiss="modal"> Cancel </button>
        <button id="modal-str-OK" type="button" class="btn btn-primary btn-modal-submit" style="min-width: 80px;"> OK </button>
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
        <button id="modal-warning-cancel" type="button" class="btn btn-outline pull-left" style="min-width: 80px;" data-dismiss="modal"> Cancel </button>
        <button id="modal-warning-OK" type="button" class="btn btn-outline btn-modal-submit" style="min-width: 80px;" onclick="modalWarningOK()"> OK </button>
      </div>

    </div>
  </div>
</div>

<!-- Modal textarea input -->
<div class="modal modal-warning fade" id="modal-input" data-myparam-triggered-by="" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-input-title" class="modal-title"> Modal Title </h4>
      </div>

      <div id="modal-input-message" class="modal-body"> Modal message </div>

      <textarea id="modal-input-textarea" class="logs" cols="30" rows="3" wrap='off' autofocus ></textarea>

      <div class="modal-footer">
        <button id="modal-input-cancel" type="button" class="btn btn-outline pull-left" style="min-width: 80px;" data-dismiss="modal"> Cancel </button>
        <button id="modal-input-OK" type="button" class="btn btn-outline btn-modal-submit" style="min-width: 80px;" onclick="modalDefaultInput()"> OK </button>
      </div>

    </div>
  </div>
</div>

<!-- Modal form input -->
<div class="modal fade" id="modal-form" data-myparam-triggered-by="" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-form-title" class="modal-title"> Modal Title </h4>
      </div>

      <div id="modal-form-message" class="modal-body"> Modal message </div>

      <div id="modal-form-plc"></div>

      <div class="modal-footer">
        <button id="modal-form-cancel" type="button" class="btn btn-outline pull-left" style="min-width: 80px;" data-dismiss="modal"> Cancel </button>
        <button id="modal-form-OK" type="button" class="btn btn-outline btn-modal-submit" style="min-width: 80px;" > OK </button>
      </div>

    </div>
  </div>
</div>


<!-- Modal field input -->
<div class="modal modal-warning fade" id="modal-field-input" data-myparam-triggered-by="" style="display: none;">
  <div class="modal-dialog">
    <div class="modal-content">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 id="modal-field-input-title" class="modal-title"> Modal Title </h4>
      </div>

      <div id="modal-field-input-message" class="modal-body"> Modal message </div>

      <input id="modal-field-input-field" class="modal-field-input" type="text" onfocus="this.value = this.value;" autofocus ></input>

      <div class="modal-footer">
        <button id="modal-field-input-cancel" type="button" class="btn btn-outline pull-left" style="min-width: 80px;" data-dismiss="modal">
          Cancel
        </button>
        <button id="modal-field-input-OK" type="button" class="btn btn-outline btn-modal-submit" style="min-width: 80px;" onclick="modalDefaultFieldInput()">
          OK
        </button>
      </div>

    </div>
  </div>
</div>


<!-- Alert float -->
<div id="notification_modal" class="alert alert-dimissible notification_modal" >
  <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
  <div id="alert-message"> Alert message </div>
</div>


<!-- Sticky Announcement -->
<div id="tickerAnnouncement" class="ticker_announcement myhidden">
  <div id="ticker-message"> Announcement message </div>
</div>



