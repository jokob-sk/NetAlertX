<?php
require dirname(__FILE__).'/../server/init.php';

// 🔺----- API ENDPOINTS SUPERSEDED -----🔺
// check server/api_server/api_server_start.py for equivalents
// equivalent: /nettools
// 🔺----- API ENDPOINTS SUPERSEDED -----🔺

//------------------------------------------------------------------------------
// check if authenticated
require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';

// Prefer explicit binary paths, fall back to a sanitised PATH
$speedtestCandidates = [
    '/opt/venv/bin/speedtest-cli',
    '/usr/local/bin/speedtest-cli',
    '/usr/bin/speedtest-cli',
];

$candidateDirs = array_unique(array_map('dirname', $speedtestCandidates));
$safePath = implode(':', $candidateDirs);

$resolvedCommand = null;
foreach ($speedtestCandidates as $candidate) {
    if (is_executable($candidate)) {
        $resolvedCommand = escapeshellcmd($candidate) . ' --secure --simple';
        break;
    }
}

$output = [];
$returnCode = 0;

if ($resolvedCommand === null) {
    $resolvedCommand = 'env PATH=' . escapeshellarg($safePath) . ' speedtest-cli --secure --simple';
}

exec($resolvedCommand, $output, $returnCode);

echo '<h4>' . lang('Speedtest_Results') . '</h4>';

if ($returnCode !== 0 || empty($output)) {
    $errorMessage = $returnCode === 127
        ? 'speedtest-cli command not found. Checked paths: ' . $safePath
        : (empty($output) ? 'speedtest-cli returned no output.' : implode("\n", $output));

    echo '<div class="alert alert-danger">' . htmlspecialchars('Speedtest failed: ' . $errorMessage, ENT_QUOTES, 'UTF-8') . '</div>';
    return;
}

echo '<pre style="border: none;">';
foreach ($output as $line) {
    echo htmlspecialchars($line, ENT_QUOTES, 'UTF-8') . "\n";
}
echo '</pre>';
?>
