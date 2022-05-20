<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  header.php - Front module. Common header to all the web pages 
#-------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
#--------------------------------------------------------------------------- -->

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

  <!-- Bootstrap 3.3.7 -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/bootstrap/dist/css/bootstrap.min.css">

  <!-- Font Awesome -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/font-awesome/css/font-awesome.min.css">

  <!-- Ionicons -->
  <link rel="stylesheet" href="lib/AdminLTE/bower_components/Ionicons/css/ionicons.min.css">

  <!-- Theme style -->
  <link rel="stylesheet" href="lib/AdminLTE/dist/css/AdminLTE.min.css">

  <!-- AdminLTE Skins. We have chosen the skin-blue for this starter
        page. However, you can choose any other skin. Make sure you
        apply the skin class to the body tag so the changes take effect. -->
  <link rel="stylesheet" href="lib/AdminLTE/dist/css/skins/skin-blue.min.css">

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

  <!-- Page Icon -->
  <link rel="icon" type="image/png" sizes="160x160" href="img/pialertLogoGray80.png" />

  <!-- For better UX on Mobile Devices using the Shortcut on the Homescreen -->
  <link rel="manifest" href="img/manifest.json">

<!-- In addition to the "dark-patch.css" I recommend the use of the theme "skin-blue", 
    on the basis of which I have created the patch. The "dark-patch.css" is mainly 
    the darkmode of the pi-hole AdminLTE Dashboard witch some fixes -->
  <link rel="stylesheet" href="css/dark-patch.css">

</head>

<!-- ----------------------------------------------------------------------- -->
<!-- Layout Boxed Yellow -->
<body class="hold-transition skin-blue layout-boxed sidebar-mini" style="background-image: url('img/boxed-bg-dark.png');">
<!-- Site wrapper -->
<div class="wrapper">

  <!-- Main Header -->
  <header class="main-header">

<!-- ----------------------------------------------------------------------- -->
    <!-- Logo -->
    <a href="." class="logo">
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
        <span class="sr-only">Toggle navigation</span>
      </a>
      <!-- Navbar Right Menu -->
      <div class="navbar-custom-menu">
        <ul class="nav navbar-nav">

          <!-- Server Name -->
          <li><a style="pointer-events:none;"><?php echo gethostname(); ?></a></li>

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
              <li class="user-header">
                <img src="img/pialertLogoWhite.png" class="img-circle" alt="Pi.Alert Logo" style="border-color:transparent">
                <p>
                  Open Source Network Guard
                  <small>Designed for Raspberry Pi</small>
                </p>
              </li>

              <!-- Menu Body -->
              <li class="user-body">
                <div class="row">
                  <div class="col-xs-4 text-center">
                    <a target="_blank" href="https://github.com/pucherot/Pi.Alert">GitHub Pi.Alert</a>
                  </div>
                  <div class="col-xs-4 text-center">
                    <a href="mailto:pi.alert.application@gmail.com">email Support</a>
                  </div>
                  <div class="col-xs-4 text-center">
                    <a target="_blank" href="https://github.com/pucherot/Pi.Alert/blob/main/LICENSE.txt">GNU GPLv3</a>
                  </div>
                  <!--
                  <div class="col-xs-4 text-center">
                    <a href="#">Updates</a>
                  </div>
                  -->
                </div>
                <!-- /.row -->
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
<!--
        <li class="header">MAIN MENU</li>
-->

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('devices.php', 'deviceDetails.php') ) ){ echo 'active'; } ?>">
          <a href="devices.php"><i class="fa fa-laptop"></i> <span>Devices</span></a>
        </li>
        
<!--
         <li><a href="devices.php?status=favorites"><i class="fa fa-star"></i> <span>Favorites Devices</span></a></li>
-->
        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('presence.php') ) ){ echo 'active'; } ?>">
          <a href="presence.php"><i class="fa fa-calendar"></i> <span>Presence</span></a>
        </li>

        <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('events.php') ) ){ echo 'active'; } ?>">
          <a href="events.php"><i class="fa fa-bolt"></i> <span>Events</span></a>
        </li>

<!--
        <li class="treeview">
          <a href="#"><i class="fa fa-link"></i> <span>Config</span>
            <span class="pull-right-container">
                <i class="fa fa-angle-left pull-right"></i>
              </span>
          </a>

          <ul class="treeview-menu">
            <li class=" <?php if (in_array (basename($_SERVER['SCRIPT_NAME']), array('scancycles.php', 'scancyclesDetails.php') ) ){ echo 'active'; } ?>">
              <a href="scancycles.php"><i class="fa fa-link"></i> <span>Scan Cycles</span></a>
            </li>
            <li><a href="#">Cron Status</a></li>
            <li><a href="#">Current IP</a></li>
          </ul>
        </li>
-->
      </ul>

      <!-- /.sidebar-menu -->
    </section>
    <!-- /.sidebar -->
  </aside>
