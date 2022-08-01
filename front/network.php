<?php
  session_start();
  if ($_SESSION["login"] != 1)
  {
      header('Location: /pialert/index.php');
      exit;
  }

  require 'php/templates/header.php';
  require 'php/server/db.php';
  require 'php/server/util.php';

  global $pia_lang;
  

  $DBFILE = '../db/pialert.db';
  $NETWORKTYPES = getNetworkTypes();
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

      // Create top-level node (network devices) tabs 
      function createDeviceTabs($node_mac, $node_name, $node_type, $node_ports_count, $activetab) {

        // prepare string with port number in brackets if available
        $str_port = "";
        if ($node_ports_count != "") {
          $str_port = ' ('.$node_ports_count.')';
        }

        

        $str_tab_header = '<li class="'.$activetab.'">
                              <a href="#'.str_replace(":", "_", $node_mac).'" data-toggle="tab">'
                                  .$node_name.' / '.$node_type. ' ' .$str_port.
                              '</a>
                          </li>';

        echo $str_tab_header;

      }

      function createPane($node_mac, $node_name, $node_type, $node_ports_count, $activetab){
        $str_tab_pane = '<div class="tab-pane '.$activetab.'" id="'.str_replace(":", "_", $node_mac).'">
                            <h4>'.$node_name.' (ID: '.str_replace(":", "_", $node_mac).')</h4>
                            <br>
                             <div class="box-body no-padding">';




        $str_table =      '
                              <table class="table table-striped">
                                <tbody>
                                <tr>
                                  <th style="width: 40px">Port</th>
                                  <th style="width: 100px">'.$pia_lang['Network_Table_State'].'</th>
                                  <th>'.$pia_lang['Network_Table_Hostname'].'</th>
                                  <th>'.$pia_lang['Network_Table_IP'].'</th>
                                </tr>';
        
        // Prepare Array for Devices with Port value
        // If no Port is set, the Port number is set to 0
        if ($node_ports_count == "") {
          $node_ports_count = 0;
        }

        // Get all leafs connected to a node based on the node_mac        
        $func_sql = 'SELECT dev_Network_Node_port as port,
                            dev_MAC as mac,  
                            dev_PresentLastScan as online, 
                            dev_Name as name,
                            dev_DeviceType as type, 
                            dev_LastIP as last_ip 
        FROM "Devices" WHERE "dev_Network_Node_MAC" = "'.$node_mac.'"';
        
        global $db;
        $func_result = $db->query($func_sql);        
        
        // array 
        $tableData = array();
        while ($row = $func_result -> fetchArray (SQLITE3_ASSOC)) {   
            // Push row data      
            $tableData[] = array( 'port'            => $row['port'], 
                                  'mac'             => $row['mac'],
                                  'online'          => $row['online'],
                                  'name'            => $row['name'],
                                  'type'            => $row['type'],
                                  'last_ip'         => $row['last_ip']); 
        }
    
        // Control no rows
        if (empty($tableData)) {
          $tableData = [];
        }

        $str_table_rows = "";        

        foreach ($tableData as $row) {                            
         
          if ($row['online'] == 1) {
            $port_state = '<div class="badge bg-green text-white" style="width: 60px;">Online</div>';
          } else {
            $port_state = '<div class="badge bg-red text-white" style="width: 60px;">Offline</div>';
          }
          
          // BUG: TODO fix icons - I'll need to fix the SQL query to add the type of the node on line 95
          // prepare HTML for the port table column cell
          $port_content = "N/A";
  
          if ($row['type'] == "WLAN" || $row['type'] == "AP" ) { 
            $port_content = '<i class="fa fa-wifi"></i>';
          } elseif ($row['type'] == "Powerline") 
          {
            $port_content = '<i class="fa fa-flash"></i>';
          } elseif ($row['port'] != NULL && $row['port'] != "") 
          {
            $port_content = $row['port'];
          }
  
          $str_table_rows = $str_table_rows.
                            '<tr>
                              <td style="text-align: center;">
                                '.$port_content.'                  
                              </td>
                              <td>'
                                .$port_state.
                              '</td>
                              <td style="padding-left: 10px;">
                                <a href="./deviceDetails.php?mac='.$row['mac'].'">
                                  <b>'.$row['name'].'</b>
                                </a>
                              </td>
                              <td>'
                                .$row['last_ip'].
                              '</td>
                            </tr>';
          
        }        

        $str_table_close =    '</tbody>
                            </table>';

        // no connected device - don't render table
        if($str_table_rows == "")
        {
          $str_table = "";
          $str_table_close = "";
        }
         
        $str_close_pane = '</div>       
          </div>     
          <div class="aaaaaaa"></div>';  

        // write the HTML
        echo  ''.$str_tab_header.
              $str_tab_pane.
              $str_table.
              $str_table_rows.
              $str_table_close.
              $str_close_pane;
      }     

    
    // Create Top level tabs   (List of network devices), explanation of the terminology below:
    //
    //             Switch 1 (node) 
    //              /(p1)    \ (p2)     <----- port numbers
    //             /          \
    //   Smart TV (leaf)      Switch 2 (node (for the PC) and leaf (for Switch 1))
    //                          \
    //                          PC (leaf)
    
    $sql = "SELECT node_name, node_mac, node_type, node_ports_count
              FROM 
              (
                  SELECT a.dev_Name as  node_name,        
                         a.dev_MAC as node_mac,
                         a.dev_DeviceType as node_type 
                    FROM Devices a 
                    WHERE a.dev_DeviceType in ('AP', 'Gateway', 'Powerline', 'Switch', 'WLAN', 'PLC', 'Router','USB LAN Adapter', 'USB WIFI Adapter', 'Internet')					
              ) t1
              LEFT JOIN
              (
                  SELECT b.dev_Network_Node_MAC as node_mac_2,
                         count() as node_ports_count 
                    FROM Devices b 
                    WHERE b.dev_Network_Node_MAC NOT NULL group by b.dev_Network_Node_MAC
              ) t2
              ON (t1.node_mac = t2.node_mac_2);
          ";

    $result = $db->query($sql);    

    // array 
    $tableData = array();
    while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {   
        // Push row data      
        $tableData[] = array( 'node_mac'                => $row['node_mac'], 
                              'node_name'               => $row['node_name'],
                              'node_type'               => $row['node_type'],
                              'node_ports_count'        => $row['node_ports_count']); 
    }

    // Control no rows
    if (empty($tableData)) {
      $tableData = [];
    }

    echo '<div class="nav-tabs-custom" style="margin-bottom: 0px;">
    <ul class="nav nav-tabs">';

    $activetab='active';                    
    foreach ($tableData as $row) {                            
        createDeviceTabs($row['node_mac'], 
                          $row['node_name'], 
                          $row['node_type'], 
                          $row['node_ports_count'],
                          $activetab);

                          $activetab = ""; // reset active tab indicator, only the first tab is active
      
    }
    echo ' </ul>  <div class="tab-content">';

    $activetab='active';    

    foreach ($tableData as $row) {                            
      createPane($row['node_mac'], 
                  $row['node_name'], 
                  $row['node_type'], 
                  $row['node_ports_count'],
                  $activetab);

                  $activetab = ""; // reset active tab indicator, only the first tab is active
    
  }
                              
    
    ?>
                  <!-- /.tab-pane -->
          </div>
         
  </section>

    <!-- /.content -->
  </div>
  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>
