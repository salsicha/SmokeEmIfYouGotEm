param(
    [Parameter(Mandatory=$true)][string]$Label,
    [Parameter(Mandatory=$true)][int]$CookProcessId,
    [Parameter(Mandatory=$true)][string]$CookStartUtc,
    [string]$ExtraGameArgument = '',
    [string[]]$ExtraGameArguments = @(),
    [switch]$NativePerformanceGate
)
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^south-fork-[a-z0-9-]+$') { throw 'Use a fresh scoped capture label' }
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$logFile = Join-Path $projectRoot "unreal/Saved/Logs/$Label.log"
$reportFile = Join-Path $projectRoot "unreal/Saved/RaftSimValidation/$Label-process.json"
$gateFile = Join-Path $projectRoot "unreal/Saved/RaftSimValidation/$Label-gate.json"
if ((Test-Path -LiteralPath $logFile) -or (Test-Path -LiteralPath $reportFile)) { throw 'Preserve previous capture evidence' }
if ($NativePerformanceGate -and (Test-Path -LiteralPath $gateFile)) { throw 'Preserve previous native gate evidence' }
$cookExe = Join-Path $projectRoot 'tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe'
$cook = [Diagnostics.Process]::GetProcessById($CookProcessId)
if ($cook.StartTime.ToUniversalTime().ToString('o') -ne $CookStartUtc -or $cook.MainModule.FileName -ne $cookExe) {
    throw 'Live cook identity does not match explicit caller request'
}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RaftSimProfileProcessControl {
    [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr handle);
    [DllImport("ntdll.dll")] public static extern int NtResumeProcess(IntPtr handle);
}
'@
$suspended = $false
$game = $null
$report = [ordered]@{ cook_pid=$CookProcessId; cook_start_utc=$CookStartUtc; label=$Label; native_gate=[bool]$NativePerformanceGate; gate_passed=$null; suspend_status=$null; resume_status=$null; game_exit_code=$null; game_timeout=$false }
try {
    $report.suspend_status = [RaftSimProfileProcessControl]::NtSuspendProcess($cook.Handle)
    if ($report.suspend_status -ne 0) { throw 'Cook suspension failed; do not label capture isolated' }
    $suspended = $true
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
    } else {
        # Let the profiler own shutdown after its frame count and file flush.
        # A wall/game-time screenshot exit can truncate slow runs to zero bytes.
        $start.ArgumentList.Add('-ExitAfterCsvProfiling')
        $start.ArgumentList.Add("-ExecCmds=csv.TargetFrameRateOverride 30,CsvCategory FMsgLogf disable,csvprofile STARTFILE=$Label,csvprofile FRAMES=300")
    }
    if ($ExtraGameArgument) { $start.ArgumentList.Add($ExtraGameArgument) }
    foreach ($argument in $ExtraGameArguments) { $start.ArgumentList.Add($argument) }
    $game = [Diagnostics.Process]::Start($start)
    $deadline = [DateTime]::UtcNow.AddSeconds(240)
    while (-not $game.WaitForExit(1000)) {
        if ([DateTime]::UtcNow -ge $deadline) {
            $report.game_timeout = $true
            $game.Kill()
            if (-not $game.WaitForExit(10000)) { throw 'Owned capture process did not exit' }
            break
        }
    }
    $report.game_exit_code = $game.ExitCode
    if (-not $NativePerformanceGate -and -not $report.game_timeout -and $game.ExitCode -eq 0) {
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
} finally {
    if ($suspended) {
        $report.resume_status = [RaftSimProfileProcessControl]::NtResumeProcess($cook.Handle)
    }
    [IO.File]::WriteAllText($reportFile, ($report | ConvertTo-Json) + "`n")
    $report | ConvertTo-Json -Compress
}
if ($report.resume_status -ne 0) { throw 'Cook resume failed: immediate same-process recovery required' }
if ($report.game_timeout -or $report.game_exit_code -ne 0) { throw 'Capture did not finish successfully' }
if ($NativePerformanceGate -and -not $report.gate_passed) { throw 'Native performance gate failed; see preserved gate report' }
