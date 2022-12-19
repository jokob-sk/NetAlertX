<?php
session_start();

if ($_SESSION["login"] != 1)
{
    header('Location: index.php');
    exit;
}

require 'php/templates/header.php';

foreach (glob("../db/setting_language*") as $filename) {
    $pia_lang_selected = str_replace('setting_language_','',basename($filename));
}

if (strlen($pia_lang_selected) == 0) {$pia_lang_selected = 'en_us';}

//------------------------------------------------------------------------------
// External files
require 'php/server/db.php';
require 'php/server/util.php';
require 'php/templates/language/'.$pia_lang_selected.'.php';

//------------------------------------------------------------------------------
//  Action selector
//------------------------------------------------------------------------------
// Set maximum execution time to 15 seconds
ini_set ('max_execution_time','30');

// Open DB
OpenDB('../db/pialert.db');

global $db;
global $pia_lang;

$result = $db->query("SELECT * FROM Settings");  

// array 
$settings = array();
while ($row = $result -> fetchArray (SQLITE3_ASSOC)) {   
  // Push row data      
  $settings[] = array( 'Index'        => $row['Index'], 
                        'Code_Name'    => $row['Code_Name'],
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
         <?php echo $pia_lang['Navigation_Settings'];?>
      </h1>
    </section>

   <?php

      $resultHTML = "";
      $groups = [];

      // collect all groups
      foreach ($settings as $row) { 
        if( in_array($row['Group'] , $groups) == false) {
          array_push($groups ,$row['Group']);
        }
      }

      // create settings groups
      foreach ($groups as $group) { 
        $resultHTML = $resultHTML.'<section class="settings_content">
          <h4>'.$group.'</h4>';
          
          // populate settings for each group
          foreach ($settings as $setting) { 
            if($setting["Group"] == $group)
            {
              $resultHTML = $resultHTML.
              '<div class="table_row" >
                <div class="table_cell setting_name" >';

              $resultHTML = $resultHTML.getString ($setting['Code_Name'].'_name', $setting['Display_Name'], $pia_lang);

              $resultHTML = $resultHTML.
              '</div>       
               <div class="table_cell setting_description" >';

              $resultHTML = $resultHTML.getString ($setting['Code_Name'].'_description', $setting['Description'], $pia_lang);

              $resultHTML = $resultHTML.
                '</div>       
              <div class="table_cell setting_input" >';

              // render different input types based on the setting type
              $inputType = "";
              // text - textbox
              if($setting['Type'] == 'text') 
              {
                $inputType = '<input  value="'.$setting['Value'].'"/>';                
              } 
              // password - hidden text
              elseif ($setting['Type'] == 'password')
              {
                $inputType = '<input  type="password" value="'.$setting['Value'].'"/>';
              }
              // boolean - checkbox
              elseif ($setting['Type'] == 'boolean')
              {
                $checked = "";
                if ($setting['Value'] == "True") { $checked = "checked";};
                $inputType = '<input  type="checkbox" value="'.$setting['Value'].'" '.$checked.' />';                
              }
              // integer - number input
              elseif ($setting['Type'] == 'integer')
              {
                $inputType = '<input  type="number" value="'.$setting['Value'].'"/>';                
              }
              // select - dropdown
              elseif ($setting['Type'] == 'select')
              {
                $inputType = '<select name="'.$setting['Code_Name'].'" id="'.$setting['Code_Name'].'">';                 
                $options = createArray($setting['Options']);
                foreach ($options as $option) {                   
                  $inputType = $inputType.'<option value="'.$option.'">'.$option.'</option>';

                }                
                $inputType = $inputType.'</select>';
              }
              // multiselect
              elseif ($setting['Type'] == 'multiselect')
              {
                $inputType = '<select name="'.$setting['Code_Name'].'" id="'.$setting['Code_Name'].'" multiple>';                 
                $values = createArray($setting['Value']);
                $options = createArray($setting['Options']);

                foreach ($options as $option) {                     
                  $selected = "";

                  if( in_array( $option , $values) == true) {
                    $selected = "selected";
                  }

                  $inputType = $inputType.'<option value="'.$option.'" '.$selected.'>'.$option.'</option>';
                }                
                $inputType = $inputType.'</select>';
              }              

              $resultHTML = $resultHTML.$inputType;

              $resultHTML = $resultHTML.'</div>  
              </div>';
            }
          }

        $resultHTML = $resultHTML.'</section>';
      }

      echo $resultHTML;
   ?>
   
    <!-- /.content -->
    <div class="table_row" >
          <button type="button" class="btn btn-default pa-btn bg-green dbtools-button" id="save" onclick="alert('Not yet implemented.')"><?php echo $pia_lang['DevDetail_button_Save'];?></button>
      </div>
</div>


  <!-- /.content-wrapper -->

<!-- ----------------------------------------------------------------------- -->
<?php
  require 'php/templates/footer.php';
?>
