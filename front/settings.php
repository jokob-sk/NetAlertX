<?php

require 'php/templates/header.php';

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
// Set maximum execution time to 15 seconds
ini_set ('max_execution_time','30');

// check permissions
$dbPath = "../db/pialert.db";
$confPath = "../config/pialert.conf";

checkPermissions([$dbPath, $confPath]);

// get settings from the API json file

// path to your JSON file
$file = '../front/api/table_settings.json'; 
// put the content of the file in a variable
$data = file_get_contents($file); 
// JSON decode
$settingsJson = json_decode($data); 

// get settings from the DB

global $db;
global $settingKeyOfLists;

$result = $db->query("SELECT * FROM Settings");  

// array 
$settingKeyOfLists = array();
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
                        'Group'        => $row['Group'],
                        'Events'       => $row['Events']
                      ); 
}


?>
<!-- Page ------------------------------------------------------------------ -->
<div id="settingsPage" class="content-wrapper">

<!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
    <?php require 'php/templates/notification.php'; ?>
      <h1 id="pageTitle">
          <?= lang('Navigation_Settings');?> 
          <a style="cursor:pointer">
            <span>
              <i id='toggleSettings' onclick="toggleAllSettings()" class="settings-expand-icon fa fa-angle-double-down"></i>
            </span> 
          </a>
      </h1>
      <div class="settingsImported"><?= lang("settings_imported");?> <span id="lastImportedTime"></span></div>      
    </section>
    <div class="content " id='accordion_gen'>
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
      $isIn = ' in ';
      foreach ($groups as $group) 
      { 
        $html = $html.'<div  class=" box panel panel-default">
                          <a data-toggle="collapse" data-parent="#accordion_gen" href="#'.$group.'">
                            <div class="panel-heading">                              
                                <h4 class="panel-title">'.lang($group.'_icon')." ".lang($group.'_display_name').'</h4>                              
                            </div>
                          </a>
                          <div id="'.$group.'" data-myid="collapsible" class="panel-collapse collapse '.$isIn.'"> 
                            <div class="panel-body">';
        $isIn = ' '; // open the first panel only by default on page load

        // populate settings for each group 
        foreach ($settings as $set) 
        { 
          if($set["Group"] == $group)
          {
            $html = $html.
            '<div  class=" row table_row" > 
              <div class="table_cell setting_name bold" ><label>';

            $html = $html.getString ($set['Code_Name'].'_name', $set['Display_Name']).'</label>';

            $html = $html.'<div class="small" ><code>'.$set['Code_Name'].'</code></div>';

            $html = $html.
            '</div>       
              <div class="table_cell setting_description" >';               

            $html = $html.getString ($set['Code_Name'].'_description', $set['Description']);

            $html = $html.
              '</div>       
            <div class="table_cell setting_input input-group" >';

            // render different input types based on the settings type
            $input = "";

            // text - textbox
            if($set['Type'] == 'text' ) 
            {
              $input = '<input class="form-control" onChange="settingsChanged()" id="'.$set['Code_Name'].'" value="'.$set['Value'].'"/>';                
            } 
            // password - hidden text
            elseif ($set['Type'] == 'password')
            {
              $input = '<input onChange="settingsChanged()" class="form-control input" id="'.$set['Code_Name'].'" type="password" value="'.$set['Value'].'"/>';
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
              $input = '<input onChange="settingsChanged()" class="checkbox" id="'.$set['Code_Name'].'" type="checkbox" value="'.$set['Value'].'" '.$checked.' />';              
              
            }
            // integer - number input
            elseif ($set['Type'] == 'integer')
            {
              $input = '<input onChange="settingsChanged()" class="form-control" id="'.$set['Code_Name'].'" type="number" value="'.$set['Value'].'"/>';                
            }
            // selecttext - dropdown
            elseif ($set['Type'] == 'selecttext')
            {
              $input = '<select onChange="settingsChanged()" class="form-control" name="'.$set['Code_Name'].'" id="'.$set['Code_Name'].'">';                 
              
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
              $input = '<select onChange="settingsChanged()" class="form-control" name="'.$set['Code_Name'].'" id="'.$set['Code_Name'].'">';                 

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
              $input = '<select onChange="settingsChanged()" class="form-control" name="'.$set['Code_Name'].'" id="'.$set['Code_Name'].'" multiple>';  

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
            //  subnets
            elseif ($set['Type'] == 'subnets')
            {
              $input = $input.
              '<div class="row form-group">
                <div class="col-xs-6">
                  <input class="form-control" id="ipMask" type="text" placeholder="192.168.1.0/24"/>
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
            //  list
            elseif ($set['Type'] == 'list')
            {

              $settingKeyOfLists[] = $set['Code_Name'];

              $input = $input.
              '<div class="row form-group">
                <div class="col-xs-9">
                  <input class="form-control" type="text" id="'.$set['Code_Name'].'_input" placeholder="Enter value"/>
                </div>';
              // Add interface button
              $input = $input.
                '<div class="col-xs-3"><button class="btn btn-primary" onclick="addList'.$set['Code_Name'].'()" >Add</button></div>
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
              $input = $input.'<div><button class="btn btn-primary" onclick="removeFromList'.$set['Code_Name'].'()">Remove last</button></div>';
              
            }               

            $html = $html.$input;

            // render any buttons or additional actions if specified            
            $eventsHtml = "";
            // if available get all the events associated with this setting 
            $eventsList = createArray($set['Events']);  

            // icon map for the events
            // $iconMap = [
            //   "test"  => [lang("settings_event_tooltip"),""]
            // ];

            if(count($eventsList) > 0)
            {
              foreach ($eventsList as $event) {
                $eventsHtml = $eventsHtml.'<span class="input-group-addon pointer"
                  data-myparam="'.$set['Code_Name'].'" 
                  data-myevent="'.$event.'"
                >
                  <i title="'.lang($event."_event_tooltip").'" class="fa '.lang($event."_event_icon").' " >                 
                  </i>
                </span>';
              }
            }

            $html = $html.$eventsHtml.'</div>  
            </div>';
          }
        }

        $html = $html.'</div></div></div>';
      }

      echo $html;
   ?>
   </div>
   
    <!-- /.content -->
    <div class="row" >
          <div class="row">
            <button type="button" class="center top-margin  btn btn-primary btn-default pa-btn bg-green dbtools-button" id="save" onclick="saveSettings()"><?= lang('DevDetail_button_Save');?></button>
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

  // display the name of the first person
  // echo $settingsJson[0]->name;
  var settingsNumber = <?php echo count($settingsJson->data)?>;

  // Wrong number of settings processing
  if(<?php echo count($settings)?> != settingsNumber) 
  {
    showModalOk('WARNING', "<?= lang("settings_missing")?>");    
  }

  <?php
    // generate javascript methods to handle add and remove items to lists
    foreach($settingKeyOfLists as $settingKey )
    {
      $addList = 'function addList'.$settingKey.'()
      {
        input = $("#'.$settingKey.'_input").val();
        $("#'.$settingKey.'").append($("<option disabled></option>").attr("value", input).text(input));

        
        $("#'.$settingKey.'_input").val("");
  
        settingsChanged();
      }
      ';      


      $remList = 'function removeFromList'.$settingKey.'()
      {
        settingsChanged();
        // $("#'.$settingKey.'").empty();
        $("#'.$settingKey.'").find("option:last").remove();
      }';

      echo $remList;
      echo $addList;
    }
  ?>
  
  // ---------------------------------------------------------
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

      settingsChanged();
    }
  }

  // ---------------------------------------------------------
  function removeInterfaces()
  {
    settingsChanged();
    $('#SCAN_SUBNETS').empty();
  }

  // ---------------------------------------------------------
  function collectSettings()
  {
    var settingsArray = [];

    // generate javascript to collect values    
    <?php 

    $noConversion = array('text', 'integer', 'password', 'readonly', 'selecttext', 'selectinteger', 'multiselect'); 

    foreach ($settings as $set) { 
      if(in_array($set['Type'] , $noConversion))
      {         
        
        echo 'settingsArray.push(["'.$set["Group"].'", "'.$set["Code_Name"].'", "'.$set["Type"].'", $("#'.$set["Code_Name"].'").val() ]);';
      } 
      elseif ($set['Type'] == "boolean")
      {
        echo 'temp = $("#'.$set["Code_Name"].'").is(":checked") ;';
        echo 'settingsArray.push(["'.$set["Group"].'", "'.$set["Code_Name"].'", "'.$set["Type"].'", temp ]);';  
      }
      elseif ($set["Code_Name"] == "SCAN_SUBNETS")
      {        
        echo "var temps = [];

        $( '#SCAN_SUBNETS option' ).each( function( i, selected ) {
          temps.push($( selected ).val());
        });       
        
        ";
        echo 'settingsArray.push(["'.$set["Group"].'", "'.$set["Code_Name"].'", "'.$set["Type"].'", temps ]);';
      }
      elseif ($set['Type'] == "list")
      { 
        echo 'console.log($("#'.$set["Code_Name"].'"));';       
        echo "var temps = [];
        
        $( '#".$set["Code_Name"]." option' ).each( function( i, selected ) {
          vl = $( selected ).val()
          if (vl != '')
          {
            temps.push(vl);
          }
        });       
        console.log(temps);
        ";
        echo 'settingsArray.push(["'.$set["Group"].'", "'.$set["Code_Name"].'", "'.$set["Type"].'", temps ]);';
      }
    }
    
    ?>
    console.log(settingsArray);
    return settingsArray;
  }  

  // ---------------------------------------------------------
  function saveSettings() {
    if(<?php echo count($settings)?> != settingsNumber) 
    {
      showModalOk('WARNING', "<?= lang("settings_missing_block")?>");    
    } else
    {
      $.ajax({
      method: "POST",
      url: "../php/server/util.php",
      data: { function: 'savesettings', settings: collectSettings() },
      success: function(data, textStatus) {                    
          showModalOk ('Result', data );
          // Remove navigation prompt "Are you sure you want to leave..."
          window.onbeforeunload = null;
        }
      });
    }
  }

  // ---------------------------------------------------------  
  function getParam(targetId, key, skipCache = false) {  

    skipCacheQuery = "";

    if(skipCache)
    {
      skipCacheQuery = "&skipcache";
    }

    // get parameter value
    $.get('php/server/parameters.php?action=get&defaultValue=0&parameter='+ key + skipCacheQuery, function(data) {

      var result = data;   
      
      if(key == "Back_Settings_Imported")
      {
        fileModificationTime = <?php echo filemtime($confPath)*1000;?>;        
        importedMiliseconds = parseInt(result.match(  /\d+/g ).join('')); // sanitize the string and get only the numbers
        
        result = (new Date(importedMiliseconds)).toLocaleString("en-UK", { timeZone: "<?php echo $timeZone?>" }); //.toDateString("");

        // check if displayed settings are outdated
        if(fileModificationTime > importedMiliseconds)
        {
          showModalOk('WARNING: Outdated settings displayed', "<?= lang("settings_old")?>");
        }
      } else{
        result = result.replaceAll('"', '');
      }

      document.getElementById(targetId).innerHTML = result.replaceAll('"', ''); 
    });
  }
  
  
  // -----------------------------------------------------------------------------
  function toggleAllSettings()
  {
    inStr = ' in';
    allOpen = true;
    openIcon = 'fa-angle-double-down';
    closeIcon = 'fa-angle-double-up';    

    $('.panel-collapse').each(function(){
      if($(this).attr('class').indexOf(inStr) == -1)
      {
        allOpen = false;
      }
    })
    
    if(allOpen)
    {
      // close all
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('class', 'panel-collapse collapse  ')})      
      $('#toggleSettings').attr('class', $('#toggleSettings').attr('class').replace(closeIcon, openIcon))
    }
    else{
      // open all
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('class', 'panel-collapse collapse in')})
      $('div[data-myid="collapsible"]').each(function(){$(this).attr('style', 'height:inherit')})
      $('#toggleSettings').attr('class', $('#toggleSettings').attr('class').replace(openIcon, closeIcon))
    }
    
  }

