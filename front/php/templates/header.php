<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  header.php - Front module. Common header to all the web pages 
#-------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
#--------------------------------------------------------------------------- -->

<?php
require dirname(__FILE__).'/../server/init.php';
require dirname(__FILE__).'/security.php';

?>

<!DOCTYPE html> 
<html>

<!-- ----------------------------------------------------------------------- -->
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <link rel="manifest" href="img/manifest.json">
  <title>Pi.Alert - <?php echo gethostname();?></title>

  <!-- Tell the browser to be responsive to screen width -->
  <meta content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" name="viewport">
  <!-- ----------------------------------------------------------------------- -->
  <!-- REQUIRED JS SCRIPTS -->
  <!-- jQuery 3 -->
  <script src="lib/AdminLTE/bower_components/jquery/dist/jquery.min.js"></script>

  <script src="js/pialert_common.js"></script>

  <!-- Bootstrap 3.3.7 -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/bootstrap/dist/css/bootstrap.min.css">
  

  <!-- Font Awesome -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/font-awesome/css/fontawesome.min.css">
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/font-awesome/css/solid.css">
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/font-awesome/css/brands.css">
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/font-awesome/css/v5-font-face.css">

  <!-- Ionicons -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/Ionicons/css/ionicons.min.css">

  <!-- Theme style -->
  <link rel="stylesheet" href="lib/AdminLTE/dist/css/AdminLTE.min.css">

  <!-- AdminLTE Skins. We have chosen the skin-blue for this starter
        page. However, you can choose any other skin. Make sure you
        apply the skin class to the body tag so the changes take effect. -->
  <link rel="stylesheet" href="lib/AdminLTE/dist/css/skins/<?php echo $pia_skin_selected;?>.min.css">

  <!-- Pi.Alert CSS -->
  <link rel="stylesheet" href="css/pialert.css">

  <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
  <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
  <!--[if lt IE 9]>
    <script src="https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"></script>
    <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
  <![endif]-->

  <!-- Google Font -->
  <!-- <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,600,700,300italic,400italic,600italic"> -->
  <link rel="stylesheet" href="css/offline-font.css">
  <link rel="icon" type="image/x-icon" href="img/pialertLogoOrange.png">

  <!-- For better UX on Mobile Devices using the Shortcut on the Homescreen -->
  <link rel="manifest" href="img/manifest.json">  
  <!-- Dark-Mode Patch -->
<?php
if ($ENABLED_DARKMODE === True) {
   echo '<link rel="stylesheet" href="css/dark-patch.css">';
   $BACKGROUND_IMAGE_PATCH='style="background-image: url(\'img/boxed-bg-dark.png\');"';
} else { $BACKGROUND_IMAGE_PATCH='style="background-image: url(\'img/background.png\');"';}
?>


<!-- Servertime to the right of the hostname -->
<script>

  function updateState(){
    $.get('api/app_state.json?nocache=' + Date.now(), function(appState) {    

      document.getElementById('state').innerHTML = appState["currentState"].replaceAll('"', '');

      setTimeout("updateState()", 1000);
        
    })
  }

  function show_pia_servertime() {

    // datetime in timeZone in the "en-UK" locale
    let time = new Date().toLocaleString("en-UK", { timeZone: "<?php echo $timeZone?>" });

    if (document.getElementById) { 
      document.getElementById("PIA_Servertime_place").innerHTML = '('+time+')'; 
    } 
    
    setTimeout("show_pia_servertime()", 1000);
  }


</script>

</head>

<!-- ----------------------------------------------------------------------- -->
<!-- Layout Boxed Yellow -->
<body class="hold-transition fixed <?php echo $pia_skin_selected;?> sidebar-mini" <?php echo $BACKGROUND_IMAGE_PATCH;?> onLoad="show_pia_servertime();" >
<!-- Site wrapper -->
<div class="wrapper">

  <!-- Main Header -->
  <header class="main-header">

