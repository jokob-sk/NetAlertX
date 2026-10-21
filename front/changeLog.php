<?php
require 'php/templates/header.php';
?>
<div class="content-wrapper changeHistoryPage spinnerTarget" id="changeHistoryPage">
  <div class="content" >
    <div class="tab-content box">
      <?php
        require 'changeLogCore.php';
      ?>
    </div>
  </div>
</div>


<?php require 'php/templates/footer.php'; ?>
