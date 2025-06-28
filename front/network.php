<?php

  require 'php/templates/header.php';
  require 'php/templates/notification.php';

  // online / offline badges HTML snippets 
  define('badge_online', '<div class="badge bg-green text-white" style="width: 60px;">Online</div>');
  define('badge_offline', '<div class="badge bg-red text-white" style="width: 60px;">Offline</div>');
  define('sortable_column', ' <span class="sort-btn" onclick="sortColumn(this)"><i class="fa-solid fa-arrow-up-short-wide"></i></span>'); 
  
?>

<script>
  // show spinning icon
  showSpinner()
</script> 
 

<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">


  <span class="helpIcon"> <a target="_blank" href="https://github.com/jokob-sk/NetAlertX/blob/main/docs/NETWORK_TREE.md"><i class="fa fa-circle-question"></i></a></span>

  <div id="networkTree" class="drag"></div>

  <!-- Main content ---------------------------------------------------------- -->
  <section class="content networkTable">
    <?php
      // Create top-level node (network devices) tabs 
      function createDeviceTabs($node_mac, $node_name, $node_status, $node_type, $node_ports_count, $icon, $activetab) {        

        // prepare string with port number in brackets if available
        $str_port = "";
        if ($node_ports_count != "") {
          $str_port = ' ('.$node_ports_count.')';
        }

        // online/offline status circle (red/green)
        $icon_style = "";
        if($node_status == 0) // 1 means online, 0 offline
        {
          $icon_style = "style=\"color:var(--color-red);\""; 
        } 

        $decoded_icon = base64_decode($icon);
        $idFromMac = str_replace(":", "_", $node_mac);
        $str_tab_header = '<li class="networkNodeTabHeaders '.$activetab.' " >
                              
                              <a href="#'.$idFromMac.'" data-mytabmac="'.$node_mac.'" id="'.$idFromMac.'_id" data-toggle="tab" title="'.$node_name.' ">' // _id is added so it doesn't conflict with AdminLTE tab behavior
                                .'<div class="icon" '.$icon_style.'>'.$decoded_icon.' </div> <span class="node-name">'.$node_name.'</span>' .$str_port.
                              '</a>
                          </li>';

        echo $str_tab_header;

      }

      // Create pane content (displayed inside of the tabs)      
      function createPane($node_mac, $node_name, $node_status, $node_type, $node_ports_count, $node_parent_mac, $activetab){        

        // online/offline status circle (red/green)
        $node_badge = "";
        if($node_status == 1) // 1 means online, 0 offline
        {
          $node_badge = badge_online; 
        } else
        {
          $node_badge = badge_offline;
        }

        $idFromMac = str_replace(":", "_", $node_mac);
        $idParentMac = str_replace(":", "_", $node_parent_mac);
        $str_tab_pane = '<div class="tab-pane '.$activetab.'" id="'.$idFromMac.'">
                            <div>
                              <h2 class="page-header"><i class="fa fa-server"></i> '.lang('Network_Node'). '</h2>
                            </div>
                            <table class="table table-striped" > 
                              <tbody>
                                <tr> 
                                  <td class="col-sm-3">
                                    <b>'.lang('Network_Node').'</b>
                                  </td>
                                  <td  class="anonymize">
                                    <a href="./deviceDetails.php?mac='.$node_mac.'">
                                    '.$node_name.'
                                    </a>
                                  </td>
                                </tr>
                                <tr> 
                                  <td >
                                    <b>MAC</b>
                                  </td>
                                  <td data-mynodemac="'.$node_mac.'" class="anonymize">'
                                    .$node_mac.
                                  '</td>
                                </tr>
                                <tr>
                                  <td>
                                    <b>'.lang('Device_TableHead_Type').'</b>
                                  </td>
                                  <td>
                                  ' .$node_type. '
                                  </td>
                                </tr>
                                <tr> 
                                  <td>
                                    <b>'.lang('Network_Table_State').'</b> 
                                  </td>
                                  <td>  '
                                    .$node_badge.
                                  '</td>
                                </tr>
                                <tr> 
                                  <td>
                                    <b>'.lang('Network_Parent').'</b> 
                                  </td>
                                  <td>  
                                    <a href="./network.php?mac='.$idParentMac.'">
                                      <b class="anonymize">
                                        <span class="mac-to-name" my-data-mac="'.$node_parent_mac.'">'.$node_parent_mac.' </span>
                                        <i class="fa fa-square-up-right"></i>
                                      </b>
                                    </a>                                 
                                  </td>
                              </tr>
                              </tbody>
                            </table>                            
                             <div id="assignedDevices"  class="box-body no-padding">
                              <div class="page-header">
                                <h3>
                                  <i class="fa fa-sitemap"></i> '.lang('Network_Connected').'
                                </h3>
                              </div>
                             ';

        $str_table =      '   <table class="table table-striped">
                                <thead>
                                  <tr>
                                    <th  class="col-sm-1" >Port</th>
                                    <th  class="col-sm-1" >'.lang('Network_Table_State').'</th>
                                    <th  class="col-sm-2" >'.lang('Network_Table_Hostname').sortable_column.'</th>
                                    <th  class="col-sm-1" >'.lang('Network_Table_IP').sortable_column.'</th>
                                    <th  class="col-sm-3" >'.lang('Network_ManageLeaf').'</th>
                                  </tr>
                                </thead>
                                <tbody>
                                <tr>

                                </tr>';
        
        // Prepare Array for Devices with Port value
        // If no Port is set, the Port number is set to 0
        if ($node_ports_count == "") {
          $node_ports_count = 0;
        }

        // Get all leafs connected to a node based on the node_mac        
        $func_sql = 'SELECT devParentPort as port,
                            devMac as mac,  
                            devPresentLastScan as online, 
                            devName as name,
                            devType as type, 
                            devLastIP as last_ip,
                            (select devType from Devices a where devMac = "'.$node_mac.'") as node_type
                        FROM Devices WHERE devParentMAC = "'.$node_mac.'" and devIsArchived = 0	order by port, name asc';
        
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
                                  'last_ip'         => $row['last_ip'],
                                  'node_type'       => $row['node_type']); 
        }
    
        // Control no rows
        if (empty($tableData)) {
          $tableData = [];
        }

        $str_table_rows = "";        

        foreach ($tableData as $row) {                            
         
          if ($row['online'] == 1) {
            $port_state = badge_online;
          } else {
            $port_state = badge_offline;
          }
                    
          // prepare HTML for the port table column cell
          $port_content = "N/A";
  
          if (($row['node_type'] == "WLAN" || $row['node_type'] == "AP" ) && ($row['port'] == NULL || $row['port'] == "") ){ 
            $port_content = '<i class="fa fa-wifi"></i>';
          } elseif ($row['node_type'] == "Powerline") 
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
                                  <b class="anonymize">'.$row['name'].'</b>
                                </a>
                              </td>
                              <td class="anonymize">'
                                .$row['last_ip'].
                              '</td>
                              <td class="">
                                <button class="btn btn-primary btn-danger btn-sm" data-myleafmac="'.$row['mac'].'" >'.lang('Network_ManageUnassign').'</button>
                              </td>
                            </tr>';
          
        }        

        $str_table_close =    '</tbody>
                            </table>';

        // no connected device - don't render table, just display some info
        if($str_table_rows == "")
        {
          $str_table = "<div>                        
                          <div>
                            ".lang("Network_NoAssignedDevices")."
                          </div>
                        </div>";
          $str_table_close = "";
        }
         
        $str_close_pane = '</div>       
          </div>';  

        // write the HTML
        echo  ''.$str_tab_pane.
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
    //                          PC (leaf) <------- leafs are not included in this SQL query

    $networkDeviceTypes = str_replace("]", "",(str_replace("[", "", getSettingValue("NETWORK_DEVICE_TYPES"))));
    
    $sql = "SELECT node_name, node_mac, online, node_type, node_ports_count, parent_mac, node_icon
            FROM 
            (
                  SELECT  a.devName as  node_name,        
                        a.devMac as node_mac,
                        a.devPresentLastScan as online,
                        a.devType as node_type,
                        a.devParentMAC as parent_mac,
                        a.devIcon as node_icon
                  FROM Devices a 
                  WHERE a.devType in (".$networkDeviceTypes.") and devIsArchived = 0				
            ) t1
            LEFT JOIN
            (
                  SELECT  b.devParentMAC as node_mac_2,
                        count() as node_ports_count 
                  FROM Devices b 
                  WHERE b.devParentMAC NOT NULL group by b.devParentMAC
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
                              'online'                  => $row['online'],
                              'node_type'               => $row['node_type'],
                              'parent_mac'              => $row['parent_mac'],
                              'node_icon'               => $row['node_icon'],
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
        createDeviceTabs( $row['node_mac'], 
                          $row['node_name'], 
                          $row['online'],
                          $row['node_type'], 
                          $row['node_ports_count'],
                          $row['node_icon'],
                          $activetab);

                          $activetab = ""; // reset active tab indicator, only the first tab is active
      
    }
    echo ' </ul>  <div class="tab-content">';

    $activetab='active';    

    foreach ($tableData as $row) {                            
      createPane($row['node_mac'], 
                  $row['node_name'],
                  $row['online'], 
                  $row['node_type'], 
                  $row['node_ports_count'],
                  $row['parent_mac'],
                  $activetab);

                  $activetab = ""; // reset active tab indicator, only the first tab is active
    
    }

    ?>
    <!-- /.tab-pane -->
    </div>         
  </section>

  <!-- Unassigned devices -->
  <?php   

    // Get all Unassigned / unconnected nodes 
    $func_sql = 'SELECT 
                  devMac AS mac,
                  devPresentLastScan AS online,
                  devName AS name,
                  devLastIP AS last_ip,
                  devParentMAC
                FROM Devices
                WHERE devParentMAC IS NULL 
                  OR devParentMAC IN ("", " ", "undefined", "null")
                  AND devMac NOT LIKE "%internet%"
                ORDER BY name ASC;'; 

    global $db;
    $func_result = $db->query($func_sql);  

    // array 
    $tableData = array();
    while ($row = $func_result -> fetchArray (SQLITE3_ASSOC)) {   
      // Push row data      
      $tableData[] = array( 'mac'             => $row['mac'],
                            'online'          => $row['online'],
                            'name'            => $row['name'],
                            'last_ip'         => $row['last_ip']); 
    }

    // Don't do anything if empty
    if (!(empty($tableData))) {
      $str_table_header =  '
                        <div class="content">
                          <div id="unassignedDevices" class="box box-aqua box-body">
                            <section> 
                              <h3>
                                <i class="fa fa-laptop"></i> '.lang('Network_UnassignedDevices').'
                              </h3>
                              <table class="table table-striped">
                                <thead>
                                  <tr>
                                    <th  class="col-sm-1" ></th>
                                    <th  class="col-sm-1" >'.lang('Network_Table_State').'</th>
                                    <th  class="col-sm-2" >'.lang('Network_Table_Hostname').sortable_column.'</th>
                                    <th  class="col-sm-1" >'.lang('Network_Table_IP').sortable_column.'</th>
                                    <th  class="col-sm-3" >'.lang('Network_Assign').'</th>
                                  </tr>
                                </thead>
                                <tbody>
                                <tr>                              

                                </tr>';   

      $str_table_rows = "";        

      foreach ($tableData as $row) {  
        
        if ($row['online'] == 1) {
          $state = badge_online;
        } else {
          $state = badge_offline;
        }

        $str_table_rows = $str_table_rows.
                                          '
                                          <tr>                  
                                            <td> </td> 
                                            <td>'
                                              .$state.
                                            '</td>
                                            <td style="padding-left: 10px;">
                                              <a href="./deviceDetails.php?mac='.$row['mac'].'">
                                                <b class="anonymize">'.$row['name'].'</b>
                                              </a>
                                            </td>
                                            <td>'
                                              .$row['last_ip'].
                                            '</td>                                            
                                            <td>
                                            <button class="btn btn-primary btn-sm" data-myleafmac="'.$row['mac'].'" >'.lang('Network_ManageAssign').'</button>
                                          </td>
                                          </tr>';
      }        

      $str_table_close =    '</tbody>
                          </table>
                        </section>
                      </div>
                    </div>';

      // write the html
      echo $str_table_header.$str_table_rows.$str_table_close;     
    }


  ?>
    
    <!-- /.content -->
  </div>
  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->



