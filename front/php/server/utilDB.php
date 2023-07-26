<!-- utils needing a DB connection -->

<?php

require dirname(__FILE__).'/init.php';

// Action functions
if (isset ($_REQUEST['key']))
{
  echo lang($_REQUEST['key']);
}

?>