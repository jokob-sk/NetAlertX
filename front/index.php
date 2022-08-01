<?php 
session_start();

if ($_REQUEST['action'] == 'logout') {
  session_destroy();
  header('Location: /pialert/index.php');
}
// ##################################################
// ## Login Processing start
// ##################################################
$config_file = "../config/pialert.conf";
$config_file_lines = file($config_file);

// ###################################
// ## PIALERT_WEB_PROTECTION FALSE
// ###################################

$config_file_lines_bypass = array_values(preg_grep('/^PIALERT_WEB_PROTECTION\s.*/', $config_file_lines));
$protection_line = explode("=", $config_file_lines_bypass[0]);
$Pia_WebProtection = strtolower(trim($protection_line[1]));

if ($Pia_WebProtection != 'true')
  {
      header('Location: /pialert/devices.php');
      $_SESSION["login"] = 1;
      exit;
  }

// ###################################
// ## PIALERT_WEB_PROTECTION TRUE
// ###################################

$config_file_lines = array_values(preg_grep('/^PIALERT_WEB_PASSWORD\s.*/', $config_file_lines));
$password_line = explode("'", $config_file_lines[0]);
$Pia_Password = $password_line[1];

if ($Pia_Password == hash('sha256',$_POST["loginpassword"]))
  {
      header('Location: /pialert/devices.php');
      $_SESSION["login"] = 1;
  }

if ($_SESSION["login"] == 1)
  {
      header('Location: /pialert/devices.php');
  }

if ($_SESSION["login"] != 1)
  {
      if (file_exists('../db/setting_darkmode')) {$ENABLED_DARKMODE = True;}
      if ($Pia_Password == '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92') {$login_info = 'Defaultpassword "123456" is still active';
  }

// ##################################################
// ## Login Processing end
// ##################################################
?>

<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Pi-Alert | Log in</title>
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
  <!-- iCheck -->
  <link rel="stylesheet" href="lib/AdminLTE/plugins/iCheck/square/blue.css">

  <!-- Dark-Mode Patch -->
<?php
if ($ENABLED_DARKMODE === True) {
   echo '<link rel="stylesheet" href="css/dark-patch.css">';
   $BACKGROUND_IMAGE_PATCH='style="background-image: url(\'img/boxed-bg-dark.png\');"';
} else { $BACKGROUND_IMAGE_PATCH='style="background-image: url(\'img/background.png\');"';}
?>

  <link rel="stylesheet" href="/front/css/offline-font.css">
</head>
<body class="hold-transition login-page">
<div class="login-box">
  <div class="login-logo">
    <a href="/pialert/index2.php">Pi.<b>Alert</b></a>
  </div>
  <!-- /.login-logo -->
  <div class="login-box-body">
    <p class="login-box-msg">Sign in to start your session</p>

    <form action="/pialert/index.php" method="post">
      <div class="form-group has-feedback">
        <input type="password" class="form-control" placeholder="Password" name="loginpassword">
        <span class="glyphicon glyphicon-lock form-control-feedback"></span>
      </div>
      <div class="row">
        <div class="col-xs-8">
          <div class="checkbox icheck">
            <label>
              <input type="checkbox" disabled> Remember Me
            </label>
          </div>
        </div>
        <!-- /.col -->
        <div class="col-xs-4">
          <button type="submit" class="btn btn-primary btn-block btn-flat">Sign In</button>
        </div>
        <!-- /.col -->
      </div>
    </form>

  </div>
  <!-- /.login-box-body -->

  <div class="box-body" style="margin-top: 50px;">
      <div class="alert alert-danger alert-dismissible">
          <button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>
          <h4><i class="icon fa fa-ban"></i>Password Alert!</h4>
          <p><?php echo $login_info;?></p>
          <p>To set a new password run:<br><span style="border: solid 1px yellow; padding: 2px;">./reset_password.sh yournewpassword</span><br>in the config folder.</p>
      </div>
  </div>


</div>
<!-- /.login-box -->


<!-- jQuery 3 -->
<script src="lib/AdminLTE/bower_components/jquery/dist/jquery.min.js"></script>
<!-- Bootstrap 3.3.7 -->
<script src="lib/AdminLTE/bower_components/bootstrap/dist/js/bootstrap.min.js"></script>
<!-- iCheck -->
<script src="lib/AdminLTE/plugins/iCheck/icheck.min.js"></script>
<script>
  $(function () {
    $('input').iCheck({
      checkboxClass: 'icheckbox_square-blue',
      radioClass: 'iradio_square-blue',
      increaseArea: '20%' /* optional */
    });
  });
</script>
</body>
</html>

<?php

  }
?>