<?php
  require 'php/templates/footer.php';
?>

<script src="lib/treeviz/bundle.js"></script> 



<script defer>
  $.get('php/server/devices.php?action=getDevicesList&status=all&forceDefaultOrder', function(data) {     

    rawData = JSON.parse (data)      

    if(rawData["data"] == "")
    {
      showModalOK (getString('Gen_Warning'), getString('Network_NoDevices'))      
      
      return;
    }

    orderTopologyBy = createArray(getSetting("UI_TOPOLOGY_ORDER"))

    devicesListnew = rawData["data"].map(item =>  { 
      return {
          "name": item[0], 
          "type": item[2], 
          "icon": item[3], 
          "mac": item[11], 
          "parentMac": item[14], 
          "rowid": item[13], 
          "status": item[10],
          "childrenQty": item[15],
          "port": item[18]
        };
    }).sort((a, b) => {
      // Helper to safely parse port into an integer; invalid ports become Infinity for sorting
      const parsePort = (port) => {
        const parsed = parseInt(port, 10);
        return isNaN(parsed) ? Infinity : parsed;
      };

      switch (orderTopologyBy[0]) {
        case "Name":
          // First sort by name alphabetically
          const nameCompare = a.name.localeCompare(b.name);
          if (nameCompare !== 0) {
            return nameCompare;
          }
          // If names are the same, sort by port numerically
          return parsePort(a.port) - parsePort(b.port);

        case "Port":
          // Sort by port numerically
          return parsePort(a.port) - parsePort(b.port);

        default:
          // Default: Sort by rowid (as a fallback)
          return a.rowid - b.rowid;
      }
    });

    setCache('devicesListNew', JSON.stringify(devicesListnew));

    // Init global variable
    deviceListGlobal = devicesListnew;
    
    // create tree
    initTree(getHierarchy());

    // attach on-click events
    attachTreeEvents();
  });
