# Compatibility entrypoint: CP3 now uses the single persistent main stack.
$ErrorActionPreference = 'Stop'
Write-Output 'CP3 uses tension-dashboard on port 8080. No separate 8081 database is started.'
& (Join-Path $PSScriptRoot 'start_main.ps1')
