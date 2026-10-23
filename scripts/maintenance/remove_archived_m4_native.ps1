# Storage maintenance only: never starts ANSYS or changes a simulation model.
# Run only for the researcher's 2026-10-23 archive-then-delete instruction.
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$evidenceDir = Join-Path $repoRoot 'results/m4/storage_cleanup_20261023'
$inventory = Get-Content -LiteralPath (Join-Path $evidenceDir 'native_deletion_inventory.json') -Raw | ConvertFrom-Json
$verification = Get-Content -LiteralPath (Join-Path $evidenceDir 'archive_verification.json') -Raw | ConvertFrom-Json
if ($verification.status -ne 'PASS_ALL_MEMBERS_READ_BACK_SHA256_AND_SIZE') { throw 'Archive verification did not pass.' }
$archivePath = (Resolve-Path -LiteralPath $verification.archive).Path
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $verification.archive_sha256) {
    throw 'Archive hash changed; refusing deletion.'
}
$allowedParent = (Resolve-Path -LiteralPath 'E:/ansys_runs').Path.TrimEnd('\')
$allowedNames = @('m4_case0_20261021', 'm4_viewer_20261022',
    'M4_Case0_reproduction_prepared_20261021', 'M4_D_reproduction_prepared_20261021', 'm4_native_benchmark')
$resolvedRoots = @()
foreach ($candidate in $inventory.roots) {
    $resolved = (Resolve-Path -LiteralPath $candidate).Path.TrimEnd('\')
    if ([IO.Path]::GetDirectoryName($resolved) -ne $allowedParent -or
        [IO.Path]::GetFileName($resolved) -notin $allowedNames) { throw "Outside approved cleanup scope: $resolved" }
    $rootItem = Get-Item -LiteralPath $resolved
    $children = @(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
    if (($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        @($children | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) {
        throw "Unexpected junction or link: $resolved"
    }
    $actualFiles = @($children | Where-Object { -not $_.PSIsContainer })
    $expected = @($inventory.files | Where-Object { $_.root -eq $candidate })
    if ($actualFiles.Count -ne $expected.Count) { throw "Native inventory changed: $resolved" }
    foreach ($row in $expected) {
        $file = Get-Item -LiteralPath $row.path
        if ($file.Length -ne $row.bytes) { throw "Native file changed: $($row.path)" }
    }
    $resolvedRoots += $resolved
}
if ($resolvedRoots.Count -ne 5) { throw 'Expected exactly five project-specific roots.' }
$active = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(ANSYS241|MAPDL241|AnsysWBU|RunWB2)\.exe$'
})
if ($active.Count) { throw 'ANSYS application is active; close the project before cleanup.' }
$tagsBefore = (& git -C $repoRoot show-ref --tags) -join "`n"
$freeBefore = (Get-PSDrive E).Free
$removed = @()
$failure = $null
try {
    foreach ($target in $resolvedRoots) {
        # Each absolute target was resolved, checked against exact allowed names,
        # and checked for reparse points above. Never delete the shared parent.
        Remove-Item -LiteralPath $target -Recurse -Force
        if (Test-Path -LiteralPath $target) { throw "Root still exists: $target" }
        $removed += $target
    }
} catch {
    $failure = $_.Exception.Message
} finally {
    $freeAfter = (Get-PSDrive E).Free
    $tagsAfter = (& git -C $repoRoot show-ref --tags) -join "`n"
    $receipt = [ordered]@{
        status = $(if ($failure) { 'PARTIAL_CLEANUP_FAILURE' } else { 'COMPLETED' })
        completed_at = (Get-Date).ToString('o')
        authorization = 'Researcher request on 2026-10-23: preserve core results, then delete current ANSYS model files'
        archive = $archivePath
        archive_sha256 = $verification.archive_sha256
        removed_roots = $removed
        removed_file_count = $(if (-not $failure) { $inventory.file_count } else { $null })
        removed_logical_bytes = $(if (-not $failure) { $inventory.logical_bytes } else { $null })
        drive_free_bytes_before_deletion = $freeBefore
        drive_free_bytes_after_deletion = $freeAfter
        drive_free_bytes_increase = $freeAfter - $freeBefore
        drive_measurement_note = 'Volume free-space delta; logical size differs because of compression, hard links and other activity'
        tags_unchanged = ($tagsBefore -eq $tagsAfter)
        no_simulation_executed = $true
        preserved = @('All tracked source/config/CAD/data/results/reports', 'M0-M3 tags and Git history',
            '29 native contour captures and Word/PDF explanations', 'Compressed exact native inputs',
            'ANSYS installation, license service, Python/CAD runtimes', 'Unrelated f510s_d280_20260928 project')
        limitation = 'Native full fields and Workbench models removed. Arbitrary-time 3D result browsing requires recomputation.'
        error = $failure
    }
    $json = $receipt | ConvertTo-Json -Depth 5
    $json | Set-Content -LiteralPath (Join-Path $evidenceDir 'deletion_receipt.json') -Encoding utf8
    $json | Set-Content -LiteralPath ($archivePath + '.cleanup_receipt.json') -Encoding utf8
    $json
}
if ($failure) { throw $failure }
if ($tagsBefore -ne $tagsAfter) { throw 'Stage tag references changed unexpectedly.' }
