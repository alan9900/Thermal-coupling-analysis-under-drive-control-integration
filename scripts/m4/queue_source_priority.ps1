$ErrorActionPreference='Stop'
$sourceRoot='E:/ansys_runs/m4_case0_20261021'
$sourceLog=Join-Path $sourceRoot 'studies/C_normal12_rd95_contact_low/study.out'
do {
    $sourceComplete=(Get-Content -LiteralPath $sourceLog -Tail 60 | Out-String) -match 'RUN COMPLETED'
    if(-not $sourceComplete){Start-Sleep -Seconds 10}
} while(-not $sourceComplete)
& (Join-Path $sourceRoot 'run_native_studies.ps1') -Cases @('D_normal12_rd95_dt1','A_normal12_rd95_dt1','C_normal12_rd95_contact_high','C_normal12_rd95_cooling_low','C_normal12_rd95_cooling_high') -Cores 4
