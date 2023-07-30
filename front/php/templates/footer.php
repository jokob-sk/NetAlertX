<!-- ---------------------------------------------------------------------------
#  Pi.Alert
#  Open Source Network Guard / WIFI & LAN intrusion detector 
#
#  footer.php - Front module. Common footer to all the web pages 
#-------------------------------------------------------------------------------
#  Puche 2021 / 2022+ jokob             jokob@duck.com                GNU GPLv3
#--------------------------------------------------------------------------- -->

  <!-- Main Footer -->
  <footer class="main-footer">
    <!-- Default to the left -->

    <!-- &copy; 2020 Puche -->
    <span style="display:inline-block; transform: rotate(180deg)">&copy;</span>
    
       2020 Puche (2022+ <a href="mailto:jokob@duck.com?subject=PiAlert">jokob-sk</a>) | <b><?= lang('Maintenance_built_on');?>: </b> 
       
       <?php echo date("Y-m-d", ((int)file_get_contents( "buildtimestamp.txt")));?> 
       
       | <b> Version: </b>
       
       <?php $filename = "/.VERSION";
       
        if(file_exists($filename))
        {
          echo file_get_contents($filename);
        }
        else{
          echo "File not found";
        }               
       
       ?>
        |
      <a href="https://github.com/jokob-sk/Pi.Alert/tree/main/docs" target="_blank"> 
        <span>Docs <i class="fa fa-circle-question"></i>
      </a><span>
    
    <!-- To the right -->
    <div class="pull-right no-hidden-xs">

    <!-- Pi.Alert  2.50  <small>(2019-12-30)</small> -->
    <?php
      echo 'Pi.Alert';
    ?>
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
