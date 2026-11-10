# One persistent application stack, port 8080. No ETL, reset or model regeneration.
$ErrorActionPreference = 'Stop'
$mainRoot = Split-Path -Parent $PSScriptRoot
Push-Location $mainRoot
try {
    & docker compose -p tension-dashboard -f compose.yaml up --build -d --wait db backend frontend
    if ($LASTEXITCODE -ne 0) { throw 'Main stack build/start failed; inspect Docker logs.' }
    $mainMeta = Invoke-RestMethod 'http://127.0.0.1:8080/api/meta'
    if ($mainMeta.warehouse_empty) {
        Write-Output 'Main stack ready but empty. Data loading requires a separate validated, authorized procedure.'
    } elseif ($mainMeta.source_kind -eq 'synthetic') {
        $mainModel = Invoke-RestMethod 'http://127.0.0.1:8080/api/model/baseline'
        if (-not $mainModel.available -or $mainModel.warehouse_batch_match -ne $true) {
            throw 'Application is running, but model/batch verification is incomplete. Do not auto-import or edit hashes.'
        }
        Write-Output "Verified synthetic warehouse: $($mainMeta.participants) profiles / $($mainMeta.daily_records) daily / $($mainMeta.session_records) sessions."
    } else {
        Write-Output 'Actual/restricted source: keep data access restrictions; do not replace with simulation.'
    }
    Write-Output 'Main application: http://127.0.0.1:8080 | API docs: http://127.0.0.1:8080/api/docs'
} finally { Pop-Location }
