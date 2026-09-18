param(
    [Parameter(Mandatory=$true)][string]$Config,
    [Parameter(Mandatory=$true)][string]$CookManifest
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
function Get-ReviewLocalPath([string]$Name, [string]$Root) {
    $path = [IO.Path]::GetFullPath((Join-Path $Root $Name))
    $prefix = [IO.Path]::GetFullPath((Join-Path $Root 'tmp')) + [IO.Path]::DirectorySeparatorChar
    if (-not $path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Review input must be project-local tmp' }
    return $path
}
function Test-ReviewCookIdentity($Expected, $Actual) {
    $stamp = if ($Expected.start_utc -is [datetime]) { $Expected.start_utc.ToUniversalTime().ToString('o') } else { $Expected.start_utc }
    return ($Expected.pid -is [int] -or $Expected.pid -is [long]) -and $Expected.pid -gt 0 -and
        $Expected.pid -eq $Actual.pid -and $stamp -ceq $Actual.start_utc -and
        $Expected.executable -ieq $Actual.executable -and
        $Expected.sha256 -cmatch '^[a-f0-9]{64}$' -and $Expected.sha256 -ceq $Actual.sha256 -and
        -not [string]::IsNullOrEmpty($Expected.command_line) -and $Expected.command_line -ceq $Actual.command_line
}
function Test-ReviewPlayerCaptureLog([string]$LogText, [int]$Count) {
    if ($Count -lt 24 -or $Count -gt 120) { return $false }
    $rows=[regex]::Matches($LogText,'RaftSim PIE player-backbuffer capture: index=([0-9]+) saved=([01])')
    if ($rows.Count -ne $Count) { return $false }
    for ($i=0; $i -lt $Count; ++$i) {
        if ([int]$rows[$i].Groups[1].Value -ne $i -or $rows[$i].Groups[2].Value -cne '1') { return $false }
    }
    return $true
}
function Get-ReviewTerrainRayArguments($Config) {
    $hasPixels = $null -ne $Config.terrain_pixels
    $hasIndex = $null -ne $Config.terrain_capture_index
    if (-not $hasPixels -and -not $hasIndex) { return }
    if (-not $hasPixels -or -not $hasIndex) { throw 'Terrain pixels and capture index must be paired' }
    $count = if ($null -eq $Config.capture_count) { 24 } else { $Config.capture_count }
    if ($count -isnot [long] -and $count -isnot [int]) { throw 'Integer capture count required' }
    $index = $Config.terrain_capture_index
    if (($index -isnot [long] -and $index -isnot [int]) -or $index -lt 0 -or $index -ge $count -or $count -lt 24 -or $count -gt 120) { throw 'Terrain capture index outside series' }
    $pixels = @($Config.terrain_pixels)
    if ($pixels.Count -lt 1 -or $pixels.Count -gt 32) { throw 'One to 32 terrain pixels required' }
    $tokens = foreach ($pixel in $pixels) {
        if ($pixel -isnot [array] -or $pixel.Count -ne 2) { throw 'Pixel coordinate pair required' }
        foreach ($value in $pixel) {
            if ($value -isnot [long] -and $value -isnot [int]) { throw 'Integer pixel coordinate required' }
        }
        if ($pixel[0] -lt 0 -or $pixel[0] -ge 1280 -or $pixel[1] -lt 0 -or $pixel[1] -ge 720) { throw 'Pixel outside actual player viewport' }
        '{0},{1}' -f $pixel[0],$pixel[1]
    }
    "-RaftSimCaptureCarrierShapeIndex=$index"
    '-RaftSimCaptureTerrainPixels=' + ($tokens -join ';')
}
$configPath = Get-ReviewLocalPath $Config $projectRoot
$raw = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$terrainArguments = @(Get-ReviewTerrainRayArguments $raw)
if ($raw.label -notmatch '^south-fork-[a-z0-9-]+$') { throw 'Scoped fresh review label required' }
$descriptorPath = Get-ReviewLocalPath $raw.descriptor $projectRoot
$descriptor = Get-Content -LiteralPath $descriptorPath -Raw | ConvertFrom-Json
if ($descriptor.schema -ne 'raftsim.source_supported_paired_review.v1' -or
    $descriptor.production_promoted -cne $false -or $descriptor.candidate -cne $true) { throw 'Unaccepted paired descriptor required' }
$station = [double]$descriptor.review_start_station_m
if (-not [double]::IsFinite($station) -or $station -lt 0 -or $station -gt 33334) { throw 'Invalid station' }
$playReport = Get-ReviewLocalPath $raw.report $projectRoot
$reportFile = Get-ReviewLocalPath ('tmp/' + $raw.label + '-process.json') $projectRoot
$logFile = Get-ReviewLocalPath ('tmp/' + $raw.label + '.log') $projectRoot
foreach ($path in @($playReport,$reportFile,$logFile)) {
    if (Test-Path -LiteralPath $path) { throw 'Preserve previous review evidence' }
}
$manifest = Get-Content -LiteralPath (Get-ReviewLocalPath $CookManifest $projectRoot) -Raw | ConvertFrom-Json
if ($manifest.schema -ne 'raftsim.paired_review_cooks.v1' -or @($manifest.processes).Count -ne 2) { throw 'Both explicitly owned cooks required' }
$owned = @(); $seen = @($PID)
# Validate every identity before suspending anything, then retain handles for
# resume: a reused PID must never redirect cleanup to an unrelated process.
foreach ($identity in $manifest.processes) {
    if ($identity.pid -in $seen) { throw 'Duplicate or launcher process ID' }; $seen += $identity.pid
    $exe = Get-ReviewLocalPath $identity.executable $projectRoot
    if ([IO.Path]::GetFileName($exe) -ne 'raftsim_cartesian_cook.exe') { throw 'Expected local solver' }
    $process = [Diagnostics.Process]::GetProcessById($identity.pid)
    $command = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $identity.pid)
    $actual = [pscustomobject]@{ pid=$process.Id; start_utc=$process.StartTime.ToUniversalTime().ToString('o');
        executable=$process.MainModule.FileName; sha256=(Get-FileHash -LiteralPath $exe).Hash.ToLowerInvariant(); command_line=$command.CommandLine }
    $identity.executable = $exe
    if (-not (Test-ReviewCookIdentity $identity $actual)) { throw 'Live cook identity changed' }
    $owned += [pscustomobject]@{ process=$process; handle=$process.Handle; identity=$actual }
}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RaftSimPairedReviewProcessControl {
    [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr handle);
    [DllImport("ntdll.dll")] public static extern int NtResumeProcess(IntPtr handle);
}
'@
$paused=@(); $editor=$null
$result=[ordered]@{schema='raftsim.paired_review_process.v1'; processes=@(); editor_exit_code=$null; timeout=$false; performance_accepted=$false}
try {
    foreach ($item in $owned) {
        $entry=[ordered]@{identity=$item.identity; cpu_before=$item.process.TotalProcessorTime.TotalSeconds; suspend=$null; resume=$null}
        $result.processes += $entry
        $entry.suspend=[RaftSimPairedReviewProcessControl]::NtSuspendProcess($item.handle)
        if ($entry.suspend -ne 0) { throw 'Cook suspension failed' }
        $paused += @{item=$item; entry=$entry}
    }
    $start=[Diagnostics.ProcessStartInfo]::new()
    $start.FileName='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
    $start.UseShellExecute=$false; $start.CreateNoWindow=$true; $start.WorkingDirectory=$projectRoot
    $start.Environment['RAFTSIM_CONSTRICTION_PLAY_CONFIG']=$configPath
    $stationText=$station.ToString('R',[cultureinfo]::InvariantCulture)
    foreach ($argument in @((Join-Path $projectRoot 'unreal/SmokeEmIfYouGotEm.uproject'), '/Engine/Maps/Entry',
        '-d3d12','-RenderOffscreen','-Unattended','-NoSplash','-NoSound','-ResX=1280','-ResY=720','-Windowed','-ForceRes',
        '-RaftSimEphemeralProfile','-RaftSimScenario=south_fork_full_descent',"-RaftSimWaterReviewStation=$stationText",
        "-abslog=$logFile",('-ExecCmds=py ' + (Join-Path $PSScriptRoot 'play_constriction_paired_review.py').Replace('\','/')))) {
        $start.ArgumentList.Add($argument)
    }
    foreach ($argument in $terrainArguments) { $start.ArgumentList.Add($argument) }
    $result.arguments=@($start.ArgumentList)
    $editor=[Diagnostics.Process]::Start($start); $result.editor_pid=$editor.Id
    $deadline=[DateTime]::UtcNow.AddSeconds(600)
    while (-not $editor.WaitForExit(1000)) {
        if ([DateTime]::UtcNow -ge $deadline) {
            $result.timeout=$true; $editor.Kill()
            if (-not $editor.WaitForExit(10000)) { throw 'Owned review editor did not exit' }
            break
        }
    }
    $result.editor_exit_code=$editor.ExitCode
} finally {
    for ($index=$paused.Count-1; $index -ge 0; --$index) {
        $item=$paused[$index]
        try { $item.item.process.Refresh(); $item.entry.cpu_before_resume=$item.item.process.TotalProcessorTime.TotalSeconds }
        catch { $item.entry.cpu_error=$_.Exception.Message }
        try { $item.entry.resume=[RaftSimPairedReviewProcessControl]::NtResumeProcess($item.item.handle) }
        catch { $item.entry.resume=-1; $item.entry.resume_error=$_.Exception.Message }
    }
    [IO.File]::WriteAllText($reportFile,($result | ConvertTo-Json -Depth 8) + "`n")
}
if (@($result.processes | Where-Object { $_.suspend -eq 0 -and $_.resume -ne 0 }).Count) { throw 'Cook resume failed; same-handle recovery required' }
if ($result.timeout -or $result.editor_exit_code -ne 0) { throw 'Review editor did not finish successfully' }
$play=Get-Content -LiteralPath $playReport -Raw | ConvertFrom-Json
if ($play.complete -cne $true -or $play.capture_resolution_matched -cne $true) { throw 'Actual PIE review failed; see preserved report' }
$logText=Get-Content -LiteralPath $logFile -Raw
$result.player_viewport_captures_verified=Test-ReviewPlayerCaptureLog $logText @($play.screenshots).Count
if (-not $result.player_viewport_captures_verified) { throw 'Missing actual player-viewport capture confirmation' }
. (Join-Path $PSScriptRoot 'raftsim_startup_motion_evidence.ps1')
$result.motion=Get-RaftSimStartupMotionEvidence -LogText $logText -VideoRoot (Join-Path $projectRoot 'unreal/Saved/VideoCaptures')
[IO.File]::WriteAllText($reportFile,($result | ConvertTo-Json -Depth 8) + "`n")
$result | ConvertTo-Json -Depth 8
