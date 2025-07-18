<?php

  require 'php/templates/header.php';
  require 'php/templates/notification.php';
  
?>
    
<script>
  // show spinning icon
  showSpinner()
</script>  

<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">
  <span class="helpIcon"> 
    <a target="_blank" href="https://github.com/jokob-sk/NetAlertX/blob/main/docs/NETWORK_TREE.md">
      <i class="fa fa-circle-question"></i>
    </a>
  </span>

  <div id="toggleFilters" class="">    
      <div class="checkbox icheck col-xs-12">
        <label>
          <input type="checkbox" name="showOffline" checked>
            <div style="margin-left: 10px; display: inline-block; vertical-align: top;"> 
              <?= lang('Network_ShowOffline');?>
            </div>
        </label>
      </div>
      <div class="checkbox icheck col-xs-12">
        <label>
          <input type="checkbox" name="showArchived">
            <div style="margin-left: 10px; display: inline-block; vertical-align: top;"> 
              <?= lang('Network_ShowArchived');?>
            </div>
        </label>      
      </div>    
  </div>

  <div id="networkTree" class="drag">
    <!-- Tree topology Placeholder -->
  </div>

  <!-- Main content ---------------------------------------------------------- -->
  <section class="content networkTable">
    <!-- /.content -->
    <div class="nav-tabs-custom">
      <ul class="nav nav-tabs">
        <!-- Placeholder -->
      </ul>
    </div>
    <div class="tab-content">
      <!-- Placeholder -->
    </div>    
  </section>  
  <section id="unassigned-devices-wrapper">
      <!-- Placeholder -->
    </section>
    <!-- /.content -->
</div>
<!-- /.content-wrapper -->
<!-- ----------------------------------------------------------------------- -->

<?php
  require 'php/templates/footer.php';
?>

<script src="lib/treeviz/bundle.js"></script> 

