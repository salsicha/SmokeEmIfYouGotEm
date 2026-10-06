param(
    [Parameter(Mandatory=$true)][string]$Label,
    [Parameter(Mandatory=$true)][int]$CookProcessId,
    [Parameter(Mandatory=$true)][string]$CookStartUtc,
    [int]$ReplayProcessId=0,
    [string]$ReplayStartUtc='',
    [ValidateSet('NonlinearAccelerationGPU','NonlinearPressureGPU','TemporalEvolutionGPU')][string]$TestName='NonlinearAccelerationGPU',
    [string]$PressureFixture='',
    [string]$PrescribedPressureFixture='',
    [string]$TemporalEvolutionFixture='',
    [switch]$UnculledTemporalEvolution
)
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^south-fork-[a-z0-9-]+$') { throw 'Use a fresh scoped label' }
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$reportDirectory = Join-Path $projectRoot "unreal/Saved/RaftSimValidation/$Label"
$logFile = Join-Path $projectRoot "unreal/Saved/Logs/$Label.log"
$processReport = Join-Path $projectRoot "unreal/Saved/RaftSimValidation/$Label-process.json"
if ((Test-Path -LiteralPath $reportDirectory) -or (Test-Path -LiteralPath $logFile) -or (Test-Path -LiteralPath $processReport)) { throw 'Preserve previous evidence' }
if ($TestName -eq 'NonlinearPressureGPU' -and -not (Test-Path -LiteralPath $PressureFixture -PathType Leaf)) { throw 'Generate the explicit pressure fixture first' }
if ($TestName -eq 'NonlinearPressureGPU' -and -not (Test-Path -LiteralPath $PrescribedPressureFixture -PathType Leaf)) { throw 'Generate the prescribed face-pressure fixture first' }
if ($TestName -eq 'TemporalEvolutionGPU' -and -not (Test-Path -LiteralPath $TemporalEvolutionFixture -PathType Leaf)) { throw 'Generate the actual temporal evolution fixture first' }
if ($UnculledTemporalEvolution -and $TestName -ne 'TemporalEvolutionGPU') { throw 'Unculled control requires the temporal evolution test' }
$cook = [Diagnostics.Process]::GetProcessById($CookProcessId)
if ($cook.StartTime.ToUniversalTime().ToString('o') -ne $CookStartUtc -or
    $cook.MainModule.FileName -ne (Join-Path $projectRoot 'tmp/south-fork-checkpoint-solver-v1-20260912/raftsim_cartesian_cook.exe')) { throw 'Cook identity changed' }
$ownedProcesses = @($cook)
# Omit both replay arguments only after its owned session has exited. Never
# silently ignore an explicitly supplied missing or identity-mismatched job.
if (($ReplayProcessId -eq 0) -ne [string]::IsNullOrEmpty($ReplayStartUtc)) { throw 'Supply both replay identity arguments or neither' }
if ($ReplayProcessId -ne 0) {
    $replay = [Diagnostics.Process]::GetProcessById($ReplayProcessId)
    if ($replay.StartTime.ToUniversalTime().ToString('o') -ne $ReplayStartUtc -or $replay.ProcessName -ne 'python') { throw 'Replay identity changed' }
    $replayCommand = (Get-CimInstance Win32_Process -Filter "ProcessId=$ReplayProcessId").CommandLine
    $knownReplay = $replayCommand -like '*south-fork-fixed-bed-pressure-bank-twenty-second-v1-20260912.json*' -or
        $replayCommand -like '*south-fork-hybrid-front-bank-twenty-second-v1-20260912.json*'
    if ($replayCommand -notlike '*total_depth_bank_replay.py*' -or -not $knownReplay) { throw 'Not an explicitly scoped replay' }
    $ownedProcesses += $replay
}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RaftSimAccelerationProfileControl {
    [DllImport("ntdll.dll")] public static extern int NtSuspendProcess(IntPtr handle);
    [DllImport("ntdll.dll")] public static extern int NtResumeProcess(IntPtr handle);
}
'@
$paused = @()
$record = [ordered]@{ label=$Label; test=$TestName; pressure_fixture=$PressureFixture; prescribed_pressure_fixture=$PrescribedPressureFixture; temporal_evolution_fixture=$TemporalEvolutionFixture; cull_inactive_iterations=($TestName -eq 'TemporalEvolutionGPU' -and -not $UnculledTemporalEvolution); paired_temporal_timing=($TestName -eq 'TemporalEvolutionGPU'); isolated_from_owned_jobs=$false; processes=@(); editor_exit_code=$null; timeout=$false }
try {
    foreach ($process in $ownedProcesses) {
        $entry = [ordered]@{ pid=$process.Id; start_utc=$process.StartTime.ToUniversalTime().ToString('o'); suspend=$null; resume=$null }
        $record.processes += $entry
        $entry.suspend = [RaftSimAccelerationProfileControl]::NtSuspendProcess($process.Handle)
        if ($entry.suspend -ne 0) { throw 'Suspension failed; do not claim isolation' }
        $paused += @{ process=$process; entry=$entry }
    }
    $record.isolated_from_owned_jobs = $true
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
    $start.UseShellExecute = $false; $start.CreateNoWindow = $true
    foreach ($argument in @((Join-Path $projectRoot 'unreal/SmokeEmIfYouGotEm.uproject'),
        "-ExecCmds=Automation RunTests RaftSim.WaterDetail.$TestName;Quit",
        '-TestExit=Automation Test Queue Empty',"-ReportExportPath=$reportDirectory",
        '-unattended','-nosound','-nop4','-RenderOffscreen','-d3d12',"-AbsLog=$logFile")) { $start.ArgumentList.Add($argument) }
    if ($TestName -eq 'NonlinearPressureGPU') {
        $start.ArgumentList.Add("-RaftSimNonlinearPressureFixture=$([IO.Path]::GetFullPath($PressureFixture))")
        $start.ArgumentList.Add("-RaftSimPrescribedPressureFixture=$([IO.Path]::GetFullPath($PrescribedPressureFixture))")
        $start.ArgumentList.Add('-RaftSimPressureTiming')
    }
    if ($TestName -eq 'TemporalEvolutionGPU') {
        $start.ArgumentList.Add("-RaftSimTemporalEvolutionFixture=$([IO.Path]::GetFullPath($TemporalEvolutionFixture))")
        $start.ArgumentList.Add('-RaftSimTemporalEvolutionTiming')
        if ($UnculledTemporalEvolution) { $start.ArgumentList.Add('-RaftSimUnculledTemporalEvolution') }
    }
    $editor = [Diagnostics.Process]::Start($start)
    $deadline = [DateTime]::UtcNow.AddSeconds(180)
    while (-not $editor.WaitForExit(1000)) {
        if ([DateTime]::UtcNow -ge $deadline) { $record.timeout=$true; $editor.Kill(); $editor.WaitForExit(); break }
    }
    $record.editor_exit_code = $editor.ExitCode
} finally {
    foreach ($item in $paused) { $item.entry.resume = [RaftSimAccelerationProfileControl]::NtResumeProcess($item.process.Handle) }
    [IO.File]::WriteAllText($processReport,($record | ConvertTo-Json -Depth 5)+"`n")
    $record | ConvertTo-Json -Depth 5 -Compress
}
if (@($record.processes | Where-Object { $_.suspend -eq 0 -and $_.resume -ne 0 }).Count) { throw 'Immediate same-process resume recovery required' }
if ($record.timeout -or $record.editor_exit_code -ne 0) { throw 'GPU component test did not finish normally' }