</script>


<script defer>
// ---------------------------------------------------------------------------
// Tree functionality
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
var leafNodesCount = 0;
var visibleNodesCount = 0;
var parentNodesCount = 0;
var hiddenMacs = []; // hidden children
var hiddenChildren = [];
var deviceListGlobal = null; 




// ---------------------------------------------------------------------------
// Recursively get children nodes and build a tree
function getChildren(node, list, path, visited = [])
{
    var children = [];

    // Check for infinite recursion by seeing if the node has been visited before
    if (visited.includes(node.mac.toLowerCase())) {
        console.error("Infinite recursion detected at node:", node.mac);
        write_notification("[ERROR] ⚠ Infinite recursion detected. You probably have assigned the Internet node to another children node or to itself. Please open a new issue on GitHub and describe how you did it.", 'interrupt')
        return { error: "Infinite recursion detected", node: node.mac };
    }

    // Add current node to visited list
    visited.push(node.mac.toLowerCase());

    // Loop through all items to find children of the current node
    for (var i in list) {
        if (list[i].parentMac.toLowerCase() == node.mac.toLowerCase() && !hiddenMacs.includes(list[i].parentMac)) {   

            visibleNodesCount++;

            // Process children recursively, passing a copy of the visited list
            children.push(getChildren(list[i], list, path + ((path == "") ? "" : '|') + list[i].parentMac, visited));
        }
    }

    // Track leaf and parent node counts
    if (children.length == 0) {
        leafNodesCount++;
    } else {
        parentNodesCount++;
    }

    return { 
        name: node.name,
        path: path,
        mac: node.mac,
        port: node.port,
        id: node.mac,
        parentMac: node.parentMac,
        icon: node.icon,
        type: node.type,
        status: node.status,
        hasChildren: children.length > 0 || hiddenMacs.includes(node.mac),
        hiddenChildren: hiddenMacs.includes(node.mac),
        qty: children.length,
        children: children
    };
}