<script defer>

  // -----------------------------------------------------------------------
  function loadNetworkNodes() {

    // Create Top level tabs   (List of network devices), explanation of the terminology below:
    //
    //             Switch 1 (node) 
    //              /(p1)    \ (p2)     <----- port numbers
    //             /          \
    //   Smart TV (leaf)      Switch 2 (node (for the PC) and leaf (for Switch 1))
    //                          \
    //                          PC (leaf) <------- leafs are not included in this SQL query 


    const networkDeviceTypes = getSetting("NETWORK_DEVICE_TYPES").replace("[", "").replace("]", "");
    const rawSql = `
      SELECT node_name, node_mac, online, node_type, node_ports_count, parent_mac, node_icon, node_alert
      FROM (
        SELECT a.devName as node_name, a.devMac as node_mac, a.devPresentLastScan as online,
              a.devType as node_type, a.devParentMAC as parent_mac, a.devIcon as node_icon, a.devAlertDown as node_alert
        FROM Devices a
        WHERE a.devType IN (${networkDeviceTypes}) and a.devIsArchived = 0
      ) t1
      LEFT JOIN (
        SELECT b.devParentMAC as node_mac_2, count() as node_ports_count
        FROM Devices b
        WHERE b.devParentMAC NOT NULL
        GROUP BY b.devParentMAC
      ) t2
      ON (t1.node_mac = t2.node_mac_2)
    `;

    const apiUrl = `php/server/dbHelper.php?action=read&rawSql=${btoa(encodeURIComponent(rawSql))}`;

    $.get(apiUrl, function (data) {
      const nodes = JSON.parse(data);
      renderNetworkTabs(nodes);
      loadUnassignedDevices();
    });
  }

  // -----------------------------------------------------------------------
  function renderNetworkTabs(nodes) {
    let html = '';
    nodes.forEach((node, i) => {
      const iconClass = node.online == 1 ? "text-green" :
                        (node.node_alert == 1 ? "text-red" : "text-gray50");

      const portLabel = node.node_ports_count ? ` (${node.node_ports_count})` : '';
      const icon = atob(node.node_icon);
      const id = node.node_mac.replace(/:/g, '_');      

      html += `
        <li class="networkNodeTabHeaders ${i === 0 ? 'active' : ''}">
          <a href="#${id}" data-mytabmac="${node.node_mac}" id="${id}_id" data-toggle="tab" title="${node.node_name}">
            <div class="icon ${iconClass}">${icon}</div>
            <span class="node-name">${node.node_name}</span>${portLabel}
          </a>
        </li>`;
    });

    $('.nav-tabs').html(html);

    // populate tabs
    renderNetworkTabContent(nodes);

    // init selected (first) tab
    initTab();  

    // init selected node highlighting 
    initSelectedNodeHighlighting()

    // Register events on tab change
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {   
      initSelectedNodeHighlighting()
    });
  }

  // -----------------------------------------------------------------------
  function renderNetworkTabContent(nodes) {
    $('.tab-content').empty();

    nodes.forEach((node, i) => {
      const id = node.node_mac.replace(/:/g, '_');

      const badge = getStatusBadgeParts(
        node.online,
        node.node_alert,
        node.node_mac
      );

      const badgeHtml = `<a href="${badge.url}" class="badge ${badge.cssClass}">${badge.iconHtml} ${badge.status}</a>`;
      const parentId = node.parent_mac.replace(/:/g, '_');

      const paneHtml = `
        <div class="tab-pane box box-aqua box-body ${i === 0 ? 'active' : ''}" id="${id}">
          <h2 class="page-header"><i class="fa fa-server"></i> ${getString('Network_Node')}</h2>
          <table class="table table-striped">
            <tbody>
              <tr><td><b>${getString('Network_Node')}</b></td><td><a href="./deviceDetails.php?mac=${node.node_mac}" class="anonymize">${node.node_name}</a></td></tr>
              <tr><td><b>MAC</b></td><td class="anonymize">${node.node_mac}</td></tr>
              <tr><td><b>${getString('Device_TableHead_Type')}</b></td><td>${node.node_type}</td></tr>
              <tr><td><b>${getString('Network_Table_State')}</b></td><td>${badgeHtml}</td></tr>
              <tr><td><b>${getString('Network_Parent')}</b></td>
                  <td>
                    <a href="./network.php?mac=${parentId}">
                      <b class="anonymize"><span class="mac-to-name" my-data-mac="${node.parent_mac}">${node.parent_mac}</span>
                      <i class="fa fa-square-up-right"></i></b>
                    </a>
                  </td></tr>
            </tbody>
          </table>
          <div class=" box box-aqua box-body" id="connected">
            <h3 class="page-header">
              <i class="fa fa-sitemap"></i> 
              ${getString('Network_Connected')}
            </h3>
          
            <div  id="leafs_${id}">
            </div>
          </div>

        </div>`;

      $('.tab-content').append(paneHtml);
      loadConnectedDevices(node.node_mac);
    });
  }

  // ----------------------------------------------------
  function loadDeviceTable({ sql, containerSelector, tableId, wrapperHtml = null, assignMode = true }) {
    const apiUrl = `php/server/dbHelper.php?action=read&rawSql=${btoa(encodeURIComponent(sql))}`;

    $.get(apiUrl, function (data) {
      const devices = JSON.parse(data);
      const $container = $(containerSelector);

      // end if nothing to show
      if(devices.length == 0)
      {
        return;
      }

      
      $container.html(wrapperHtml);
      
      const $table = $(`#${tableId}`);

      const columns = [
        {
          title: getString('Network_Table_State'),
          data: 'devStatus',
          width: '15%',
          render: function (_, type, device) {
            const badge = getStatusBadgeParts(
              device.devPresentLastScan,
              device.devAlertDown,
              device.devMac
            );
            return `<a href="${badge.url}" class="badge ${badge.cssClass}">${badge.iconHtml} ${badge.status}</a>`;
          }
        },
        {
          title: getString('Device_TableHead_Name'),
          data: 'devName',
          width: '15%',
          render: function (name, type, device) {
            return `<a href="./deviceDetails.php?mac=${device.devMac}">
                      <b class="anonymize">${name || '-'}</b>
                    </a>`;
          }
        },
        {
          title: 'MAC',
          data: 'devMac',
          width: '5%',
          render: (data) => `<span class="anonymize">${data}</span>`
        },
        {
          title: getString('Network_Table_IP'),
          data: 'devLastIP',
          width: '5%'
        },
        {
          title: getString('Device_TableHead_Vendor'),
          data: 'devVendor',
          width: '20%'
        },
        {
          title: assignMode ? getString('Network_ManageAssign') : getString('Network_ManageUnassign'),
          data: 'devMac',
          orderable: false,
          width: '5%',
          render: function (mac) {
            const label = assignMode ? 'assign' : 'unassign';
            const btnClass = assignMode ? 'btn-primary' : 'btn-primary bg-red';
            const btnText = assignMode ? getString('Network_ManageAssign') : getString('Network_ManageUnassign');
            return `<button class="btn ${btnClass} btn-sm" data-myleafmac="${mac}" onclick="updateLeaf('${mac}','${label}')">
                      ${btnText}
                    </button>`;
          }
        }
      ].filter(Boolean);


      tableConfig = {
          data: devices,
          columns: columns,
          pageLength: 10,
          order: assignMode ? [[2, 'asc']] : [],
          responsive: true,
          autoWidth: false,
          searching: true
        }

      if ($.fn.DataTable.isDataTable($table)) {
        $table.DataTable(tableConfig).clear().rows.add(devices).draw();
      } else {
        $table.DataTable(tableConfig);
      }
    });
  }

  // ----------------------------------------------------
  function loadUnassignedDevices() {
    const sql = `
      SELECT devMac, devPresentLastScan, devName, devLastIP, devVendor, devAlertDown
      FROM Devices
      WHERE (devParentMAC IS NULL OR devParentMAC IN ("", " ", "undefined", "null"))
        AND devMac NOT LIKE "%internet%"
        AND devIsArchived = 0
      ORDER BY devName ASC`;

    const wrapperHtml = `
      <div class="content">
        <div id="unassignedDevices" class="box box-aqua box-body">
          <section>
            <h3><i class="fa fa-laptop"></i> ${getString('Network_UnassignedDevices')}</h3>
            <table id="unassignedDevicesTable" class="table table-striped" width="100%"></table>
          </section>
        </div>
      </div>`;

    loadDeviceTable({
      sql,
      containerSelector: '#unassigned-devices-wrapper',
      tableId: 'unassignedDevicesTable',
      wrapperHtml,
      assignMode: true
    });
  }

  // ----------------------------------------------------
  function loadConnectedDevices(node_mac) {
    const sql = `
      SELECT devName, devMac, devLastIP, devVendor, devPresentLastScan, devAlertDown,
        CASE
          WHEN devAlertDown != 0 AND devPresentLastScan = 0 THEN "Down"
          WHEN devPresentLastScan = 1 THEN "On-line"
          ELSE "Off-line"
        END as devStatus
      FROM Devices
      WHERE devIsArchived = 0 AND devParentMac = '${node_mac}'`;

    const id = node_mac.replace(/:/g, '_');

    const wrapperHtml = `
      <table class="table table-bordered table-striped node-leafs-table" id="table_leafs_${id}" data-node-mac="${node_mac}">
            
      </table>`;

    loadDeviceTable({
      sql,
      containerSelector: `#leafs_${id}`,
      tableId: `table_leafs_${id}`,
      wrapperHtml,
      assignMode: false
    });
  }

  // INIT

  const showArchived = getCache('showArchived') == "true";
  const showOffline = getCache('showOffline') == "true";

  console.log('showArchived:', showArchived);
  console.log('showOffline:', showOffline);

  // Build WHERE conditions dynamically
  let filters = [];

  if (!showArchived) {
    filters.push(`a.devIsArchived = 0`);
  }

  if (!showOffline) {
    filters.push(`a.devPresentLastScan != 0`);
  }

  // Assemble WHERE clause only if filters exist
  const whereClause = filters.length > 0 ? `WHERE ${filters.join(' AND ')}` : '';

  console.log(whereClause);

  const rawSql = `
    SELECT *,
      CASE
        WHEN devAlertDown != 0 AND devPresentLastScan = 0 THEN "Down"
        WHEN devPresentLastScan = 1 THEN "On-line"
        ELSE "Off-line"
      END as devStatus
    FROM Devices a
    ${whereClause}
  `;

  const apiUrl = `php/server/dbHelper.php?action=read&rawSql=${btoa(encodeURIComponent(rawSql))}`;

  $.get(apiUrl, function (data) {
  
    rawData = JSON.parse (data)      

    console.log(rawData);

    if(rawData["data"] == "")
    {
      showModalOK (getString('Gen_Warning'), getString('Network_NoDevices'))      
      
      return;
    }

    orderTopologyBy = createArray(getSetting("UI_TOPOLOGY_ORDER"))

    devicesListnew = rawData.sort((a, b) => {
      // Helper to safely parse port into an integer; invalid ports become Infinity for sorting
      const parsePort = (devParentPort) => {
        const parsed = parseInt(devParentPort, 10);
        return isNaN(parsed) ? Infinity : parsed;
      };

      switch (orderTopologyBy[0]) {
        case "Name":
          // First sort by name alphabetically
          const nameCompare = a.devName.localeCompare(b.devName);
          if (nameCompare !== 0) {
            return nameCompare;
          }
          // If names are the same, sort by port numerically
          return parsePort(a.devParentPort) - parsePort(b.devParentPort);

        case "Port":
          // Sort by port numerically
          return parsePort(a.devParentPort) - parsePort(b.devParentPort);

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

    // bottom tables
    loadNetworkNodes();    
   
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
    if (visited.includes(node.devMac.toLowerCase())) {
        console.error("Infinite recursion detected at node:", node.devMac);
        write_notification("[ERROR] ⚠ Infinite recursion detected. You probably have assigned the Internet node to another children node or to itself. Please open a new issue on GitHub and describe how you did it.", 'interrupt')
        return { error: "Infinite recursion detected", node: node.devMac };
    }

    // Add current node to visited list
    visited.push(node.devMac.toLowerCase());

    // Loop through all items to find children of the current node
    for (var i in list) {
        if (list[i].devParentMAC.toLowerCase() == node.devMac.toLowerCase() && !hiddenMacs.includes(list[i].devParentMAC)) {   

            visibleNodesCount++;

            // Process children recursively, passing a copy of the visited list
            children.push(getChildren(list[i], list, path + ((path == "") ? "" : '|') + list[i].devParentMAC, visited));
        }
    }

    // Track leaf and parent node counts
    if (children.length == 0) {
        leafNodesCount++;
    } else {
        parentNodesCount++;
    }

    return { 
        name: node.devName,
        path: path,
        mac: node.devMac,
        port: node.devParentPort,
        id: node.devMac,
        parentMac: node.devParentMAC,
        icon: node.devIcon,
        type: node.devType,
        vendor: node.devVendor,
        lastseen: node.devLastConnection,
        firstseen: node.devFirstConnection,
        ip: node.devLastIP,
        status: node.devStatus,
        presentLastScan: node.devPresentLastScan,
        alertDown: node.devAlertDown,
        hasChildren: children.length > 0 || hiddenMacs.includes(node.devMac),
        relType: node.devParentRelType,
        hiddenChildren: hiddenMacs.includes(node.devMac),
        qty: children.length,
        children: children
    };
}

// ---------------------------------------------------------------------------  
function getHierarchy()
{ 
  for(i in deviceListGlobal)
  {      
    if(deviceListGlobal[i].devMac == 'Internet')
    { 
      return (getChildren(deviceListGlobal[i], deviceListGlobal, ''))
      break;
    }
  }
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

  // handle network node
  var targetTab = $(`a[data-mytabmac="${targetTabMAC}"]`);

  if (targetTab.length) {
    // Simulate a click event on the target tab
    targetTab.click();

    // Smooth scroll to the tab content
    $('html, body').animate({
      scrollTop: targetTab.offset().top - 50
    }, 500); // Adjust the duration as needed
  } else
  {
    // handle regular device - open in new tab
    goToDevice($(el).data("mac"), true)
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
  
  let screenWidthEm = pxToEm($('.networkTable').width()-15);

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
                          style="margin-left:-${emSize*0.7}em;">
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

      const badgeConf = getStatusBadgeParts(nodeData.data.presentLastScan, nodeData.data.alertDown, nodeData.data.mac, statusText = '')

      return result = `<div 
                            class="node-inner hover-node-info box pointer ${highlightedCss}"
                            style="height:${nodeHeightPx}px;font-size:${nodeHeightPx-5}px;"
                            onclick="handleNodeClick(this)"
                            data-mytreemacmain="${nodeData.data.mac}"                            
                            data-name="${nodeData.data.name}"
                            data-ip="${nodeData.data.ip}"
                            data-mac="${nodeData.data.mac}"
                            data-vendor="${nodeData.data.vendor}"
                            data-type="${nodeData.data.type}"
                            data-lastseen="${nodeData.data.lastseen}"
                            data-firstseen="${nodeData.data.firstseen}"
                            data-relationship="${nodeData.data.relType}"
                            data-status="${nodeData.data.status}"
                            data-present="${nodeData.data.presentLastScan}"
                            data-alert="${nodeData.data.alertDown}"
                            data-icon="${nodeData.data.icon}"
                        >
                          <div class="netNodeText">
                            <strong><span>${devicePort}  <span class="${badgeConf.cssText}">${deviceIcon}</span></span>
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
    marginLeft: '10',
    marginRight: '10',
    idKey: "mac",
    hasFlatData: false,
    relationnalField: "children",
    linkWidth: (nodeData) => 3,
    linkColor: (nodeData) => {  

      relConf = getRelationshipConf(nodeData.data.relType)  

      return relConf.color;
    }
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
function initSelectedNodeHighlighting()
{ 

  var currentNodeMac = $(".networkNodeTabHeaders.active a").data("mytabmac");

  // change highlighted node in the tree
  selNode = $("#networkTree .highlightedNode")[0]

  console.log(selNode)

  if(selNode)
  {
    $(selNode).attr('class',  $(selNode).attr('class').replace('highlightedNode'))
  }

  newSelNode = $("#networkTree div[data-mytreemacmain='"+currentNodeMac+"']")[0]

  console.log(newSelNode)
  
  $(newSelNode).attr('class',  $(newSelNode).attr('class') + ' highlightedNode')
}

// ---------------------------------------------------------------------------
function updateLeaf(leafMac, action) {
  console.log(leafMac); // child
  console.log(action);  // action

  const nodeMac = $(".networkNodeTabHeaders.active a").data("mytabmac") || "";

  if (action === "assign") {
    if (!nodeMac) {
      showMessage(getString("Network_Cant_Assign_No_Node_Selected"));
    } else if (leafMac.toLowerCase().includes("internet")) {
      showMessage(getString("Network_Cant_Assign"));
    } else {
      saveData("updateNetworkLeaf", leafMac, nodeMac);
      setTimeout(() => location.reload(), 500);
    }

  } else if (action === "unassign") {
    saveData("updateNetworkLeaf", leafMac, "");
    setTimeout(() => location.reload(), 500);

  } else {
    console.warn("Unknown action:", action);
  }
}

// init device names where macs are used
initDeviceNamesFromMACs();

// init pop up hover  boxes for device details
initHoverNodeInfo();

// display toggles
$(document).ready(function () {
  // Restore cached values on load
  const cachedOffline = getCache('showOffline');
  if (cachedOffline !== null) {
    $('input[name="showOffline"]').prop('checked', cachedOffline === 'true');
  }

  const cachedArchived = getCache('showArchived');
  if (cachedArchived !== null) {
    $('input[name="showArchived"]').prop('checked', cachedArchived === 'true');
  }

  // Bind change event for both toggles
  $('input[name="showOffline"], input[name="showArchived"]').on('change', function () {
    const name = $(this).attr('name');
    const value = $(this).is(':checked');
    setCache(name, value);

    // Refresh page after a brief delay to ensure cache is written
    setTimeout(() => {
      location.reload();
    }, 100);
  });
});

</script>



