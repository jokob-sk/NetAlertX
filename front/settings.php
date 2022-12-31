<?php

require 'php/templates/header.php';


//------------------------------------------------------------------------------
// External files
require 'php/server/db.php';
require 'php/server/util.php';

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
// Set maximum execution time to 15 seconds
ini_set ('max_execution_time','30');

// check permissions
$dbPath = "../db/pialert.db";
$confPath = "../config/pialert.conf";

checkPermissions([$dbPath, $confPath]);

// Open DB
OpenDB($dbPath);

global $db;
global $pia_lang;

$result = $db->query("SELECT * FROM Settings");  

// array 
$settings = array();
while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {   
  // Push row data      
  $settings[] = array(  'Code_Name'    => $row['Code_Name'],
                        'Display_Name' => $row['Display_Name'],
                        'Description'  => $row['Description'],
                        'Type'         => $row['Type'],
                        'Options'      => $row['Options'],
                        'RegEx'        => $row['RegEx'],
                        'Value'        => $row['Value'],
                        'Group'        => $row['Group']
                      ); 
}

$db->close();

?>
<!-- Page ------------------------------------------------------------------ -->
<div class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
         <?php echo lang('Navigation_Settings');?>
      </h1>
    </section>
    <div class="content">
   <?php      

      $html = "";
      $groups = [];

      // collect all groups
      foreach ($settings as $row) { 
        if( in_array($row['Group'] , $groups) == false) {
          array_push($groups ,$row['Group']);
        }
      }

      // create settings groups
      foreach ($groups as $group) { 
        $html = $html.'<section class="content box">
          <h4>'.$group.'</h4>';
          
          // populate settings for each group
          foreach ($settings as $set) { 
            if($set["Group"] == $group)
            {
              $html = $html.
              '<div class=" row table_row" >
                <div class="table_cell setting_name bold" ><label>';

              $html = $html.getString ($set['Code_Name'].'_name', $set['Display_Name']).'</label>';

              $html = $html.'<div class="small" ><code>'.$set['Code_Name'].'</code></div>';

              $html = $html.
              '</div>       
               <div class="table_cell setting_description" >';               

              $html = $html.getString ($set['Code_Name'].'_description', $set['Description']);

              $html = $html.
                '</div>       
              <div class="table_cell setting_input" >';

              // render different input types based on the settings type
              $input = "";

              // text - textbox
              if($set['Type'] == 'text' ) 
              {
                $input = '<input class="form-control input" id="'.$set['Code_Name'].'" value="'.$set['Value'].'"/>';                
              } 
              // password - hidden text
              elseif ($set['Type'] == 'password')
              {
                $input = '<input class="form-control input" id="'.$set['Code_Name'].'" type="password" value="'.$set['Value'].'"/>';
              }
              // readonly 
              elseif ($set['Type'] == 'readonly')
              {
                $input = '<input class="form-control input" id="'.$set['Code_Name'].'"  value="'.$set['Value'].'" readonly/>';
              }
              // boolean - checkbox
              elseif ($set['Type'] == 'boolean')
              {
                $checked = "";
                if ($set['Value'] == "True") { $checked = "checked";};
                $input = '<input class="checkbox" id="'.$set['Code_Name'].'" type="checkbox" value="'.$set['Value'].'" '.$checked.' />';                
              }
              // integer - number input
              elseif ($set['Type'] == 'integer')
              {
                $input = '<input class="form-control" id="'.$set['Code_Name'].'" type="number" value="'.$set['Value'].'"/>';                
              }
              // selecttext - dropdown
              elseif ($set['Type'] == 'selecttext')
              {
                $input = '<select class="form-control" name="'.$set['Code_Name'].'" id="'.$set['Code_Name'].'">';                 
                
                $values = createArray($set['Value']);
                $options = createArray($set['Options']);

                foreach ($options as $option) {              
                  $selected = "";

                  if( in_array( $option , $values) == true) {
                    $selected = "selected";
                  }

                  $input = $input.'<option value="'.$option.'" '.$selected.'>'.$option.'</option>';
                }                
                $input = $input.'</select>';
              }
              // selectinteger - dropdown
              elseif ($set['Type'] == 'selectinteger')
              {
                $input = '<select class="form-control" name="'.$set['Code_Name'].'" id="'.$set['Code_Name'].'">';                 

                $values = createArray($set['Value']);
                $options = createArray($set['Options']);

                foreach ($options as $option) {   
                  
                  $selected = "";

                  if( in_array( $option , $values) == true) {
                    $selected = "selected";
                  }

                  $input = $input.'<option value="'.$option.'" '.$selected.'>'.$option.'</option>';
                }                
                $input = $input.'</select>';
              }
              // multiselect
              elseif ($set['Type'] == 'multiselect')
              {
                $input = '<select class="form-control" name="'.$set['Code_Name'].'" id="'.$set['Code_Name'].'" multiple>';  

                $values = createArray($set['Value']);
                $options = createArray($set['Options']);

                foreach ($options as $option) {                     
                  $selected = "";

                  if( in_array( $option , $values) == true) {
                    $selected = "selected";
                  }

                  $input = $input.'<option value="'.$option.'" '.$selected.'>'.$option.'</option>';
                }                
                $input = $input.'</select>';
              }
              // multiselect
              elseif ($set['Type'] == 'subnets')
              {
                $input = $input.
                '<div class="row form-group">
                  <div class="col-xs-6">
                    <input class="form-control " id="ipMask" type="text" placeholder="192.168.1.0/24"/>
                  </div>';
                // Add interface button
                $input = $input.
                  '<div class="col-xs-3">
                    <input class="form-control " id="ipInterface" type="text" placeholder="eth0" />
                  </div>
                  <div class="col-xs-3"><button class="btn btn-primary" onclick="addInterface()" >Add</button></div>
                 </div>';
                
                // list all interfaces as options
                $input = $input.'<div class="form-group">
                  <select class="form-control" name="'.$set['Code_Name'].'" id="'.$set['Code_Name'].'" multiple readonly>';
                  
                $options = createArray($set['Value']);                

                foreach ($options as $option) {                                       

                  $input = $input.'<option value="'.$option.'" disabled>'.$option.'</option>';
                }                
                $input = $input.'</select></div>';
                // Remove all interfaces button               
                $input = $input.'<div><button class="btn btn-primary" onclick="removeInterfaces()">Remove all</button></div>';
                
              }               

              $html = $html.$input;

              $html = $html.'</div>  
              </div>';
            }
          }

        $html = $html.'</section>';
      }

      echo $html;
   ?>
   </div>
   
    <!-- /.content -->
    <div class="row" >
          <div class="row">
            <button type="button" class="center top-margin  btn btn-primary btn-default pa-btn bg-green dbtools-button" id="save" onclick="saveSettings()"><?php echo lang('DevDetail_button_Save');?></button>
          </div>
          <div id="result"></div>
      </div>
