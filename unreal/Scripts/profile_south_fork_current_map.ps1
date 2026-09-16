param(
    [Parameter(Mandatory=$true)][string]$Label,
    [Parameter(Mandatory=$true)][int]$CookProcessId,
    [Parameter(Mandatory=$true)][string]$CookStartUtc,
    [string]$CookExecutable = 'tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe',
    [string]$ShaderWorkloadManifest = '',
    [string]$ExtraGameArgument = '',
    [string[]]$ExtraGameArguments = @(),
    [switch]$NativePerformanceGate,
    [switch]$DetailStreamingReplay
)
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^south-fork-[a-z0-9-]+$') { throw 'Use a fresh scoped capture label' }
if ($NativePerformanceGate -and $DetailStreamingReplay) { throw 'Choose one native validation mode' }
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$logFile = Join-Path $projectRoot "unreal/Saved/Logs/$Label.log"
$reportFile = Join-Path $projectRoot "unreal/Saved/RaftSimValidation/$Label-process.json"
$gateFile = Join-Path $projectRoot "unreal/Saved/RaftSimValidation/$Label-gate.json"
$detailReplayFile = Join-Path $projectRoot "unreal/Saved/RaftSimValidation/$Label-detail.json"
if ((Test-Path -LiteralPath $logFile) -or (Test-Path -LiteralPath $reportFile)) { throw 'Preserve previous capture evidence' }
if ($NativePerformanceGate -and (Test-Path -LiteralPath $gateFile)) { throw 'Preserve previous native gate evidence' }
if ($DetailStreamingReplay -and (Test-Path -LiteralPath $detailReplayFile)) { throw 'Preserve previous detail replay evidence' }
$cookExe = [IO.Path]::GetFullPath((Join-Path $projectRoot $CookExecutable))
$localCookRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'tmp')) + [IO.Path]::DirectorySeparatorChar
if (-not $cookExe.StartsWith($localCookRoot, [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Path]::GetFileName($cookExe) -ne 'raftsim_cartesian_cook.exe') {
    throw 'Explicit cook executable must be a project-local tmp solver'
}
$cook = [Diagnostics.Process]::GetProcessById($CookProcessId)
if ($cook.StartTime.ToUniversalTime().ToString('o') -ne $CookStartUtc -or $cook.MainModule.FileName -ne $cookExe) {
    throw 'Live cook identity does not match explicit caller request'
}
$owned = @([pscustomobject]@{ process=$cook; role='cook'; parent_id=0; handle=$cook.Handle })
if ($ShaderWorkloadManifest) {
    # The caller records the exact existing job, not every editor on the host.
    # Validate ALL identities before suspending ANY process. Retain handles so
    # PID reuse cannot redirect a later resume to a different process.
    $workload = Get-Content -LiteralPath $ShaderWorkloadManifest -Raw | ConvertFrom-Json
    if ($workload.schema -ne 'raftsim.owned_shader_workload.v1' -or
        @($workload.processes).Count -lt 1 -or @($workload.processes).Count -gt 17) {
        throw 'Invalid explicitly owned shader workload'
    }
    $editorExe = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
    $workerExe = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\ShaderCompileWorker.exe'
    $roots = @($workload.processes | Where-Object role -EQ 'shader_editor')
    if ($roots.Count -ne 1) { throw 'Exactly one owned shader editor is required' }
    $seen = @($CookProcessId, $PID)
    foreach ($identity in @($workload.processes | Sort-Object { $_.role -ne 'shader_editor' })) {
        if ($identity.pid -isnot [long] -and $identity.pid -isnot [int]) { throw 'Integer owned process ID required' }
        if ($identity.pid -le 0 -or $identity.pid -in $seen) { throw 'Invalid or duplicate owned process ID' }
        $seen += $identity.pid
        $process = [Diagnostics.Process]::GetProcessById($identity.pid)
        $actual = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $identity.pid)
        $expectedExe = if ($identity.role -eq 'shader_editor') { $editorExe } elseif ($identity.role -eq 'shader_worker') { $workerExe } else { throw 'Unexpected owned process role' }
        # PowerShell 7.5+ decodes JSON ISO timestamps as DateTime by default.
        # Normalize that representation without losing any identity precision.
        $expectedStartUtc = if ($identity.start_utc -is [datetime]) {
            $identity.start_utc.ToUniversalTime().ToString('o')
        } else { $identity.start_utc }
        if ($process.StartTime.ToUniversalTime().ToString('o') -cne $expectedStartUtc -or
            $process.MainModule.FileName -ine $expectedExe -or $identity.executable -ine $expectedExe -or
            [string]::IsNullOrEmpty($identity.command_line) -or $actual.CommandLine -cne $identity.command_line -or
            $actual.ParentProcessId -ne $identity.parent_id) { throw 'Owned shader process identity changed' }
        if ($identity.role -eq 'shader_worker' -and $identity.parent_id -ne $roots[0].pid) { throw 'Worker is outside the explicitly owned shader job' }
        if ($identity.role -eq 'shader_editor' -and
            ($actual.CommandLine -notlike '*Automation RunTests RaftSim.*' -or
             $actual.CommandLine -notmatch '(?i)(?:^|\s)-sm5(?:\s|$)' -or
             -not $actual.CommandLine.Replace('\','/').Contains($projectRoot.Replace('\','/')+'/unreal/SmokeEmIfYouGotEm.uproject'))) {
            throw 'Owned editor is not this project SM5 automation job'
        }
        $owned += [pscustomobject]@{ process=$process; role=$identity.role; parent_id=$identity.parent_id; handle=$process.Handle }
    }
}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RaftSimProfileProcessControl {
    [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr handle);
    [DllImport("ntdll.dll")] public static extern int NtResumeProcess(IntPtr handle);
}
'@
$paused = @()
$game = $null
$report = [ordered]@{ cook_pid=$CookProcessId; cook_start_utc=$CookStartUtc; cook_executable=$cookExe; cook_sha256=(Get-FileHash -LiteralPath $cookExe).Hash.ToLowerInvariant(); shader_manifest=$ShaderWorkloadManifest; label=$Label; native_gate=[bool]$NativePerformanceGate; gate_passed=$null; suspend_status=$null; resume_status=$null; processes=@(); game_exit_code=$null; game_timeout=$false }
$report.detail_replay = [bool]$DetailStreamingReplay
$report.detail_replay_passed = $null
try {
    foreach ($item in $owned) {
        $entry = [ordered]@{ pid=$item.process.Id; role=$item.role; start_utc=$item.process.StartTime.ToUniversalTime().ToString('o'); executable=$item.process.MainModule.FileName; cpu_seconds_before=$item.process.TotalProcessorTime.TotalSeconds; cpu_seconds_before_resume=$null; suspend=$null; resume=$null }
        $report.processes += $entry
        $entry.suspend = [RaftSimProfileProcessControl]::NtSuspendProcess($item.handle)
        if ($item.role -eq 'cook') { $report.suspend_status=$entry.suspend }
        if ($entry.suspend -ne 0) { throw 'Owned job suspension failed; no isolated profile' }
        $paused += @{ item=$item; entry=$entry }
    }
    if ($ShaderWorkloadManifest) {
        # Parent is now suspended: its child set must match the explicit
        # manifest. A new/exited worker invalidates isolation; do not expand scope.
        $actualWorkers = @((Get-CimInstance Win32_Process -Filter ('ParentProcessId='+$roots[0].pid+" AND Name='ShaderCompileWorker.exe'")).ProcessId | Sort-Object)
        $expectedWorkers = @($owned | Where-Object role -EQ 'shader_worker' | ForEach-Object { $_.process.Id } | Sort-Object)
        if (($actualWorkers -join ',') -ne ($expectedWorkers -join ',')) { throw 'Owned worker set changed; no isolated profile' }
    }
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    foreach ($argument in @((Join-Path $projectRoot 'unreal/SmokeEmIfYouGotEm.uproject'),
        '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach', '-game', '-RenderOffscreen', '-Unattended',
        '-NoSplash', '-NoSound', '-ResX=1280', '-ResY=720', '-Windowed', '-RaftSimEphemeralProfile',
        '-RaftSimScenario=south_fork_full_descent', '-RaftSimWaterReviewStation=8330', '-csvCompression=0',
        "-abslog=$logFile")) { $start.ArgumentList.Add($argument) }
    if ($NativePerformanceGate) {
        # The director owns completion. No screenshot auto-exit may truncate
        # its warmup/soak. This short development run is not release acceptance.
        foreach ($argument in @('-RaftSimPerformanceWarmupSeconds=10', '-RaftSimPerformanceSoakSeconds=20',
            '-RaftSimPerformanceRequiredMap=L_SouthForkAmerican_FullReach', "-RaftSimValidationOutput=$gateFile")) {
            $start.ArgumentList.Add($argument)
        }
    } elseif ($DetailStreamingReplay) {
        # The existing read-only native probe owns all coverage gates and its
        # unchanged 900-second observation timeout. Never truncate it with CSV.
        $start.ArgumentList.Add('-ForceRes')
        $start.ArgumentList.Add("-RaftSimDetailStreamingReport=$detailReplayFile")
    } else {
        # Let the profiler own shutdown after its frame count and file flush.
        # A wall/game-time screenshot exit can truncate slow runs to zero bytes.
        $start.ArgumentList.Add('-ExitAfterCsvProfiling')
        $start.ArgumentList.Add("-ExecCmds=csv.TargetFrameRateOverride 30,CsvCategory FMsgLogf disable,csvprofile STARTFILE=$Label,csvprofile FRAMES=300")
    }
    if ($ExtraGameArgument) { $start.ArgumentList.Add($ExtraGameArgument) }
    foreach ($argument in $ExtraGameArguments) { $start.ArgumentList.Add($argument) }
    $game = [Diagnostics.Process]::Start($start)
    # Native replay still fails itself at 900 seconds. The outer watchdog only
    # allows startup/report flushing; it does not alter a native acceptance gate.
    $deadline = [DateTime]::UtcNow.AddSeconds($(if ($DetailStreamingReplay) { 960 } else { 240 }))
    while (-not $game.WaitForExit(1000)) {
        if ([DateTime]::UtcNow -ge $deadline) {
            $report.game_timeout = $true
            $game.Kill()
            if (-not $game.WaitForExit(10000)) { throw 'Owned capture process did not exit' }
            break
        }
    }
    $report.game_exit_code = $game.ExitCode
    if (-not $NativePerformanceGate -and -not $DetailStreamingReplay -and -not $report.game_timeout -and $game.ExitCode -eq 0) {
        $csvFile = Join-Path $projectRoot "unreal/Saved/Profiling/CSV/$Label.csv"
        if (-not (Test-Path -LiteralPath $csvFile) -or (Get-Item -LiteralPath $csvFile).Length -eq 0) {
            throw 'Profiler exited without a nonempty CSV; no timing evidence'
        }
        $report.csv_file = $csvFile
        $report.csv_sha256 = (Get-FileHash -LiteralPath $csvFile -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    if ($NativePerformanceGate) {
        # Unreal's requested status can differ from the host process status.
        # Require the actual fresh report; exit 0 alone is never a gate pass.
        if (-not (Test-Path -LiteralPath $gateFile)) { throw 'Native performance report was not produced' }
        $gate = Get-Content -LiteralPath $gateFile -Raw | ConvertFrom-Json
        if ($gate.passed -isnot [bool]) { throw 'Native performance report lacks a Boolean result' }
        $report.gate_passed = $gate.passed
    }
    if ($DetailStreamingReplay) {
        if (-not (Test-Path -LiteralPath $detailReplayFile)) { throw 'Native detail replay report was not produced' }
        $detailReplay = Get-Content -LiteralPath $detailReplayFile -Raw | ConvertFrom-Json
        if ($detailReplay.schema -ne 'raftsim.detail_streaming_actual_play.v1' -or $detailReplay.passed -isnot [bool]) {
            throw 'Invalid native detail replay report'
        }
        $report.detail_replay_passed = $detailReplay.passed
        $report.detail_replay_file = $detailReplayFile
        $report.detail_replay_sha256 = (Get-FileHash -LiteralPath $detailReplayFile).Hash.ToLowerInvariant()
    }
} finally {
    # Resume workers before their editor, then the cook, even after a failed
    # launch/partial suspension. One recovery failure must not skip the others.
    for ($index=$paused.Count-1; $index -ge 0; --$index) {
        $item=$paused[$index]
        try {
            $item.item.process.Refresh()
            $item.entry.cpu_seconds_before_resume=$item.item.process.TotalProcessorTime.TotalSeconds
        } catch { $item.entry.cpu_observation_error=$_.Exception.Message }
        try { $item.entry.resume=[RaftSimProfileProcessControl]::NtResumeProcess($item.item.handle) }
        catch { $item.entry.resume_error=$_.Exception.Message; $item.entry.resume=-1 }
        if ($item.item.role -eq 'cook') { $report.resume_status=$item.entry.resume }
    }
    [IO.File]::WriteAllText($reportFile, ($report | ConvertTo-Json -Depth 6) + "`n")
    $report | ConvertTo-Json -Depth 6 -Compress
}
if (@($report.processes | Where-Object { $_.suspend -eq 0 -and $_.resume -ne 0 }).Count) { throw 'Owned process resume failed: immediate same-process recovery required' }
if ($report.game_timeout -or $report.game_exit_code -ne 0) { throw 'Capture did not finish successfully' }
if ($NativePerformanceGate -and -not $report.gate_passed) { throw 'Native performance gate failed; see preserved gate report' }
if ($DetailStreamingReplay -and -not $report.detail_replay_passed) { throw 'Native detail replay failed; see preserved replay report' }
