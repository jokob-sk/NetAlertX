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
// ## Create Table if not exists'
// #####################################
$sql = 'CREATE TABLE IF NOT EXISTS "network_infrastructure" (
	"device_id"	INTEGER,
	"net_device_name"	TEXT NOT NULL,
	"net_device_typ"	TEXT NOT NULL,
  "net_device_port"  INTEGER,
	PRIMARY KEY("device_id" AUTOINCREMENT)
)';
$result = $db->query($sql);
// #####################################
// ## Expand Devices Table
// #####################################
$sql = 'ALTER TABLE "Devices" ADD "dev_Infrastructure" INTEGER';
$result = $db->query($sql);
$sql = 'ALTER TABLE "Devices" ADD "dev_Infrastructure_port" INTEGER';
$result = $db->query($sql);
// #####################################
// Add New Network Devices
// #####################################
if ($_REQUEST['Networkinsert'] == "yes") {
	if (isset($_REQUEST['NetworkDeviceName']) && isset($_REQUEST['NetworkDeviceTyp']))
	{
		$sql = 'INSERT INTO "network_infrastructure" ("net_device_name", "net_device_typ", "net_device_port") VALUES("'.$_REQUEST['NetworkDeviceName'].'", "'.$_REQUEST['NetworkDeviceTyp'].'", "'.$_REQUEST['NetworkDevicePort'].'")';	
		$result = $db->query($sql);
	}
}
// #####################################
// remove Network Devices
// #####################################
if ($_REQUEST['Networkdelete'] == "yes") {
	if (isset($_REQUEST['NetworkDeviceID']))
	{
		$sql = 'DELETE FROM "network_infrastructure" WHERE "device_id"="'.$_REQUEST['NetworkDeviceID'].'"';	
		$result = $db->query($sql);	
	}
}

?>
<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
         Netzwerkvisualisierung
      </h1>
    </section>

<?php
echo $_REQUEST['device_id'];
?>
    <!-- Main content ---------------------------------------------------------- -->
    <section class="content">
		<div class="box box-default collapsed-box">
        <div class="box-header with-border">
          <h3 class="box-title">Verwalte Netzwerk-Geräte</h3>
          <div class="box-tools pull-right">
            <button type="button" class="btn btn-box-tool" data-widget="collapse"><i class="fa fa-minus"></i></button>
          </div>
        </div>
        <!-- /.box-header -->
        <div class="box-body" style="">
          <div class="row">
            <div class="col-md-6">
            <form role="form" method="post" action="./network.php">
              <div class="form-group">
                <label for="exampleInputEmail1">Netzwerk Gerät hinzufügen:</label>
                <input type="text" class="form-control" id="NetworkDeviceName" name="NetworkDeviceName" placeholder="Name">
              </div>
              <!-- /.form-group -->
              <div class="form-group">
               <label>Typ</label>
                  <select class="form-control" name="NetworkDeviceTyp">
                    <option value="">-- Select Typ --</option>
                    <option value="Router">Router</option>
                    <option value="Switch">Switch</option>
                    <option value="WLAN">WLAN</option>
                  </select>
              </div>
              <div class="form-group">
                <label for="exampleInputEmail1">Portanzahl des Gerätes:</label>
                <input type="text" class="form-control" id="NetworkDevicePort" name="NetworkDevicePort" placeholder="Portanzahl">
              </div>
              <div class="form-group">
              <button type="submit" class="btn btn-success" name="Networkinsert" value="yes">Hinzufügen</button>
          	  </div>
          </form>
              <!-- /.form-group -->
            </div>
            <!-- /.col -->
            <div class="col-md-6">
              <form role="form" method="post" action="./network.php">
              <div class="form-group">
              	<label>Netzwerk Gerät entfernen:</label>
                  <select class="form-control" name="NetworkDeviceID">
                    <option value="">-- Select Typ --</option>
					<?php
					$sql = 'SELECT "device_id", "net_device_name", "net_device_typ" FROM "network_infrastructure"'; 
					$result = $db->query($sql);//->fetchArray(SQLITE3_ASSOC); 
					while($res = $result->fetchArray(SQLITE3_ASSOC)){
						if(!isset($res['device_id'])) continue; 
					    echo '<option value="'.$res['device_id'].'">'.$res['net_device_name'].' / '.$res['net_device_typ'].'</option>';
					} 
					?>
                  </select>
              </div>
              <!-- /.form-group -->
              <div class="form-group">
                <button type="submit" class="btn btn-danger" name="Networkdelete" value="yes">Entfernen</button>
              </div>
         	 </form>
              <!-- /.form-group -->
            </div>
            <!-- /.col -->
          </div>
          <!-- /.row -->
        </div>
        <!-- /.box-body -->
      </div>

