param([Parameter(Mandatory=$true)][string]$CaseDirectory)
$ErrorActionPreference = 'Stop'
$taskWorkspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskCase = (Resolve-Path -LiteralPath $CaseDirectory).Path
$taskAllowed = [IO.Path]::GetFullPath((Join-Path $taskWorkspace 'tmp/water-feature-lab')) + [IO.Path]::DirectorySeparatorChar
if (-not $taskCase.StartsWith($taskAllowed, [StringComparison]::OrdinalIgnoreCase)) { throw 'Case outside isolated-feature workspace' }
$taskBlend = Join-Path $taskCase 'feature.blend'
$taskScript = Join-Path $taskWorkspace 'unreal/Scripts/bake_prepared_water_feature_data.py'
$taskOut = Join-Path $taskCase 'data-bake-stdout.log'
$taskErr = Join-Path $taskCase 'data-bake-stderr.log'
if ((Test-Path -LiteralPath $taskOut) -or (Test-Path -LiteralPath $taskErr)) { throw 'Preserve existing run logs; inspect previous process first' }
$taskDrive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($taskCase))
if ($taskDrive.AvailableFreeSpace -lt 3GB) { throw 'Need 3 GiB before launching base-liquid bake' }
$taskArguments = @('-b', ('"' + $taskBlend + '"'), '-t', '4', '--python-exit-code', '1', '--python', ('"' + $taskScript + '"'))
$taskProcess = Start-Process -FilePath 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -ArgumentList $taskArguments -WorkingDirectory $taskWorkspace -WindowStyle Hidden -RedirectStandardOutput $taskOut -RedirectStandardError $taskErr -PassThru
Write-Output "Owned base-liquid bake PID: $($taskProcess.Id)"
while (-not $taskProcess.HasExited) {
    if ($taskDrive.AvailableFreeSpace -lt 1.5GB) {
        $taskProcess.Kill()
        $taskProcess.WaitForExit()
        throw 'Stopped this owned bake below 1.5 GiB reserve; preserve all partial cache and logs'
    }
    Start-Sleep -Seconds 2
    $taskProcess.Refresh()
}
$taskProcess.WaitForExit()
Get-Content -LiteralPath $taskOut -Tail 12
if ($taskProcess.ExitCode -ne 0) {
    Get-Content -LiteralPath $taskErr -Tail 12
    throw "Owned base-liquid bake failed: $($taskProcess.ExitCode)"
}
Write-Output 'Guarded base-liquid bake completed; secondary and mesh stages remain unbaked.'