<!-- ----------------------------------------------------------------------- -->
    <!-- Logo -->
    <a href="devices.php" class="logo">
      <!-- mini logo for sidebar mini 50x50 pixels -->
      <span class="logo-mini">
        <img src="img/pialertLogoWhite.png" class="pia-top-left-logo" alt="Pi.Alert Logo"/>        
      </span>
      <!-- logo for regular state and mobile devices -->
      <span class="logo-lg">Pi<b>.Alert</b>

      </span>
      
    </a>

<!-- ----------------------------------------------------------------------- -->
    <!-- Header Navbar -->
    <nav class="navbar navbar-static-top" role="navigation">
      <!-- Sidebar toggle button-->
      <a href="#" class="sidebar-toggle" data-toggle="push-menu" role="button">
        <i class="fa-solid fa-bars"></i>
      </a>      
      <!-- Navbar Right Menu -->
      <div class="navbar-custom-menu">
        <ul class="nav navbar-nav">          
	 <!-- Back Button -->		 
	 <li>
	   <a id="back-button" href="javascript:history.go(-1);" role="button" span class='of-bt-icon'><i class='fa fa-arrow-left'></i></a>
	 </li>
	 <!-- Next Button -->		 
	 <li>
	   <a id="next-button" href="javascript:history.go(1);" role="button" span class='of-bt-icon'><i class='fa fa-arrow-right'></i></a>
	 </li>			
	 <!-- Clear cache & Reload -->		 
	 <li>
	   <a id="reload-button" href='#' role="button" span class='of-bt-icon' onclick='clearCache()'><i class='fa fa-repeat'></i></a>
	 </li>	
	 <!-- Full Screen -->		 
	 <li>
	   <a id="fullscreen-button" href='#' role="button" span class='of-bt-icon' onclick='toggleFullscreen()'><i class='fa fa-arrows-alt'></i></a>
	 </li>	                
          <!-- Server Status -->
          <li>
            <a onclick="setCache('activeMaintenanceTab', 'tab_Logging_id')" href="maintenance.php#tab_Logging">
              <div class="header-status">
                <code id="state"></code>
              </div>
            </a>
          </li>
          <!-- Server Name -->
          <li>
            <div class="header-server-time small">
              <div><?php echo gethostname();?></div> <div><span id="PIA_Servertime_place"></span></div>
            </div>
          </li>

          <!-- Header right info -->
          <li class="dropdown user user-menu">
            <!-- Menu Toggle Button -->
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">
              <!-- The user image in the navbar-->
              <img src="img/pialertLogoWhite.png" class="user-image" style="border-radius: initial" alt="Pi.Alert Logo">
              <!-- hidden-xs hides the username on small devices so only the image appears. -->
              <span class="hidden-xs">Pi.Alert</span>
            </a>
            <ul class="dropdown-menu">
              <!-- The user image in the menu -->
              <li class="user-header" style=" height: 100px;">
                <img src="img/pialertLogoWhite.png" class="img-circle" alt="Pi.Alert Logo" style="border-color:transparent;  height: 50px; width: 50px; margin-top:15px;">
                <p style="float: right; width: 200px">
                <?= lang('About_Title');?>
                  <small><?= lang('About_Design');?> Docker</small>
                </p>
              </li>

              <!-- Menu Body -->

              <li class="user-footer">
                <div class="pull-right">
                  <a href="index.php?action=logout" class="btn btn-danger"><?= lang('About_Exit');?></a>
                </div>
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </nav>
  </header>

