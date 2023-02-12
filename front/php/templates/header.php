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
    getParam("state","Back_App_State", true)
    setTimeout("updateState()", 5000);
  }

  function show_pia_servertime() {

    // datetime in timeZone in the "en-UK" locale
    let time = new Date().toLocaleString("en-UK", { timeZone: "<?php echo $timeZone?>" });

    if (document.getElementById) { 
      document.getElementById("PIA_Servertime_place").innerHTML = '('+time+')'; 
    } 
    
    setTimeout("show_pia_servertime()", 1000);
  }

  // refresh page on focus - adds a lot of SQL queries overhead onto the DB - disabling for now
  // document.addEventListener("visibilitychange",()=>{
  //   if(document.visibilityState==="visible"){
  //       window.location.href = window.location.href.split('#')[0];
  //   }
  // })

</script>

</head>

<!-- ----------------------------------------------------------------------- -->
<!-- Layout Boxed Yellow -->
<body class="hold-transition <?php echo $pia_skin_selected;?> layout-boxed sidebar-mini" <?php echo $BACKGROUND_IMAGE_PATCH;?> onLoad="show_pia_servertime();" >
<!-- Site wrapper -->
<div class="wrapper">

  <!-- Main Header -->
  <header class="main-header">

<!-- ----------------------------------------------------------------------- -->
    <!-- Logo -->
    <a href="devices.php" class="logo">
      <!-- mini logo for sidebar mini 50x50 pixels -->
      <span class="logo-mini">P<b>a</b></span>
      <!-- logo for regular state and mobile devices -->
      <span class="logo-lg">Pi<b>.Alert</b></span>
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
          <!-- Server Status -->
          <li>
            <a onclick="setCache('activeMaintenanceTab', 'tab_Logging_id')" href="/maintenance.php#tab_Logging">
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
                  <small><?= lang('About_Design');?> Raspberry Pi</small>
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

      <!-- Sidebar user panel (optional) -->
      <div class="user-panel">
        <a href="." class="logo">
          <img src="img/pialertLogoGray80.png" class="img-responsive" alt="Pi.Alert Logo"/>
        </a>
      </div>

      <!-- search form (Optional) -->
        <!-- DELETED -->

      <!-- Sidebar Menu -->
      <ul class="sidebar-menu" data-widget="tree">

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('devices.php', 'deviceDetails.php') ) ){ echo 'active'; } ?>">
          <a href="devices.php"><span><i class="fa fa-laptop"></i> <?= lang('Navigation_Devices');?></span></a>
        </li>

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('presence.php') ) ){ echo 'active'; } ?>">
          <a href="presence.php"><i class="fa fa-calendar"></i> <?= lang('Navigation_Presence');?></span></a>
        </li>

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('events.php') ) ){ echo 'active'; } ?>">
          <a href="events.php"><i class="fa fa-bolt"></i> <span><?= lang('Navigation_Events');?></span></a>
        </li>

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('network.php') ) ){ echo 'active'; } ?>">
          <a href="network.php"><span><i class="fa fa-fw fa-network-wired"></i>  <?= lang('Navigation_Network');?></span></a>
        </li>

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('plugins.php') ) ){ echo 'active'; } ?>">
          <a href="plugins.php"><span><i class="fa fa-fw fa-plug"></i>  <?= lang('Navigation_Plugins');?></span></a>
        </li>

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('maintenance.php') ) ){ echo 'active'; } ?>">
          <div class="new-version myhidden" id="version" data-build-time="<?php echo file_get_contents( "buildtimestamp.txt");?>">🆕</div>
          <a href="maintenance.php"><i class="fa fa-wrench "></i> <span><?= lang('Navigation_Maintenance');?></span></a>
        </li>
        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('settings.php') ) ){ echo 'active'; } ?>">
          <a href="settings.php"><i class="fa fa-cog"></i> <span><?= lang('Navigation_Settings');?></span></a>
        </li>

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('help_faq.php') ) ){ echo 'active'; } ?>">
          <a href="help_faq.php"><i class="fa fa-question"></i> <span><?= lang('Navigation_HelpFAQ');?></span></a>
        </li>
      </ul>

      <!-- /.sidebar-menu -->
    </section>
    <!-- /.sidebar -->
  </aside>

<script src="js/pialert_common.js"></script>
<script defer>

//--------------------------------------------------------------

  
  //--------------------------------------------------------------
  function getParam(targetId, key, skipCache = false) {  

    skipCacheQuery = "";

    if(skipCache)
    {
      skipCacheQuery = "&skipcache";
    }

    // get parameter value
    $.get('php/server/parameters.php?action=get&defaultValue=NULL&parameter='+ key + skipCacheQuery, function(data) {
      var result = data;

      document.getElementById(targetId).innerHTML = result.replaceAll('"', '');    

    });
  }

  //--------------------------------------------------------------

  // Update server time in the header
  show_pia_servertime()

  // Update server state in the header
  updateState()



</script>