// ---------------------------------------------------------------------------  
function getHierarchy()
{ 
  for(i in deviceListGlobal)
  {      
    if(deviceListGlobal[i].mac == 'Internet')
    { 
      return (getChildren(deviceListGlobal[i], deviceListGlobal, ''))
      break;
    }
  }
}

// ---------------------------------------------------------------------------
function getFlatData() {
  var result = [];
  var leafNodesCount = 0;
  var parentNodesCount = 0;
  var visibleNodesCount = 0;
  
  for (let node of deviceListGlobal) {
    let path = "";
    let childrenCount = 0;

    // count children of this node
    for (let nodeTmp of deviceListGlobal) {
        if (nodeTmp.parentMac === node.mac) {
            childrenCount++;
        }
    }
    
    // store parent and leaf node count
    if (childrenCount === 0) {
        leafNodesCount++;
    } else {
        parentNodesCount++;
    }
    
    if (!hiddenMacs.includes(node.parentMac)) {   
      if (!((node.parentMac == "") && node.mac != "Internet")) {  // skip leaf nodes without father that are not the root
        visibleNodesCount++;
        
        result.push({
            name: node.name,
            path: path,
            mac: node.mac, // Replacing "mac" with "id"
            parentMac: node.mac == "Internet" ? "" : node.parentMac, // Replacing "parentMac" with "father"
            port: node.port,
            icon: node.icon,
            type: node.type,
            status: node.status,
            hasChildren: childrenCount > 0 || hiddenMacs.includes(node.mac),
            hiddenChildren: hiddenMacs.includes(node.mac),
            qty: childrenCount,
        });
      }
    }
      
  }

  return result;
}
  
