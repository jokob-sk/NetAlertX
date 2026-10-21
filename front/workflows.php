<?php

  require 'php/templates/header.php';
?>
<!-- ----------------------------------------------------------------------- -->


<!-- Page ------------------------------------------------------------------ -->
<div id="wf-content-wrapper" class="content-wrapper spinnerTarget" >
<?php require 'php/templates/skel_workflows.php'; ?>
<span class="helpIcon"> 
  <a target="_blank" href="https://docs.netalertx.com/WORKFLOWS"><i class="fa fa-circle-question"></i></a>
</span>
<?php
   require 'workflowsCore.php';
?>


</div>

<?php
  require 'php/templates/footer.php';
?>