<div id="events-skeleton" class="spinnerTarget">

  <!-- 6 stat tiles -->
  <div class="row">
    <?php for ($i = 0; $i < 6; $i++): ?>
    <div class="col-lg-2 col-sm-4 col-xs-6">
      <div class="skel-tile">
        <div class="skel-tile-inner">
          <span class="skel-tile-num   skel-shimmer"></span>
          <span class="skel-tile-label skel-shimmer"></span>
        </div>
        <div class="skel-tile-icon-area">
          <span class="skel-tile-icon-shape skel-shimmer"></span>
        </div>
      </div>
    </div>
    <?php endfor; ?>
  </div>

  <!-- events table -->
  <div class="row" style="margin-top:12px">
    <div class="col-xs-12">
      <div class="skel-table-box">
        <div class="skel-box-header">
          <span class="skel-line skel-shimmer" style="width:120px"></span>
          <span class="skel-line skel-shimmer" style="width:90px; margin-left:auto;"></span>
        </div>
        <div class="skel-table-header-row">
          <?php for ($i = 0; $i < 6; $i++): ?>
          <span class="skel-th skel-shimmer"></span>
          <?php endfor; ?>
        </div>
        <?php for ($i = 0; $i < 20; $i++): ?>
        <div class="skel-tr">
          <?php for ($j = 0; $j < 6; $j++): ?>
          <span class="skel-td skel-shimmer"></span>
          <?php endfor; ?>
        </div>
        <?php endfor; ?>
      </div>
    </div>
  </div>

</div>