//---------------------------------------------------------------------------
function toggleSubTree(parentMac, treePath)
{
  treePath = treePath.split('|')

  if(!hiddenMacs.includes(parentMac))
  {
    hiddenMacs.push(parentMac)
  }
  else
  {
    removeItemFromArray(hiddenMacs, parentMac)
  }

  updatedTree = getHierarchy()
  myTree.refresh(updatedTree);

  // re-attach any onclick events
  attachTreeEvents();   
}

// --------------------------------------------------------------------------- 
function attachTreeEvents()
{
  //  toggle subtree functionality
  $("div[data-mytreemac]").each(function(){
      $(this).attr('onclick', 'toggleSubTree("'+$(this).attr('data-mytreemac')+'","'+ $(this).attr('data-mytreepath')+'")')        
  }); 
}

// --------------------------------------------------------------------------- 
// Handle network node click - select correct tab in the bottom table
function handleNodeClick(el)
{    
  const targetTabMAC = $(el).attr("data-mytreemacmain");    

  var targetTab = $(`a[data-mytabmac="${targetTabMAC}"]`);

  if (targetTab.length) {
    // Simulate a click event on the target tab
    targetTab.click();

    // Smooth scroll to the tab content
    $('html, body').animate({
      scrollTop: targetTab.offset().top - 50
    }, 500); // Adjust the duration as needed
  }
}

// --------------------------------------------------------------------------- 
var myTree;


var emSize;
var nodeHeight;
// var sizeCoefficient = 1.4

function pxToEm(px, element) {
    var baseFontSize = parseFloat($(element || "body").css("font-size"));
    return px / baseFontSize;
}

