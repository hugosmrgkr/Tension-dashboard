# Explicit isolated demo only. Never uses the active compose.yaml or its volume.
$ErrorActionPreference = 'Stop'
$cp3Root = Split-Path -Parent $PSScriptRoot
Push-Location $cp3Root
try {
    $cp3Args = @('compose','-f','compose.cp3-demo.yaml','-p','toba-cp3-demo')
    & docker @cp3Args up --build -d db backend frontend
    if ($LASTEXITCODE -ne 0) { throw 'Demo stack build/start failed' }
    $cp3Meta = Invoke-RestMethod 'http://127.0.0.1:8001/api/meta'
    if ($cp3Meta.warehouse_empty) {
        & docker @cp3Args run --rm etl python -m etl.import_data --synthetic --dry-run --summary
        if ($LASTEXITCODE -ne 0) { throw 'Synthetic dry-run failed' }
        # This command can only reach db in the separate demo network above.
        & docker @cp3Args run --rm etl python -m etl.import_data --synthetic --commit --summary
        if ($LASTEXITCODE -ne 0) { throw 'Initial isolated demo load failed' }
    } else {
        Write-Output 'Demo DB already occupied; preserving data without another ETL commit.'
    }
    & docker @cp3Args run --rm etl python -m etl.verify_warehouse
    if ($LASTEXITCODE -ne 0) { throw 'Demo warehouse verification failed' }
    $cp3Model = Invoke-RestMethod 'http://127.0.0.1:8001/api/model/baseline'
    if (-not $cp3Model.available -or -not $cp3Model.warehouse_batch_match) {
        throw 'Verified artifacts missing or demo source does not match. Run offline baseline verification first.'
    }
    Write-Output 'CP3 SYNTHETIC demo ready: http://127.0.0.1:8081 | API: http://127.0.0.1:8001/api/docs'
    Write-Output 'Demo PostgreSQL is temporary RAM storage. Stopping/recreating its db loses ONLY demo data. Active service/volume untouched.'
} finally { Pop-Location }
