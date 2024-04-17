<!--
#---------------------------------------------------------------------------------#
#  NetAlertX                                                                       #
#  Open Source Network Guard / WIFI & LAN intrusion detector                      #
#                                                                                 #
# footer.php - Front module. Common footer to all the web pages                   #
#---------------------------------------------------------------------------------#
#    Puche      2021        pi.alert.application@gmail.com   GNU GPLv3            #
#    jokob-sk   2022        jokob.sk@gmail.com               GNU GPLv3            #
#    leiweibau  2022        https://github.com/leiweibau     GNU GPLv3            #
#    cvc90      2023        https://github.com/cvc90         GNU GPLv3            #
#---------------------------------------------------------------------------------#
-->

  <!-- Main Footer -->
  <footer class="main-footer">
    <!-- Default to the left -->

    <!-- NetAlertX footer with url -->
    <a href="https://github.com/jokob-sk/NetAlertX" target="_blank">Net <b>Alert</b><sup>x</sup></a>
     
    
    <!-- To the right -->
    <div class="pull-right no-hidden-xs">
      | <a href="https://github.com/jokob-sk/NetAlertX/tree/main/docs" target="_blank">Docs <i class="fa fa-circle-question"></i></a>
      | <a href="https://github.com/jokob-sk/NetAlertX/issues"><i class="fa-solid fa-bug"></i></a> 
      | <a href="https://github.com/jokob-sk/NetAlertX/"><i class="fa-brands fa-github"></i></a> 
      | <a href="mailto:jokob@duck.com?subject=NetAlertX"><i class="fa-solid fa-envelope"></i></a> 
      | <a href="https://github.com/pucherot/Pi.Alert">&copy;</a> 
      | <?= lang('Maintenance_built_on');?>:  <?php include 'php/templates/build.php'; ?> 
      |  Version:  <?php include 'php/templates/version.php'; ?> 
      |     
    </div>
  </footer>

<!-- ----------------------------------------------------------------------- -->
  <!-- Control Sidebar -->
    <!-- DELETED -->

</div>
<!-- ./wrapper -->
        
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

<!-- NetAlertX -------------------------------------------------------------- -->

  <script src="js/handle_version.js"></script>

  <?php
    require 'migrationCheck.php';
  ?>

</body>
</html>
