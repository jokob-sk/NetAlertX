<?php
  require 'php/templates/header.php';
?>
<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
         <?= lang('HelpFAQ_Title');?>
      </h1>
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">
      <h4>
        <i class="fa fa-question"></i>
        <?= lang('HelpFAQ_Cat_General');?>
      </h4>

       <div class="panel-group" id="accordion_gen">
        <div class="panel panel-default">

          <div class="panel-heading">
            <h4 class="panel-title">
              <a data-toggle="collapse" data-parent="#accordion_gen" href="#collapse100">
              <?= lang('HelpFAQ_Cat_General_100_head');?></a>
            </h4>
          </div>

          <div id="collapse100" class="panel-collapse collapse" style="font-size: 16px;">
            <div class="panel-body"><?= lang('HelpFAQ_Cat_General_100_text_a');?>
              <span class="text-danger help_faq_code"><?php echo date_default_timezone_get(); ?></span><br>
              <?= lang('HelpFAQ_Cat_General_100_text_b');?> 
              <span class="text-danger help_faq_code"><?php echo php_ini_loaded_file(); ?></span><br>
              <?= lang('HelpFAQ_Cat_General_100_text_c');?>
            </div>
          </div>

        </div>

        
        <div class="panel panel-default">
          <div class="panel-heading">
            <h4 class="panel-title">
              <a data-toggle="collapse" data-parent="#accordion_gen" href="#collapse101">
              <?= lang('HelpFAQ_Cat_General_101_head');?></a>
            </h4>
          </div>
          <div id="collapse101" class="panel-collapse collapse" style="font-size: 16px;">
            <div class="panel-body">
              <?= lang('HelpFAQ_Cat_General_101_text');?>
            </div>
          </div>
        </div>
        <div class="panel panel-default">
          <div class="panel-heading">
            <h4 class="panel-title">
              <a data-toggle="collapse" data-parent="#accordion_gen" href="#collapse102">
              <?= lang('HelpFAQ_Cat_General_102_head');?></a>
            </h4>
          </div>
          <div id="collapse102" class="panel-collapse collapse" style="font-size: 16px;">
            <div class="panel-body">
              <?= lang('HelpFAQ_Cat_General_102_text');?>
            </div>
          </div>
        </div>
        <div class="panel panel-default">
          <div class="panel-heading">
            <h4 class="panel-title">
              <a data-toggle="collapse" data-parent="#accordion_gen" href="#collapse102docker">
              <?= lang('HelpFAQ_Cat_General_102docker_head');?></a>
            </h4>
          </div>
          <div id="collapse102docker" class="panel-collapse collapse" style="font-size: 16px;">
            <div class="panel-body">
              <?= lang('HelpFAQ_Cat_General_102docker_text');?>
            </div>
          </div>
        </div>
        <div class="panel panel-default">
          <div class="panel-heading">
            <h4 class="panel-title">
              <a data-toggle="collapse" data-parent="#accordion_gen" href="#collapse103">
              <?= lang('HelpFAQ_Cat_General_103_head');?></a>
            </h4>
          </div>
          <div id="collapse103" class="panel-collapse collapse" style="font-size: 16px;">
            <div class="panel-body">
              <?= lang('HelpFAQ_Cat_General_103_text');?>
            </div>
          </div>
          <div class="panel panel-default">
          <div class="panel-heading">
            <h4 class="panel-title">
              <a data-toggle="collapse" data-parent="#accordion_net" href="#collapse601">
              <?= lang('HelpFAQ_Cat_Network_601_head');?></a>
            </h4>
          </div>
          <div id="collapse601" class="panel-collapse collapse" style="font-size: 16px;">
            <div class="panel-body">
              <?= lang('HelpFAQ_Cat_Network_601_text');?>
            </div>
          </div>
        </div>
        </div>
      </div> 

<h4>
  <i class="fa fa-laptop"></i>
  <?= lang('Navigation_Devices');?>
</h4>
 <div class="panel-group" id="accordion_dev">
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion_dev" href="#collapse200">
        <?= lang('HelpFAQ_Cat_Device_200_head');?></a>
      </h4>
    </div>
    <div id="collapse200" class="panel-collapse collapse" style="font-size: 16px;">
      <div class="panel-body">
         <?= lang('HelpFAQ_Cat_Device_200_text');?>
      </div>
    </div>
  </div>
