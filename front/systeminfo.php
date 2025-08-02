<?php
#---------------------------------------------------------------------------------#
#  NetAlertX                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #  
#                                                                                 #
#  systeminfo.php - Front module. Server side. System Information                 #
#---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
#---------------------------------------------------------------------------------#

  require 'php/templates/header.php';
?>
<?php require 'php/templates/notification.php'; ?>
<!-- ----------------------------------------------------------------------- -->
 

<script>

  // show spinning icon
  showSpinner()

  var selectedTab         = 'tabServer';
</script>

<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">	
    <div class="row">
        <div class="col-lg-12 col-sm-12 col-xs-12">
        <!-- <div class="box-transparent"> -->
          <div id="navSysInfo" class="nav-tabs-custom">
            <ul class="nav nav-tabs" style="font-size:16px;">
              <li> 
                <a id="tabServer"  href="#panServer"  data-toggle="tab"> 
                  <i class="fa fa-info-circle"></i> 
                    <span class="dev-detail-tab-name"> 
                      <?= lang('Systeminfo_System');?>  
                    </span>
                </a>
                </li>
                <li> 
                <a id="tabNetwork"    href="#panNetwork"    data-toggle="tab"> 
                  <i class="fa fa-sitemap fa-rotate-270"></i> 
                    <span class="dev-detail-tab-name">
                      <?= lang('Systeminfo_Network');?>    
                    </span>
                </a>
                </li>
              <li> 
                <a id="tabStorage" href="#panStorage" data-toggle="tab"> 
                  <i class="fa fa-hdd"></i> 
                    <span class="dev-detail-tab-name">
                      <?= lang('Systeminfo_Storage');?> 
                    </span>
                </a>
                </li>
            </ul>
            
            <div class="tab-content" style="min-height: 430px;">

<!-- tab page  ------------------------------------------------------------ -->

              <div class="tab-pane fade" data-php-file="systeminfoServer.php" id="panServer">
               <!-- PLACEHOLDER -->
              </div>                                                                         
        
<!-- tab page  ------------------------------------------------------------ -->

              <div class="tab-pane fade" data-php-file="systeminfoNetwork.php" id="panNetwork">
                 <!-- PLACEHOLDER -->     	        
              </div>

<!-- tab page  ------------------------------------------------------------ -->
              <div class="tab-pane fade table-responsive" data-php-file="systeminfoStorage.php" id="panStorage">
               <!-- PLACEHOLDER -->
              </div>

            </div>
            <!-- /.tab-content -->
          </div>
          <!-- /.nav-tabs-custom -->

          <!-- </div> -->
        </div>
        <!-- /.col -->
      </div>

    </section>

    <!-- /.content -->
    <?php
      require 'php/templates/footer.php';
    ?>
  </div>
  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->

<script>

// function initializeTabs () {  

//   key ="activeSysinfoTab"

//   // Activate panel
//   if(!emptyArr.includes(getCache(key)))
//   {
//     selectedTab = getCache(key);
//   }

//   $('.nav-tabs a[id='+ selectedTab +']').tab('show');

//   // When changed save new current tab
//   $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
//     setCache(key, $(e.target).attr('id'))
  
//     var target = $(e.target).attr("href") // activated tab

//     if (target === '#panStorage' && !$(target).data('loaded')) {
//       // Load content only once

//       showSpinner();
//       $(target).load('systeminfoStorage.php', function () {
//         $(target).data('loaded', true);
//       });
//     }    
//   });
// }

// window.onload = function async()
// {
//   initializeTabs();  
// }


function loadTabContent(target) {
  const $tab = $(target);
  const phpFile = $tab.data('php-file');

  console.log(phpFile);
  console.log(target);
  console.log($tab );
  

  if (phpFile && !$tab.data('loaded')) {
    showSpinner();
    $tab.load(phpFile, function () {
      $tab.data('loaded', true);
    });
  }
}

function initializeTabs() {
  const key = "activeSysinfoTab";
  let selectedTab = "#panServer"; // fallback default

  const cached = getCache(key);
  if (!emptyArr.includes(cached)) {
    selectedTab = cached;
  }

  console.log(selectedTab);
  
  // Activate the correct tab
  const $tabLink = $('.nav-tabs a[id="' + selectedTab + '"]');
  $tabLink.tab('show');

  // Get the pane's ID from the tab's href attribute
  const targetSelector = $tabLink.attr("href");
  loadTabContent(targetSelector);

  // On tab change
  $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    const newTabId = $(e.target).attr('id');
    setCache(key, newTabId);

    const newTarget = $(e.target).attr("href");
    loadTabContent(newTarget);
  });
}

window.onload = function async() {
  initializeTabs();  
}

</script>
