<?php

  require 'php/templates/header.php';  
  require 'php/templates/modals.php'; 
?>
<!-- ----------------------------------------------------------------------- -->
 

<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper" id="wf-content-wrapper">
<span class="helpIcon"> <a target="_blank" href="https://github.com/jokob-sk/NetAlertX/blob/main/docs/WORKFLOWS.md"><i class="fa fa-circle-question"></i></a></span>
<?php
   require 'workflowsCore.php';
?>

        
</div>

<?php
  require 'php/templates/footer.php';
?>