</div> 


<h4>
  <i class="fa fa-info-circle"></i><?= lang('HelpFAQ_Cat_Detail');?></h4>
 <div class="panel-group" id="accordion_det">
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion_det" href="#collapse300">
        <?= lang('HelpFAQ_Cat_Detail_300_head');?> "<?= lang('DevDetail_MainInfo_Network');?>" / "<?= lang('DevDetail_MainInfo_Network_Port');?>"?</a>
      </h4>
    </div>
    <div id="collapse300" class="panel-collapse collapse" style="font-size: 16px;">
      <div class="panel-body">
        "<?= lang('DevDetail_MainInfo_Network');?>" <?= lang('HelpFAQ_Cat_Detail_300_text_a');?><br>
        "<?= lang('DevDetail_MainInfo_Network_Port');?>" <?= lang('HelpFAQ_Cat_Detail_300_text_b');?>
      </div>
    </div>
  </div>
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion_det" href="#collapse301">
        <?= lang('HelpFAQ_Cat_Detail_301_head_a');?> "<?= lang('DevDetail_EveandAl_ScanCycle');?>" <?= lang('HelpFAQ_Cat_Detail_301_head_b');?></a>
      </h4>
    </div>
    <div id="collapse301" class="panel-collapse collapse" style="font-size: 16px;">
      <div class="panel-body">
        <?= lang('HelpFAQ_Cat_Detail_301_text');?>
      </div>
    </div>
  </div>
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion_det" href="#collapse302">
        <?= lang('HelpFAQ_Cat_Detail_302_head_a');?> "<?= lang('DevDetail_EveandAl_RandomMAC');?>" <?= lang('HelpFAQ_Cat_Detail_302_head_b');?></a>
      </h4>
    </div>
    <div id="collapse302" class="panel-collapse collapse" style="font-size: 16px;">
      <div class="panel-body">
        <?= lang('HelpFAQ_Cat_Detail_302_text');?>
      </div>
    </div>
  </div>
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion_det" href="#collapse303">
        <?= lang('HelpFAQ_Cat_Detail_303_head');?></a>
      </h4>
    </div>
    <div id="collapse303" class="panel-collapse collapse" style="font-size: 16px;">
      <div class="panel-body">
        <?= lang('HelpFAQ_Cat_Detail_303_text');?>
      </div>
    </div>

  </div>
</div> 

<h4>
  <i class="fa fa-calendar"></i>
  <?= lang('Navigation_Presence');?>
</h4>
 <div class="panel-group" id="accordion_pre">
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion_pre" href="#collapse400">
        <?= lang('HelpFAQ_Cat_Presence_400_head');?></a>
      </h4>
    </div>
    <div id="collapse400" class="panel-collapse collapse" style="font-size: 16px;">
      <div class="panel-body">
        <?= lang('HelpFAQ_Cat_Presence_400_text');?>
      </div>
    </div>
  </div>
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion_pre" href="#collapse401">
        <?= lang('HelpFAQ_Cat_Presence_401_head');?></a>
      </h4>
    </div>
    <div id="collapse401" class="panel-collapse collapse" style="font-size: 16px;">
      <div class="panel-body">
        <?= lang('HelpFAQ_Cat_Presence_401_text');?>
      </div>
    </div>
  </div>
</div> 

<h4>
  <i class="fa fa-network-wired"></i><?= lang('Navigation_Network');?></h4>
 <div class="panel-group" id="accordion_net">
  <div class="panel panel-default">
    <div class="panel-heading">
      <h4 class="panel-title">
        <a data-toggle="collapse" data-parent="#accordion_net" href="#collapse600">
        <?= lang('HelpFAQ_Cat_Network_600_head');?></a>
      </h4>
    </div>
    <div id="collapse600" class="panel-collapse collapse" style="font-size: 16px;">
      <div class="panel-body">
        <?= lang('HelpFAQ_Cat_Network_600_text');?>
      </div>
    </div>
  
</div> 

    </section>
    <!-- /.content -->
</div>
  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>
