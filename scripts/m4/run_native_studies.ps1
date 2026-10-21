param([string[]]$Cases = @('A_internal_only_dt1','C_combined_dt1','D_preheat_braking_dt1'))
$ErrorActionPreference='Stop'
$run='E:/ansys_runs/m4_case0_20261021/studies'
$solver='E:/Program Files/ANSYS Inc/v241/ANSYS/bin/winx64/ANSYS241.exe'
foreach($case in $Cases) {
    if($case -notmatch '^[A-Za-z0-9_]+$'){throw 'Invalid case name'}
    $folder=Join-Path $run $case
    if(-not (Test-Path -LiteralPath (Join-Path $folder 'study.dat'))){throw 'Missing generated input'}
    $proc=Start-Process -FilePath $solver -ArgumentList @('-b','-smp','-np','2','-p','ansys','-j','study','-dir',('"'+$folder+'"'),'-i',('"'+(Join-Path $folder 'study.dat')+'"'),'-o',('"'+(Join-Path $folder 'study.out')+'"')) -WindowStyle Hidden -Wait -PassThru
    # Launcher may return before its native child; require the terminal log.
    $deadline=(Get-Date).AddHours(2)
    do {
        $log=Join-Path $folder 'study.out'
        $tail=if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Tail 60 | Out-String}else{''}
        if($tail -match 'RUN COMPLETED'){break}
        if((Get-Date) -gt $deadline){throw "Study timeout: $case"}
        Start-Sleep -Seconds 5
    } while($true)
    $all=Get-Content -LiteralPath $log -Raw
    if($all -notmatch 'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+0'){throw "Native solver errors: $case"}
    Write-Output "Native computation completed: $case (numerical/physical validation remains separate)"
}
