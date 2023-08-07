<?php      
$filename = "/.VERSION";
if(file_exists($filename))
{
  echo file_get_contents($filename);
}
else{
  echo "File not found";
}               
?>
