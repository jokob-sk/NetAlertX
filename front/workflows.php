<?php

  require 'php/templates/header.php';  
  require 'php/templates/notification.php'; 
?>
<!-- ----------------------------------------------------------------------- -->
 

<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
<section class="content-header">
        
        <h1 id="pageTitle">
            <i class="fa fa-fw fa-plug"></i> <?= lang('Navigation_Workflows');?>
            <span class="pageHelp"> <a target="_blank" href="https://github.com/jokob-sk/NetAlertX/tree/main/front/plugins"><i class="fa fa-circle-question"></i></a><span>
        </h1>    
    </section>


<?php
   require 'appEventsCore.php';
?>

        
</div>

<?php
  require 'php/templates/footer.php';
?>