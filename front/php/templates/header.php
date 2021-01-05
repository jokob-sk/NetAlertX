<!DOCTYPE html> 
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Pi.alert</title>
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
  <link rel="stylesheet" href="lib/AdminLTE/dist/css/skins/skin-yellow-light.min.css">

  
  <!-- Pi.alert CSS -->
  <link rel="stylesheet" href="css/pialert.css">

  <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
  <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
  <!--[if lt IE 9]>
  <script src="https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"></script>
  <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
  <![endif]-->

  <!-- Google Font -->
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,600,700,300italic,400italic,600italic">

  <!-- Page Icon -->
  <link rel="icon" type="image/png" sizes="160x160" href="img/pialertLogoGray80.png" />
</head>

<!-- Layout Boxed Yellow -->
<body class="hold-transition skin-yellow-light layout-boxed sidebar-mini" style="background-image: url('img/backgroud.png');">
<!-- Site wrapper -->
<div class="wrapper">

  <!-- Main Header -->
  <header class="main-header">

    <!-- Logo -->
    <a href="/" class="logo">
      <!-- mini logo for sidebar mini 50x50 pixels -->
      <span class="logo-mini">P<b>a</b></span>
      <!-- logo for regular state and mobile devices -->
      <span class="logo-lg">Pi<b>.alert</b></span>
    </a>

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
              <img src="img/pialertLogoWhite.png" class="user-image" style="border-radius: initial" alt="Pi.alert Logo">
              <!-- hidden-xs hides the username on small devices so only the image appears. -->
              <span class="hidden-xs">Pi.alert</span>
            </a>
            <ul class="dropdown-menu">
              <!-- The user image in the menu -->
              <li class="user-header">
                <img src="img/pialertLogoWhite.png" class="img-circle" alt="Pi.alert Logo" style="border-color:transparent">

                <p>
                  Open Source Network Guard
                  <small>Designed for Raspberry Pi</small>
                </p>
              </li>
              <!-- Menu Body -->
              <li class="user-body">
                <div class="row">
                  <div class="col-xs-4 text-center">
                    <a href="https://github.com/pucherot/Pi.Alert">GitHub</a>
                  </div>
                  <div class="col-xs-4 text-center">
                    <a href="https://github.com/pucherot/Pi.Alert">Pi.Alert</a>
                    <!-- <a href="#">Website</a> -->
                  </div>
                  <div class="col-xs-4 text-center">
                    <a href="#">Updates</a>
                  </div>
                </div>
                <!-- /.row -->
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </nav>
  </header>
  <!-- Left side column. contains the logo and sidebar -->
  <aside class="main-sidebar">

    <!-- sidebar: style can be found in sidebar.less -->
    <section class="sidebar">

      <!-- Sidebar user panel (optional) -->
      <div class="user-panel">
        <a href="/" class="logo">
          <img src="img/pialertLogoGray80.png" class="img-responsive" alt="Pi.alert Logo"/>
        </a>
        <div class="pull-left image">
<!--
          <br><img src="img/pialertLogoBlack.png" class="img-responsive" alt="Pi.alert Logo" style="display: table; table-layout: fixed;" />
-->
        </div>

        <div class="pull-left info" style="display: none">
                    <p>Status</p>
                        <?php

                        $pistatus = exec('sudo pihole status web');
$pistatus=1;
$FTL=true;
$celsius=56.7;
$temperatureunit='C';
$nproc=2;
$loaddata=array();
$loaddata[]=1.1;
$loaddata[]=1.2;
$loaddata[]=1.3;
$memory_usage=0.452;
                        if ($pistatus == "1") {
                            echo '<a id="status"><i class="fa fa-circle" style="color:#7FFF00"></i> Active</a>';
                        } elseif ($pistatus == "0") {
                            echo '<a id="status"><i class="fa fa-circle" style="color:#FF0000"></i> Offline</a>';
                        } elseif ($pistatus == "-1") {
                            echo '<a id="status"><i class="fa fa-circle" style="color:#FF0000"></i> DNS service not running</a>';
                        } else {
                            echo '<a id="status"><i class="fa fa-circle" style="color:#ff9900"></i> Unknown</a>';
                        }

                        // CPU Temp
                        if($FTL)
                        {
                            if ($celsius >= -273.15) {
                                echo "<a id=\"temperature\"><i class=\"fa fa-fire\" style=\"color:";
                                if ($celsius > 60) {
                                    echo "#FF0000";
                                }
                                else
                                {
                                    echo "#3366FF";
                                }
                                echo "\"></i> Temp:&nbsp;";
                                if($temperatureunit === "F")
                                {
                                    echo round($fahrenheit,1) . "&nbsp;&deg;F";
                                }
                                elseif($temperatureunit === "K")
                                {
                                    echo round($kelvin,1) . "&nbsp;K";
                                }
                                else
                                {
                                    echo round($celsius,1) . "&nbsp;&deg;C";
                                }
                                echo "</a>";
                            }
                        }
                        else
                        {
                            echo '<a id=\"temperature\"><i class="fa fa-circle" style="color:#FF0000"></i> FTL offline</a>';
                        }
                    ?>
                    <br/>
                    <?php
                    echo "<a title=\"Detected $nproc cores\"><i class=\"fa fa-circle\" style=\"color:";
                        if ($loaddata[0] > $nproc) {
                            echo "#FF0000";
                        }
                        else
                        {
                            echo "#7FFF00";
                        }
                        echo "\"></i> Load:&nbsp;&nbsp;" . $loaddata[0] . "&nbsp;&nbsp;" . $loaddata[1] . "&nbsp;&nbsp;". $loaddata[2] . "</a>";
                    ?>
                    <br/>
                    <?php
                    echo "<a><i class=\"fa fa-circle\" style=\"color:";
                        if ($memory_usage > 0.75 || $memory_usage < 0.0) {
                            echo "#FF0000";
                        }
                        else
                        {
                            echo "#7FFF00";
                        }
                        if($memory_usage > 0.0)
                        {
                            echo "\"></i> Memory usage:&nbsp;&nbsp;" . sprintf("%.1f",100.0*$memory_usage) . "&thinsp;%</a>";
                        }
                        else
                        {
                            echo "\"></i> Memory usage:&nbsp;&nbsp; N/A</a>";
                        }
                    ?>
        </div>
      </div>

      <!-- search form (Optional) -->
<!--
      <form action="#" method="get" class="sidebar-form">
        <div class="input-group">
          <input type="text" name="q" class="form-control" placeholder="Search...">
          <span class="input-group-btn">
              <button type="submit" name="search" id="search-btn" class="btn btn-flat"><i class="fa fa-search"></i>
              </button>
            </span>
        </div>
      </form>
-->
      <!-- /.search form -->

      <!-- Sidebar Menu -->
      <ul class="sidebar-menu" data-widget="tree">
<!--
        <li class="header">MAIN MENU</li>
-->

        <!-- Optionally, you can add icons to the links -->
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
            <li><a href="#">Scan Cycles</a></li>
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
