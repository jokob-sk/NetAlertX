<!--
#---------------------------------------------------------------------------------#
#  Pi.Alert                                                                       #
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

    <!-- &copy; 2022 jokob-sk -->
    <span style="display:inline-block; transform: rotate(180deg)">&copy;</span>    
       2020 Puche (2022+ <a href="mailto:jokob@duck.com?subject=PiAlert">jokob-sk</a>) | <b><?= lang('Maintenance_built_on');?>: </b> 
       <?php include 'php/templates/build.php'; ?> | <b> Version: </b> <?php include 'php/templates/version.php'; ?> | 
       <a href="https://github.com/jokob-sk/Pi.Alert/tree/main/docs" target="_blank"><span>Docs <i class="fa fa-circle-question"></i></a>
     <span>
    
    <!-- To the right -->
    <div class="pull-right no-hidden-xs">

    <!-- Pi.Alert footer with url -->
    <a href="https://github.com/jokob-sk/Pi.Alert" target="_blank">Pi.Alert</a>
    
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

<!-- Pi.Alert -------------------------------------------------------------- -->
  <script src="js/pialert_common.js"></script>
  <script src="js/handle_version.js"></script>

</body>
</html>