function emToPx(em, element) {
    var baseFontSize = parseFloat($(element || "body").css("font-size"));
    return Math.round(em * baseFontSize);
}

function initTree(myHierarchy)
{
  // calculate the drawing area based on teh tree width and available screen size
  
  let baseFontSize = parseFloat($('html').css('font-size')); 
  let treeAreaHeight = ($(window).height() - 155); ;
  // calculate the font size of the leaf nodes to fit everything into the tree area
  leafNodesCount == 0 ? 1 : leafNodesCount;

  emSize = pxToEm((treeAreaHeight/(leafNodesCount)).toFixed(2));
  
  let screenWidthEm = pxToEm($('.networkTable').width());

  // init the drawing area size
  $("#networkTree").attr('style', `height:${treeAreaHeight}px; width:${emToPx(screenWidthEm)}px`)

  if(myHierarchy.type == "")
  {
    showModalOk(getString('Network_Configuration_Error'), getString('Network_Root_Not_Configured'))      
    
    return;
  }

  // handle if only a few nodes
  emSize > 1 ? emSize = 1 : emSize = emSize;

  let nodeHeightPx = emToPx(emSize*1);
  let nodeWidthPx = emToPx(screenWidthEm / (parentNodesCount));

  // handle if only a few nodes
  nodeWidthPx > 160 ? nodeWidthPx = 160 : nodeWidthPx = nodeWidthPx;

  console.log(Treeviz);

  myTree = Treeviz.create({
    htmlId: "networkTree",
    renderNode:  nodeData =>  {

      
      (!emptyArr.includes(nodeData.data.port )) ? port =  nodeData.data.port : port = "";

      (port == "" || port == 0 || port == 'None' ) ? portBckgIcon = `<i class="fa fa-wifi"></i>` : portBckgIcon = `<i class="fa fa-ethernet"></i>`;

      portHtml = (port == "" || port == 0 || port == 'None' ) ? "" : port;
      
      // Build HTML for individual nodes in the network diagram        
      deviceIcon = (!emptyArr.includes(nodeData.data.icon )) ?  
                `<div class="netIcon">
                      ${atob(nodeData.data.icon)}
                </div>` : "";
      devicePort = `<div  class="netPort" 
                          style="width:${emSize}em;height:${emSize}em">
                      ${portHtml}</div> 
                    <div  class="portBckgIcon" 
                          style="margin-left:-${emSize}em;">
                          ${portBckgIcon}
                    </div>`;
      collapseExpandIcon = nodeData.data.hiddenChildren ? 
                          "square-plus" : "square-minus";
                          
      // generate +/- icon if node has children nodes
      collapseExpandHtml = nodeData.data.hasChildren ? 
                    `<div class="netCollapse" 
                          style="font-size:${nodeHeightPx/2}px;top:${nodeHeightPx/4}px" 
                          data-mytreepath="${nodeData.data.path}" 
                          data-mytreemac="${nodeData.data.mac}">
                      <i class="fa fa-${collapseExpandIcon} pointer"></i>
                    </div>` : "";

      selectedNodeMac = $(".nav-tabs-custom .active a").attr('data-mytabmac')

      highlightedCss = nodeData.data.mac == selectedNodeMac ? 
                    " highlightedNode" : "";

      // css indicating online/offline status
      statusCss = ` netStatus-${nodeData.data.status}`;

      return result = `<div 
                            class="node-inner box ${nodeData.data.hasChildren ? "pointer":""} ${statusCss} ${highlightedCss}"
                            data-mytreemacmain="${nodeData.data.mac}"
                            style="height:${nodeHeightPx}px;font-size:${nodeHeightPx-5}px;"
                            onclick="handleNodeClick(this)"
                        >
                          <div class="netNodeText">
                            <strong>${devicePort}  ${deviceIcon}
                              <span class="spanNetworkTree anonymizeDev" style="width:${nodeWidthPx-50}px">${nodeData.data.name}</span>
                            </strong>                            
                          </div>                          
                        </div>
                        ${collapseExpandHtml}`;
    },
    mainAxisNodeSpacing: 'auto',
    // secondaryAxisNodeSpacing: 0.3,
    nodeHeight: nodeHeightPx,
    nodeWidth: nodeWidthPx,
    marginTop: '5',
    isHorizontal : true,
    hasZoom: true,
    hasPan: true,
    marginLeft: '15',
    idKey: "mac",
    hasFlatData: false,
    relationnalField: "children",
    linkWidth: (nodeData) => 3,
    linkColor: (nodeData) => "#ffcc80"
    // onNodeClick: (nodeData) => handleNodeClick(nodeData),
  });      

  console.log(deviceListGlobal);
  myTree.refresh(myHierarchy);

  // hide spinning icon
  hideSpinner()
}