</script>

<script defer>

  // ----------------------------------------------------------------------------- 
  // handling events on the backend initiated by the front end START
  // ----------------------------------------------------------------------------- 
  $(window).on('load', function() { 
    $('span[data-myevent]').each(function(index, element){
      $(element).attr('onclick', 
      'handleEvent(\"' + $(element).attr('data-myevent') + '|'+ $(element).attr('data-myparam') + '\")'      
      );
    });
  });

  modalEventStatusId = 'modal-message-front-event'

  function handleEvent (value){
    setParameter ('Front_Event', value)

    // show message
    showModalOk("<?= lang("general_event_title")?>", "<?= lang("general_event_description")?> <code id='"+modalEventStatusId+"'></code>");

    // Periodically update state of the requested action
    getParam(modalEventStatusId,"Front_Event", true, updateModalState)

    updateModalState()
  }


  function updateModalState(){

    setTimeout(function(){
      displayedEvent = $('#'+modalEventStatusId).html()

      // loop until finished  
      if(displayedEvent.indexOf('finished') == -1) // if the message is different from finished, check again in 4s
      {
        
        getParam(modalEventStatusId,"Front_Event", true)

        updateModalState()
        
      }
    }, 2000);
  }


  // ----------------------------------------------------------------------------- 
  // handling events on the backend initiated by the front end END
  // ----------------------------------------------------------------------------- 

  // ---------------------------------------------------------
  // Show last time settings have been imported
  getParam("lastImportedTime", "Back_Settings_Imported", skipCache = true);

</script>
