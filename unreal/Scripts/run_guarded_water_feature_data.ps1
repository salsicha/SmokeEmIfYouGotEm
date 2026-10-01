param([Parameter(Mandatory=$true)][string]$CasePath,
      [ValidateSet('DATA', 'MESH', 'PARTICLES')][string]$Stage = 'DATA',
      [ValidatePattern('^([1-9][0-9]*)?$')][string]$Attempt = '',
      [switch]$CompleteOccupancyBoundary)
$ErrorActionPreference = 'Stop'
$workspacePath = 'C:\Users\salsi\repos\SmokeEmIfYouGotEm'
$caseDirectory = (Resolve-Path -LiteralPath $CasePath).Path
$labDirectory = Join-Path $workspacePath 'tmp\water-feature-lab'
if (-not $caseDirectory.StartsWith($labDirectory+'\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Case must be an explicitly prepared child of this workspace laboratory'
}
if ($CompleteOccupancyBoundary -and ($Stage -ne 'PARTICLES' -or
    $caseDirectory -ne (Join-Path $labDirectory 'eddy-v4-boundary-completed'))) {
    throw 'Occupancy completion is scoped to the fresh eddy-v4 PARTICLES stage'
}
if (@(Get-Process blender -ErrorAction SilentlyContinue).Count -gt 0) {
    throw 'A Blender process is already live; inspect it before starting another bake'
}
$blendPath = Join-Path $caseDirectory 'feature.blend'
$preflightName = switch ($Stage) { 'MESH' { 'alignment-data-audit.json' } 'PARTICLES' { 'secondary-preflight.json' } default { 'alignment-preflight.json' } }
$preflightPath = Join-Path $caseDirectory $preflightName
$preflight = Get-Content -LiteralPath $preflightPath -Raw | ConvertFrom-Json
if (-not $preflight.complete -or -not $preflight.original_unchanged) { throw 'Native alignment preflight required' }
$stageName = $Stage.ToLowerInvariant()
$attemptSuffix = if ($Attempt) { "-$Attempt" } else { '' }
$stdoutPath = Join-Path $caseDirectory "guarded-$stageName$attemptSuffix.stdout.txt"
$stderrPath = Join-Path $caseDirectory "guarded-$stageName$attemptSuffix.stderr.txt"
foreach ($target in @($stdoutPath, $stderrPath, (Join-Path $caseDirectory "bake-$stageName.json"),
                      (Join-Path $caseDirectory "bake-$stageName-in-progress.json"))) {
    if (Test-Path -LiteralPath $target) { throw "Existing evidence: $target. Refusing duplicate launch." }
}
$taskDrive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($caseDirectory))
if ($taskDrive.AvailableFreeSpace -lt 6GB) { throw 'Need 6 GiB free before the bounded stage bake' }
$scriptName = switch ($Stage) { 'MESH' { 'bake_aligned_eddy_mesh.py' } 'PARTICLES' { 'bake_aligned_eddy_particles.py' } default { 'bake_prepared_water_feature_data.py' } }
if ($CompleteOccupancyBoundary) { $scriptName = 'bake_eddy_boundary_completed_particles.py' }
$arguments = @('-b', ('"'+$blendPath+'"'), '--python-exit-code', '1', '--python',
               ('"'+(Join-Path $workspacePath "unreal\Scripts\$scriptName")+'"'))
$ownedProcess = Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' `
    -ArgumentList $arguments -WorkingDirectory $workspacePath -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
Write-Output ('OWNED_'+$Stage+'_BAKE_PID='+$ownedProcess.Id)
$ownedHandle = $ownedProcess.Handle
while (-not $ownedProcess.HasExited) {
    if ($taskDrive.AvailableFreeSpace -lt 1.5GB) {
        # Kill only the process object created by this invocation, never a scan.
        $ownedProcess.Kill()
        $ownedProcess.WaitForExit()
        throw 'Owned stage bake stopped at 1.5 GiB reserve; partial evidence preserved'
    }
    Start-Sleep -Seconds 2
    $ownedProcess.Refresh()
}
$ownedProcess.WaitForExit()
if ($null -eq $ownedProcess.ExitCode) { throw 'Native exit code unavailable; inspect owned job/receipt before proceeding' }
Write-Output ('OWNED_'+$Stage+'_BAKE_EXIT='+$ownedProcess.ExitCode)
Get-Content -LiteralPath $stdoutPath -Tail 12
if ($ownedProcess.ExitCode -ne 0) { Get-Content -LiteralPath $stderrPath -Tail 20; exit $ownedProcess.ExitCode }
