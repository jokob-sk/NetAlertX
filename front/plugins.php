<?php

  require 'php/templates/header.php';
?>
<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

    <!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
        <?php require 'php/templates/notification.php'; ?>
        <h1 id="pageTitle">
            <i class="fa fa-fw fa-plug"></i> <?= lang('Navigation_Plugins');?>
            <span class="pageHelp"> <a target="_blank" href="https://github.com/jokob-sk/Pi.Alert/tree/main/front/plugins"><i class="fa fa-circle-question"></i></a><span>
        </h1>    
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">
        <div class="tab-pane active" id="curState">
            <div>
                <h2 class="page-header"><i class="fa fa-clock"></i> Current state</h2>
            </div>
            aaa
        </div>
    </section>

    
</div>

<?php
  require 'php/templates/footer.php';
?>

<script src="js/pialert_common.js"></script>