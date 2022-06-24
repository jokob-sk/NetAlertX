<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  footer.php - Front module. Common footer to all the web pages 
#-------------------------------------------------------------------------------
#  Puche 2021        pi.alert.application@gmail.com        GNU GPLv3
#--------------------------------------------------------------------------- -->

  <!-- Main Footer -->
  <footer class="main-footer">
    <!-- Default to the left -->

    <!-- &copy; 2020 Puche -->
    <?php
      $conf_file = '../config/version.conf';
      $conf_data = parse_ini_file($conf_file);
      echo '<span style="display:inline-block; transform: rotate(180deg)">&copy;</span> '. $conf_data['VERSION_YEAR'] .' Puche';
    ?>
    <!-- To the right -->
    <div class="pull-right no-hidden-xs">

    <!-- Pi.Alert  2.50  <small>(2019-12-30)</small> -->
    <?php
      $conf_file = '../config/version.conf';
      $conf_data = parse_ini_file($conf_file);
      echo 'Pi.Alert&nbsp&nbsp'. $conf_data['VERSION'] .'&nbsp&nbsp<small>('. $conf_data['VERSION_DATE'] .')</small>';
    ?>
    </div>
  </footer>

<!-- ----------------------------------------------------------------------- -->
  <!-- Control Sidebar -->
    <!-- DELETED -->

</div>
<!-- ./wrapper -->

<!-- ----------------------------------------------------------------------- -->
<!-- REQUIRED JS SCRIPTS -->

<!-- jQuery 3 -->
  <script src="lib/AdminLTE/bower_components/jquery/dist/jquery.min.js"></script>

<!-- Bootstrap 3.3.7 -->
  <script src="lib/AdminLTE/bower_components/bootstrap/dist/js/bootstrap.min.js"></script>

<!-- AdminLTE App -->
  <script src="lib/AdminLTE/dist/js/adminlte.min.js"></script>

<!-- Optionally, you can add Slimscroll and FastClick plugins.
     Both of these plugins are recommended to enhance the
     user experience. -->

<!-- SlimScroll -->
  <!-- <script src="lib/AdminLTE/bower_components/jquery-slimscroll/jquery.slimscroll.min.js"></script> -->
<!-- FastClick -->
  <!-- <script src="lib/AdminLTE/bower_components/fastclick/lib/fastclick.js"></script>  -->

<!-- Pi.Alert -------------------------------------------------------------- -->
  <script src="js/pialert_common.js"></script>

</body>
</html>