<?php
function createnetworktab($pia_func_netdevid, $pia_func_netdevname, $pia_func_netdevtyp, $pia_func_netdevport, $activetab) {
	echo '<li class="'.$activetab.'"><a href="#'.$pia_func_netdevid.'" data-toggle="tab">'.$pia_func_netdevname.' / '.$pia_func_netdevtyp;
  if ($pia_func_netdevport != "") {echo ' ('.$pia_func_netdevport.')';}
  echo '</a></li>';
}
function createnetworktabcontent($pia_func_netdevid, $pia_func_netdevname, $pia_func_netdevtyp, $pia_func_netdevport, $activetab) {
	echo '<div class="tab-pane '.$activetab.'" id="'.$pia_func_netdevid.'">
	      <h4>'.$pia_func_netdevname.' (ID: '.$pia_func_netdevid.')</h4><br>';

  echo '<div class="box-body no-padding">
    <table class="table table-striped">
      <tbody><tr>
        <th style="width: 40px">Port</th>
        <th style="width: 100px">State</th>
        <th>Hostname</th>
        <th>Last known IP</th>
      </tr>';
  // Prepare Array
  if ($pia_func_netdevport == "") {$pia_func_netdevport = 1;}
  //echo $pia_func_netdevport;
  $network_device_portname = array();
  $network_device_portmac = array();
  $network_device_portip = array();
  $network_device_portstate = array();
  if ($pia_func_netdevport > 1)
    {
        for ($x=1; $x<=$pia_func_netdevport; $x++) { $network_device_portname[$x] = ''; $network_device_portmac[$x] = ''; $network_device_portip[$x] = ''; $network_device_portstate[$x] = ''; }
    }
  // Debug
  // print_r($network_device_port);
  // SQL for Devices with Network Device Number
	global $db;
	$func_sql = 'SELECT * FROM "Devices" WHERE "dev_Infrastructure" = "'.$pia_func_netdevid.'"';
	$func_result = $db->query($func_sql);//->fetchArray(SQLITE3_ASSOC); 
	while($func_res = $func_result->fetchArray(SQLITE3_ASSOC)){
    // Debug
		//if(!isset($func_res['dev_Name'])) continue;
		if ($func_res['dev_PresentLastScan'] == 1) {$port_state = '<div class="badge bg-green text-white" style="width: 60px;">Up</div>';} else {$port_state = '<div class="badge bg-red text-white" style="width: 60px;">Down</div>';}
		//echo 'Port: '.$func_res['dev_Infrastructure_port'].' - '.$port_state.' - <a href="./deviceDetails.php?mac='.$func_res['dev_MAC'].'">'.$func_res['dev_Name'].' - '.$func_res['dev_LastIP'].'</a><br>';
    if ($pia_func_netdevport > 1)
      {
        $network_device_portname[$func_res['dev_Infrastructure_port']] = $func_res['dev_Name'];
        $network_device_portmac[$func_res['dev_Infrastructure_port']] = $func_res['dev_MAC'];
        $network_device_portip[$func_res['dev_Infrastructure_port']] = $func_res['dev_LastIP'];
        $network_device_portstate[$func_res['dev_Infrastructure_port']] = $func_res['dev_PresentLastScan'];
      } else {
// Table without Port
        echo '<tr><td>###</td><td>'.$port_state.'</td><td><a href="./deviceDetails.php?mac='.$func_res['dev_MAC'].'">'.$func_res['dev_Name'].'</td><td>'.$func_res['dev_LastIP'].'</a></td></tr>';
      }
	}
  // Debug
  //print_r($network_device_portname);
  //print_r($network_device_portmac);
  //print_r($network_device_portip);
  //print_r($network_device_portstate);

  if ($pia_func_netdevport > 1)
    {
      for ($x=1; $x<=$pia_func_netdevport; $x++) 
        {
          if ($network_device_portstate[$x] == 1) {$port_state = '<div class="badge bg-green text-white" style="width: 60px;">Up</div>';} else {$port_state = '<div class="badge bg-red text-white" style="width: 60px;">Down</div>';}
          echo '<tr>
                  <td>'.$x.'</td>
                  <td>'.$port_state.'</td>
                  <td><a href="./deviceDetails.php?mac='.$network_device_portmac[$x].'">'.$network_device_portname[$x].'</td>
                  <td>'.$network_device_portip[$x].'</a></td>
                </tr>';
        }
    }
  echo '              </tbody></table>
            </div>';
	echo '</div> ';
}
$sql = 'SELECT "device_id", "net_device_name", "net_device_typ", "net_device_port" FROM "network_infrastructure"'; 
$result = $db->query($sql);//->fetchArray(SQLITE3_ASSOC); 
?>

<div class="nav-tabs-custom">
            <ul class="nav nav-tabs">

<?php
$i = 0;
while($res = $result->fetchArray(SQLITE3_ASSOC)){
	if(!isset($res['device_id'])) continue;
	if ($i == 0) {$active = 'active';} else {$active = '';}
    createnetworktab($res['device_id'], $res['net_device_name'], $res['net_device_typ'], $res['net_device_port'], $active);
    $i++;
}
?>              
            </ul>
			<div class="tab-content">



<?php
$i = 0;
while($res = $result->fetchArray(SQLITE3_ASSOC)){
	if(!isset($res['device_id'])) continue; 
	if ($i == 0) {$active = 'active';} else {$active = '';}
    createnetworktabcontent($res['device_id'], $res['net_device_name'], $res['net_device_typ'], $res['net_device_port'], $active);
    $i++;
}
unset($i);
?>
              <!-- /.tab-pane -->
            </div>
            <!-- /.tab-content -->
  </div>
</section>

    <!-- /.content -->
  </div>
  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>