// ---------------------------------------------------------------------------
// Tabs functionality
// ---------------------------------------------------------------------------
// Register events on tab change

$('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {   

  initButtons()

});


// ---------------------------------------------------------------------------
function initTab()
{
  key = "activeNetworkTab"

  // default selection
  selectedTab = "Internet_id"

  // the #target from the url
  target = getQueryString('mac') 

  // update cookie if target specified
  if(target != "")
  {      
    setCache(key, target.replaceAll(":","_")+'_id') // _id is added so it doesn't conflict with AdminLTE tab behavior
  }

  // get the tab id from the cookie (already overridden by the target)
  if(!emptyArr.includes(getCache(key)))
  {
    selectedTab = getCache(key);
  }

  // Activate panel
  $('.nav-tabs a[id='+ selectedTab +']').tab('show');

  // When changed save new current tab
  $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    setCache(key, $(e.target).attr('id'))
  });
  
}

// ---------------------------------------------------------------------------
function initDeviceNamesFromMACs()
{
  $('.mac-to-name').each(function() {
      var dataMacValue = $(this).attr('my-data-mac');

      if(dataMacValue =="" )
      {
        $(this).html(getString("Network_Root"))
      }
      else{
        $(this).html(getNameByMacAddress(dataMacValue));
      }
  });
  
}

// ---------------------------------------------------------------------------
function initButtons()
{ 

  var currentNodeMac = $(".tab-content .active td[data-mynodemac]").attr('data-mynodemac'); 

  // change highlighted node in the tree
  selNode = $("#networkTree .highlightedNode")[0]

  // console.log(selNode)

  if(selNode)
  {
    $(selNode).attr('class',  $(selNode).attr('class').replace('highlightedNode'))
  }

  newSelNode = $("#networkTree div[data-mytreemacmain='"+currentNodeMac+"']")[0]
  
  $(newSelNode).attr('class',  $(newSelNode).attr('class') + ' highlightedNode')


  // init the Assign buttons
  $('#unassignedDevices  button[data-myleafmac]').each(function(){
    $(this).attr('onclick', `updateLeaf("${$(this).attr('data-myleafmac')}","${currentNodeMac}")`)
  }); 

  // init Unassign buttons
  $('#assignedDevices button[data-myleafmac]').each(function(){
    $(this).attr('onclick', `updateLeaf("${$(this).attr('data-myleafmac')}","")`)
  }); 
}

// ---------------------------------------------------------------------------
function updateLeaf(leafMac,nodeMac)
{
  console.log(leafMac) // child
  console.log(nodeMac) // parent
  console.log(nodeMac != "") // parent

  // prevent the assignment of the Internet root node avoiding recursion when generating the network tree topology
  if(leafMac.toLowerCase().includes('internet') && nodeMac != "")
  {
    showMessage(getString('Network_Cant_Assign'))
  }
  else{
    saveData('updateNetworkLeaf', leafMac, nodeMac);
    setTimeout("location.reload();", 500); // refresh page 
  }
}

// init device names where macs are used
initDeviceNamesFromMACs();

// init selected (first) tab
initTab();  

// init Assign/Unassign buttons
initButtons()

</script>