</div>


  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';  
?>

<script>

  // number of settings has to be equal to
  var settingsNumber = 53;
  
  if(<?php echo count($settings)?> != settingsNumber) 
  {
    showModalOk('WARNING', '<?php echo lang("settings_missing")?>');    
  }

  function addInterface()
  {
    ipMask = $('#ipMask').val();
    ipInterface = $('#ipInterface').val();

    full = ipMask + " --interface=" + ipInterface;

    console.log(full)

    if(ipMask == "" || ipInterface == "")
    {
      showModalOk ('Validation error', 'Specify both, the network mask and the interface');
    } else {
      $('#SCAN_SUBNETS').append($('<option disabled></option>').attr('value', full).text(full));

      $('#ipMask').val('');
      $('#ipInterface').val('');
    }
  }

  function removeInterfaces()
  {
    $('#SCAN_SUBNETS').empty();
  }

  function collectSettings()
  {
    var settingsArray = [];

    // generate javascript to collect values    
    <?php 

    $noConversion = array('text', 'integer', 'password', 'readonly', 'selecttext', 'selectinteger', "multiselect"); 

    foreach ($settings as $set) { 
      if(in_array($set['Type'] , $noConversion))
      {         
        echo 'settingsArray.push(["'.$set["Group"].'", "'.$set["Code_Name"].'", $("#'.$set["Code_Name"].'").val(), "'.$set["Type"].'" ]);';      
      } 
      elseif ($set['Type'] == "boolean")
      {
        echo 'temp = $("#'.$set["Code_Name"].'").is(":checked") ;';
        echo 'settingsArray.push(["'.$set["Group"].'", "'.$set["Code_Name"].'", temp, "'.$set["Type"].'" ]);';  
      }
      elseif ($set["Code_Name"] == "SCAN_SUBNETS")
      {        
        echo "var temps = [];

        $( '#SCAN_SUBNETS option' ).each( function( i, selected ) {
          temps.push($( selected ).val());
        });       
        
        ";
        echo 'settingsArray.push(["'.$set["Group"].'", "'.$set["Code_Name"].'", temps, "'.$set["Type"].'" ]);';
      }
    }
    
    ?>
    console.log(settingsArray);
    return settingsArray;
  }  

  function saveSettings() {
    if(<?php echo count($settings)?> != settingsNumber) 
    {
      showModalOk('WARNING', '<?php echo lang("settings_missing")?>');    
    } else
    {
      $.ajax({
      method: "POST",
      url: "../php/server/util.php",
      data: { function: 'savesettings', settings: collectSettings() },
      success: function(data, textStatus) {
          // $("#result").html(data);    
          // console.log(data);
          showModalOk ('Result', data );
        }
      });
    }  
    
  }
</script>
