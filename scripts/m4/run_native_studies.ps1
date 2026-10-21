param([string[]]$Cases = @('A_internal_only_dt1','C_combined_dt1','D_preheat_braking_dt1'), [ValidateSet(2,4)][int]$Cores=2)
$ErrorActionPreference='Stop'
$run='E:/ansys_runs/m4_case0_20261021/studies'
$solver='E:/Program Files/ANSYS Inc/v241/ANSYS/bin/winx64/ANSYS241.exe'
foreach($case in $Cases) {
    if($case -notmatch '^[A-Za-z0-9_]+$'){throw 'Invalid case name'}
    $folder=Join-Path $run $case
    if(-not (Test-Path -LiteralPath (Join-Path $folder 'study.dat'))){throw 'Missing generated input'}
    if(Test-Path -LiteralPath (Join-Path $folder 'study.out')){throw "Existing native log must be preserved; use a new retry folder: $case"}
    $meta=Get-Content -LiteralPath (Join-Path $folder 'study_settings.json') -Encoding UTF8 -Raw | ConvertFrom-Json
    if($meta.viewfactor_reuse_from){
        $source=$meta.viewfactor_reuse_from
        $sourceLog=Get-Content -LiteralPath (Join-Path $source 'study.out') -Raw
        if($sourceLog -notmatch 'RUN COMPLETED' -or $sourceLog -notmatch 'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0'){throw 'View-factor source is incomplete'}
        $vf=Get-Item -LiteralPath (Join-Path $source 'study.vf')
        if($vf.Length -lt 100){throw 'Invalid native view-factor file'}
        $vfStream=[System.IO.File]::OpenRead($vf.FullName)
        try { $vfDigest=[BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($vfStream)).Replace('-','').ToLower() } finally { $vfStream.Dispose() }
        $meta | Add-Member -NotePropertyName viewfactor_sha256 -NotePropertyValue $vfDigest -Force
        [System.IO.File]::WriteAllText((Join-Path $folder 'study_settings.json'), ($meta | ConvertTo-Json -Depth 20), (New-Object System.Text.UTF8Encoding($false)))
    }
    $proc=Start-Process -FilePath $solver -ArgumentList @('-b','-smp','-np',"$Cores",'-p','ansys','-j','study','-dir',('"'+$folder+'"'),'-i',('"'+(Join-Path $folder 'study.dat')+'"'),'-o',('"'+(Join-Path $folder 'study.out')+'"')) -WindowStyle Hidden -Wait -PassThru
    # Launcher may return before its native child; require the terminal log.
    $deadline=(Get-Date).AddHours(2)
    do {
        $log=Join-Path $folder 'study.out'
        $tail=if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 60 | Out-String}else{''}
        if($tail -match 'RUN COMPLETED'){break}
        if($tail -match 'FATAL ERROR|license manager error|ANSYS LICENSE MANAGER ERROR'){throw "Native failure: $case"}
        if((Get-Date) -gt $deadline){throw "Study timeout: $case"}
        Start-Sleep -Seconds 5
    } while($true)
    $all=Get-Content -LiteralPath $log -Raw
    if($all -notmatch 'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0'){throw "Native solver errors: $case"}
    Write-Output "Native computation completed: $case (numerical/physical validation remains separate)"
}
