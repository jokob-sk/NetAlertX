<?php
require dirname(__FILE__).'/php/server/init.php';
require 'php/templates/security.php';



if ($Pia_WebProtection != 'true')
{
    header('Location: devices.php');
    $_SESSION["login"] = 1;
    exit;
}

// Logout
if (isset ($_GET["action"]) && $_GET["action"] == 'logout')
{
  setcookie("PiAlert_SaveLogin", '', time()+1); // reset cookie
  $_SESSION["login"] = 0;
  header('Location: index.php');
  exit;
}

// Password without Cookie check -> pass and set initial cookie
if (isset ($_POST["loginpassword"]) && $Pia_Password == hash('sha256',$_POST["loginpassword"]))
{
    header('Location: devices.php');
    $_SESSION["login"] = 1;
    if (isset($_POST['PWRemember'])) {setcookie("PiAlert_SaveLogin", hash('sha256',$_POST["loginpassword"]), time()+604800);}
}

// active Session or valid cookie (cookie not extends)
if (( isset ($_SESSION["login"]) && ($_SESSION["login"] == 1)) || (isset ($_COOKIE["PiAlert_SaveLogin"]) && $Pia_Password == $_COOKIE["PiAlert_SaveLogin"]))
{
    header('Location: devices.php');
    $_SESSION["login"] = 1;
    if (isset($_POST['PWRemember'])) {setcookie("PiAlert_SaveLogin", hash('sha256',$_POST["loginpassword"]), time()+604800);}
}

$login_headline = lang('Login_Toggle_Info_headline');
$login_info = "";
$login_mode = 'danger';
$login_display_mode = 'display: block;';
$login_icon = 'fa-info';

// no active session, cookie not checked
if (isset ($_SESSION["login"]) == FALSE || $_SESSION["login"] != 1)
{
  if ($Pia_Password == '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92') 
  {
    $login_info = lang('Login_Default_PWD');
    $login_mode = 'danger';
    $login_display_mode = 'display: block;';
    $login_headline = lang('Login_Toggle_Alert_headline');
    $login_icon = 'fa-ban';
  } 
  else 
  {
    $login_mode = 'info';
    $login_display_mode = 'display: none;';
    $login_headline = lang('Login_Toggle_Info_headline');
    $login_icon = 'fa-info';
  }
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
    <a href="/index2.php">Pi.<b>Alert</b></a>
  </div>
  <!-- /.login-logo -->
  <div class="login-box-body">
    <p class="login-box-msg"><?= lang('Login_Box');?></p>
      <form action="index.php" method="post">
      <div class="form-group has-feedback">
        <input type="password" class="form-control" placeholder="<?= lang('Login_Psw-box');?>" name="loginpassword">
        <span class="glyphicon glyphicon-lock form-control-feedback"></span>
      </div>
      <div class="row">
        <div class="col-xs-8">
          <div class="checkbox icheck">
            <label>
              <input type="checkbox" name="PWRemember">
                <div style="margin-left: 10px; display: inline-block; vertical-align: top;"> 
                  <?= lang('Login_Remember');?><br><span style="font-size: smaller"><?= lang('Login_Remember_small');?></span>
                </div>
            </label>
          </div>
        </div>
        <!-- /.col -->
        <div class="col-xs-4" style="padding-top: 10px;">
          <button type="submit" class="btn btn-primary btn-block btn-flat"><?= lang('Login_Submit');?></button>
        </div>
        <!-- /.col --> 
      </div>
    </form>

    <div style="padding-top: 10px;">
      <button class="btn btn-xs btn-primary btn-block btn-flat" onclick="Passwordhinfo()"><?= lang('Login_Toggle_Info');?></button>
    </div>

  </div>
  <!-- /.login-box-body -->



  <div id="myDIV" class="box-body" style="margin-top: 50px; <?php echo $login_display_mode;?>">
      <div class="alert alert-<?php echo $login_mode;?> alert-dismissible">
          <button type="button" class="close" data-dismiss="alert" aria-hidden="true">�</button>
          <h4><i class="icon fa <?php echo $login_icon;?>"></i><?php echo $login_headline;?></h4>
          <p><?php echo $login_info;?></p>
          <p><?= lang('Login_Psw_run');?><br><span style="border: solid 1px yellow; padding: 2px;">./reset_password.sh <?= lang('Login_Psw_new');?></span><br><?= lang('Login_Psw_folder');?></p>
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

function Passwordhinfo() {
  var x = document.getElementById("myDIV");
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
} 

</script>
</body>
</html>