<!-- ----------------------------------------------------------------------- -->
  <!-- Left side column. contains the logo and sidebar -->
  <aside class="main-sidebar">

    <!-- sidebar: style can be found in sidebar.less -->
    <section class="sidebar">

      <!-- search form (Optional) -->
        <!-- DELETED -->

      <!-- Navigation Mneu -->
      <ul class="sidebar-menu" data-widget="tree">

        <li class=" treeview  <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('devices.php', 'deviceDetails.php') ) ){ echo 'active menu-open'; } ?>">
          <a href="#"  onclick="openUrl(['./devices.php', './deviceDetails.php'])">

          <i class="fa fa-fw fa-laptop"></i> <span><?= lang('Navigation_Devices');?></span>
            <span class="pull-right-container">
              <i class="fa fa-angle-left pull-right"></i>
            </span>
          </a>
          <ul class="treeview-menu" style="display: <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('devices.php', 'deviceDetails.php') ) ){ echo 'block'; } else {echo 'none';} ?>;">
            <li>
              <a href="devices.php#my" onclick="initializeDatatable('my')" >  <?= lang("Device_Shortcut_AllDevices");?> </a>
            </li>
            <li>
              <a href="devices.php#connected" onclick="initializeDatatable('connected')" >  <?= lang("Device_Shortcut_Connected");?> </a>
            </li>
            <li>
              <a href="devices.php#favorites" onclick="initializeDatatable('favorites')" > <?= lang("Device_Shortcut_Favorites");?> </a>
            </li>
            <li>
              <a href="devices.php#new" onclick="initializeDatatable('new')"  >  <?= lang("Device_Shortcut_NewDevices");?> </a>
            </li>
            <li>
              <a href="devices.php#down" onclick="initializeDatatable('down')" >  <?= lang("Device_Shortcut_DownAlerts");?> </a>
            </li>
            <li>
              <a href="devices.php#archived" onclick="initializeDatatable('archived')" >  <?= lang("Device_Shortcut_Archived");?> </a>
            </li>
            
          </ul>
        </li>

        <!-- Monitoring menu item -->

        <li class=" treeview <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('presence.php', 'report.php', 'events.php' ) ) ){ echo 'active menu-open'; } ?>">
          <a href="#">
          <i class="fa fa-fw fa-chart-bar"></i> <span><?= lang('Navigation_Monitoring');?></span>
            <span class="pull-right-container">
              <i class="fa fa-angle-left pull-right"></i>
            </span>
          </a>
          <ul class="treeview-menu " style="display: <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('presence.php', 'report.php', 'events.php' ) ) ){ echo 'block'; } else {echo 'none';} ?>;">
            <li>
              <a href="presence.php">  <?= lang("Navigation_Presence");?> </a>
            </li>
            <li>
              <a href="events.php">  <?= lang("Navigation_Events");?> </a>
            </li>
            <li>
              <a href="report.php"> <?= lang("Navigation_Report");?> </a>
            </li>            
            
          </ul>
        </li>

	      <!-- Network menu item -->
        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('network.php') ) ){ echo 'active'; } ?>">
          <a href="network.php"><i class="fa fa-fw fa-network-wired"></i> <span><?= lang('Navigation_Network');?></span></a>
        </li>

        <!-- Maintenance menu item -->
        <li class=" treeview  <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('maintenance.php') ) ){ echo 'active menu-open'; } ?>">
          <a href="#" onclick="openUrl(['./maintenance.php'])">
          <div class="info-icon-nav myhidden" id="version" data-build-time="<?php echo file_get_contents( "buildtimestamp.txt");?>">🆕</div>
          <i class="fa fa-fw fa-wrench"></i> <span><?= lang('Navigation_Maintenance');?></span>
            <span class="pull-right-container">
              <i class="fa fa-angle-left pull-right"></i>
            </span>
          </a>
          <ul class="treeview-menu" style="display: <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('maintenance.php') ) ){ echo 'block'; } else {echo 'none';} ?>;">
            <li>
              <a href="maintenance.php#tab_Settings" onclick="initializeTabs()">  <?= lang("Maintenance_Tools_Tab_UISettings");?> </a>
            </li>
            <li>
              <a href="maintenance.php#tab_DBTools" onclick="initializeTabs()">  <?= lang("Maintenance_Tools_Tab_Tools");?> </a>
            </li>
            <li>
              <a href="maintenance.php#tab_BackupRestore" onclick="initializeTabs()"> <?= lang("Maintenance_Tools_Tab_BackupRestore");?> </a>
            </li>
            <li>
              <a href="maintenance.php#tab_Logging" onclick="initializeTabs()">  <?= lang("Maintenance_Tools_Tab_Logging");?> </a>
            </li>
            <li>
              <a href="maintenance.php#tab_multiEdit" onclick="initializeTabs()">  <?= lang("Device_MultiEdit");?> </a>
            </li>
            
          </ul>
        </li>

        <!-- Settings menu item -->
        <li class=" treeview  <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('settings.php') ) ){ echo 'active menu-open'; } ?>">
          <a href="#" onclick="openUrl(['./settings.php'])">
          <i class="fa fa-fw fa-cog"></i> <span><?= lang('Navigation_Settings');?></span>
            <span class="pull-right-container">
              <i class="fa fa-angle-left pull-right"></i>
            </span>
          </a>
          <ul class="treeview-menu" style="display: <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('settings.php') ) ){ echo 'block'; } else {echo 'none';} ?>;">
            <li>
              <a href="settings.php#pageTitle">  <?= lang("settings_enabled");?> </a>
            </li>
            <li>
              <a href="settings.php#core_content_header">  <?= lang("settings_core_label");?> </a>
            </li>
            <li>
              <a href="settings.php#system_content_header"> <?= lang("settings_system_label");?> </a>
            </li>
            <li>
              <a href="settings.php#device_scanner_content_header">  <?= lang("settings_device_scanners_label");?> </a>
            </li>
            <li>
              <a href="settings.php#other_content_header">  <?= lang("settings_other_scanners_label");?> </a>
            </li>
            <li>
              <a href="settings.php#publisher_content_header"> <?= lang("settings_publishers_label");?> </a>
            </li>
            
          </ul>
        </li>

        <!-- Integrations menu item -->
        <li class=" treeview <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('plugins.php', 'workflows.php' ) ) ){ echo 'active menu-open'; } ?>">
          <a href="#">
          <i class="fa fa-fw fa-plug"></i> <span><?= lang('Navigation_Integrations');?></span>
            <span class="pull-right-container">
              <i class="fa fa-angle-left pull-right"></i>
            </span>
          </a>
          <ul class="treeview-menu " style="display: <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('plugins.php', 'workflows.php' ) ) ){ echo 'block'; } else {echo 'none';} ?>;">                    
            <li>
              <div class="info-icon-nav work-in-progress">  </div>
              <a href="workflows.php"><?= lang('Navigation_Workflows');?></a>
            </li>
            <li>
              <a href="plugins.php"><?= lang("Navigation_Plugins");?> </a>
            </li>            
          </ul>
        </li>

        <!-- About menu item -->
        <li class=" treeview <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('donations.php', 'help_faq.php', 'systeminfo.php' ) ) ){ echo 'active menu-open'; } ?>">
          <a href="#">
          <i class="fa fa-fw fa-info"></i> <span><?= lang('Navigation_About');?></span>
            <span class="pull-right-container">
              <i class="fa fa-angle-left pull-right"></i>
            </span>
          </a>
          <ul class="treeview-menu " style="display: <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('donations.php', 'help_faq.php', 'systeminfo.php' ) ) ){ echo 'block'; } else {echo 'none';} ?>;">
            <li>
              <a href="donations.php">  <?= lang("Navigation_Donations");?> </a>
            </li>
            <li>
              <a href="help_faq.php">  <?= lang("Navigation_HelpFAQ");?> </a>
            </li>
            <li>
              <a href="systeminfo.php"> <?= lang("Navigation_SystemInfo");?> </a>
            </li>            
            
          </ul>
        </li>

      </ul>

      <!-- /.sidebar-menu -->
    </section>
    <!-- /.sidebar -->
  </aside>


<script defer>

// Generate work-in-progress icons
function workInProgress() {

  if($(".work-in-progress").html().trim() == "")
  {
    $(".work-in-progress").append(`
              <a href="https://github.com/jokob-sk/Pi.Alert/issues" target="_blank">
                <b class="pointer" title="${getString("Gen_Work_In_Progress")}">🦺</b>
              </a>
            `)
  }
}

//--------------------------------------------------------------


  //--------------------------------------------------------------

  function toggleFullscreen() {

   if (document.fullscreenElement) {
     document.exitFullscreen();
    }
   else {
     document.documentElement.requestFullscreen();
	}
   }
  
  //--------------------------------------------------------------

  // Update server time in the header
  show_pia_servertime()

  // Update server state in the header
  updateState()
  workInProgress() 
  
</script>
