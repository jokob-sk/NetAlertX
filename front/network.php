<?php
  session_start();
  if ($_SESSION["login"] != 1)
  {
      header('Location: /pialert/index.php');
      exit;
  }

  require 'php/templates/header.php';
  require 'php/server/db.php';

  $DBFILE = '../db/pialert.db';
  OpenDB();

  // #####################################
  // ## Expand Devices Table
  // #####################################
  $sql = 'ALTER TABLE "Devices" ADD "dev_Network_Node_MAC" INTEGER';
  $result = $db->query($sql);
  $sql = 'ALTER TABLE "Devices" ADD "dev_Network_Node_port" INTEGER';
  $result = $db->query($sql);
?>

<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

  <!-- Content header--------------------------------------------------------- -->
  <section class="content-header">
  <?php require 'php/templates/notification.php'; ?>
    <h1 id="pageTitle">
        <?php echo $pia_lang['Network_Title'];?>
    </h1>
  </section>

<?php
  echo $_REQUEST['net_MAC'];
?>

  <!-- Main content ---------------------------------------------------------- -->
  <section class="content">
    <?php

      function createDeviceTabs($mac, $name, $type, $port, $activetab) {

        echo '<li class="'.$activetab.'"><a href="#'.str_replace(":", "_", $mac).'" data-toggle="tab">'.$name.' / '.$type;
        if ($port != "") {
          echo ' ('.$port.')';
        }
        echo '</a></li>';
      }

     function createTabContent($mac, $name, $type, $port, $activetab) {
        global $pia_lang;
        echo '<div class="tab-pane '.$activetab.'" id="'.str_replace(":", "_", $mac).'">
              <h4>'.$name.' (ID: '.str_replace(":", "_", $mac).')</h4><br>';
        echo '<div class="box-body no-padding">
          <table class="table table-striped">
            <tbody><tr>
              <th style="width: 40px">Port</th>
              <th style="width: 100px">'.$pia_lang['Network_Table_State'].'</th>
              <th>'.$pia_lang['Network_Table_Hostname'].'</th>
              <th>'.$pia_lang['Network_Table_IP'].'</th>
            </tr>';
        // Prepare Array for Devices with Port value
        // If no Port is set, the Port number is set to 1
        if ($port == "") {$port = 1;}
        // Create Array with specific length
        $network_device_portname = array();
        $network_device_portmac = array();
        $network_device_portip = array();
        $network_device_portstate = array();
        // make sql query for Network Hardware ID
        global $db;
        $func_sql = 'SELECT * FROM "Devices" WHERE "dev_Network_Node_MAC" = "'.$mac.'"';
        $func_result = $db->query($func_sql);
        while($func_res = $func_result->fetchArray(SQLITE3_ASSOC)) { 
          // Online / Offline state of port     
          if ($func_res['dev_PresentLastScan'] == 1) {
            $port_state = '<div class="badge bg-green text-white" style="width: 60px;">Online</div>';
          } else {
            $port_state = '<div class="badge bg-red text-white" style="width: 60px;">Offline</div>';
          }
          // Prepare Table with Port > push values in array
          if ($port > 1)
            {
              if (stristr($func_res['dev_Network_Node_port'], ',') == '') {
                if ($network_device_portname[$func_res['dev_Network_Node_port']] != '') {
                  $network_device_portname[$func_res['dev_Network_Node_port']] = $network_device_portname[$func_res['dev_Network_Node_port']].','.$func_res['dev_Name'];
                } else {
                  $network_device_portname[$func_res['dev_Network_Node_port']] = $func_res['dev_Name'];
                }
              if ($network_device_portmac[$func_res['dev_Network_Node_port']] != '') {
                  $network_device_portmac[$func_res['dev_Network_Node_port']] = $network_device_portmac[$func_res['dev_Network_Node_port']].','.$func_res['dev_MAC'];
                  } else {
                    $network_device_portmac[$func_res['dev_Network_Node_port']] = $func_res['dev_MAC'];
                }
              if ($network_device_portip[$func_res['dev_Network_Node_port']] != '') {
                  $network_device_portip[$func_res['dev_Network_Node_port']] = $network_device_portip[$func_res['dev_Network_Node_port']].','.$func_res['dev_LastIP'];
                } else {
                  $network_device_portip[$func_res['dev_Network_Node_port']] = $func_res['dev_LastIP'];
                }
              if (isset($network_device_portstate[$func_res['dev_Network_Node_port']])) {
                  $network_device_portstate[$func_res['dev_Network_Node_port']] = $network_device_portstate[$func_res['dev_Network_Node_port']].','.$func_res['dev_PresentLastScan'];
                } else {
                  $network_device_portstate[$func_res['dev_Network_Node_port']] = $func_res['dev_PresentLastScan'];
                }
              } else {
                $multiport = array();
                $multiport = explode(',',$func_res['dev_Network_Node_port']);
                foreach($multiport as $row) {
                    $network_device_portname[trim($row)] = $func_res['dev_Name'];
                    $network_device_portmac[trim($row)] = $func_res['dev_MAC'];
                    $network_device_portip[trim($row)] = $func_res['dev_LastIP'];
                    $network_device_portstate[trim($row)] = $func_res['dev_PresentLastScan'];
                }
                unset($multiport);
              }
            } else {
              // Table without Port > echo values
              // Specific icon for devicetype
              if ($type == "WLAN") {$dev_port_icon = 'fa-wifi';}
              if ($type == "Powerline") {$dev_port_icon = 'fa-flash';}
              echo '<tr><td style="text-align: center;"><i class="fa '.$dev_port_icon.'"></i></td><td>'.$port_state.'</td><td style="padding-left: 10px;"><a href="./deviceDetails.php?mac='.$func_res['dev_MAC'].'"><b>'.$func_res['dev_Name'].'</b></a></td><td>'.$func_res['dev_LastIP'].'</td></tr>';
            }
        }
        // Create table with Port
        if ($port > 1)
          {
            for ($x=1; $x<=$port; $x++) 
              {
                // Prepare online/offline badge for later functions
                $online_badge = '<div class="badge bg-green text-white" style="width: 60px;">Online</div>';
                $offline_badge = '<div class="badge bg-red text-white" style="width: 60px;">Offline</div>';
                // Set online/offline badge
                echo '<tr>';
                echo '<td style="text-align: right; padding-right:16px;">'.$x.'</td>';
                // Set online/offline badge
                // Check if multiple badges necessary
                if (stristr($network_device_portstate[$x],',') == '') {
                  // Set single online/offline badge
                  if ($network_device_portstate[$x] == 1) {$port_state = $online_badge;} else {$port_state = $offline_badge;}
                  echo '<td>'.$port_state.'</td>';
                } else {
                  // Set multiple online/offline badges
                  $multistate = array();
                  $multistate = explode(',',$network_device_portstate[$x]);
                  echo '<td>';
                  foreach($multistate as $key => $value) {
                      if ($value == 1) {$port_state = $online_badge;} else {$port_state = $offline_badge;}
                      echo $port_state.'<br>';
                  }
                  echo '</td>';
                  unset($multistate);
                }  
                // Check if multiple Hostnames are set
                // print single hostname         
                if (stristr($network_device_portmac[$x],',') == '') {
                  echo '<td style="padding-left: 10px;"><a href="./deviceDetails.php?mac='.$network_device_portmac[$x].'"><b>'.$network_device_portname[$x].'</b></a></td>';
                } else {
                  // print multiple hostnames with separate links  
                  $multimac = array();
                  $multimac = explode(',',$network_device_portmac[$x]);
                  $multiname = array();
                  $multiname = explode(',',$network_device_portname[$x]);
                  echo '<td style="padding-left: 10px;">';
                  foreach($multiname as $key => $value) {
                      echo '<a href="./deviceDetails.php?mac='.$multimac[$key].'"><b>'.$value.'</b></a><br>';
                  }
                  echo '</td>';
                  unset($multiname, $multimac);
                }
                // Check if multiple IP are set
                // print single IP  
                if (stristr($network_device_portip[$x],',') == '') {
                  echo '<td style="padding-left: 10px;">'.$network_device_portip[$x].'</td>';
                } else {
                  // print multiple IPs
                  $multiip = array();
                  $multiip = explode(',',$network_device_portip[$x]);
                  echo '<td style="padding-left: 10px;">';
                  foreach($multiip as $key => $value) {
                      echo $value.'<br>';
                  }
                  echo '</td>';
                  unset($multiip);
                }
                echo '</tr>';
              }
        }
      echo '        </tbody>
                  </table>
                </div>';
      echo '</div> ';
    }

    
    // Create Tabs   

      $sql = 'select dev_MAC, dev_Name, dev_DeviceType, dev_Network_Node_port from Devices where dev_DeviceType in ("AP", "Gateway", "Powerline", "Switch", "WLAN", "PLC", "Router","USB LAN Adapter", "USB WIFI Adapter")'; 
      $result = $db->query($sql);

      // array
      $tableData = array();
      while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {   
        // Push row data
        $tableData[] = array('dev_MAC'                => $row['dev_MAC'], 
                             'dev_Name'               => $row['dev_Name'],
                             'dev_DeviceType'         => $row['dev_DeviceType'],
                             'dev_Network_Node_port'  => $row['dev_Network_Node_port'] ); 
      }

      // Control no rows
      if (empty($tableData)) {
        $tableData = [];
      }

    ?>
          <div class="nav-tabs-custom" style="margin-bottom: 0px;">
                <ul class="nav nav-tabs">
                    <?php 
                          $activetab='active';                    
                          foreach ($tableData as $row) {
                              createDeviceTabs($row['dev_MAC'], 
                                               $row['dev_Name'], 
                                               $row['dev_DeviceType'], 
                                               $row['dev_Network_Node_port'],
                                               $activetab);

                                               $activetab = "";
                          }                    
                    ?>                                  
                </ul>
          <div class="tab-content">
              <?php              
                // Ctreate Tab Content
                $activetab='active';
                while($res = $result->fetchArray(SQLITE3_ASSOC)){                                  
                  createTabContent(
                    $res['dev_MAC'], 
                    $res['dev_Name'], 
                    $res['dev_DeviceType'], 
                    $res['dev_Network_Node_port'],
                    $activetab); 
                    
                    $activetab = "";
                }              
              ?>
                  <!-- /.tab-pane -->
          </div>
          <!-- /.tab-content -->
      </div>
      <div style="width: 100%; height: 20px;"></div>
  </section>

    <!-- /.content -->
  </div>
  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>
