param([Parameter(Mandatory=$true)][string]$Label,[switch]$ResidentBurst,[switch]$PairedFusion,[switch]$PairedReductionFusion,
    [ValidateSet('zero-rhs','identity-range')][string]$Control)
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^south-fork-[a-z0-9-]+$') { throw 'Use a fresh scoped label' }
if ($PairedFusion -and $PairedReductionFusion) { throw 'Choose one paired fusion experiment' }
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$csvPath = Join-Path $projectRoot "tmp/$Label-gpu.csv"
$recordPath = Join-Path $projectRoot "tmp/$Label-process.json"
$outputPath = Join-Path $projectRoot "tmp/$Label-native.bin"
$reportDirectory = Join-Path $projectRoot "unreal/Saved/RaftSimValidation/$Label"
$logPath = Join-Path $projectRoot "unreal/Saved/Logs/$Label.log"
foreach ($path in @($csvPath,$recordPath,$outputPath,$reportDirectory,$logPath)) {
    if (Test-Path -LiteralPath $path) { throw "Preserve previous evidence: $path" }
}
function New-HiddenProcessInfo([string]$File,[string[]]$Arguments) {
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $File; $info.UseShellExecute = $false; $info.CreateNoWindow = $true
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    return $info
}
$record = [ordered]@{
    label=$Label; start_utc=[DateTime]::UtcNow.ToString('o'); end_utc=$null
    local_utc_offset_minutes=[TimeZoneInfo]::Local.GetUtcOffset([DateTime]::UtcNow).TotalMinutes
    sampling_interval_ms=100; sampler_pid=$null; sampler_start_utc=$null; sampler_stopped=$false
    editor_pid=$null; editor_start_utc=$null; editor_exit_code=$null; error=$null
    original_cook_or_replay_processes_modified=$false; gpu_settings_changed=$false
    resident_solves_per_graph=$(if($ResidentBurst){16}else{1})
    paired_fusion=[bool]$PairedFusion
    paired_reduction_fusion=[bool]$PairedReductionFusion
    synthetic_control=$Control
}
$sampler = $null; $editor = $null
try {
    $sampleInfo = New-HiddenProcessInfo 'C:/Windows/System32/nvidia-smi.exe' @(
        '--query-gpu=timestamp,name,pstate,clocks.current.graphics,clocks.current.sm,clocks.current.memory,utilization.gpu,temperature.gpu,power.draw',
        '--format=csv','--loop-ms=100',"--filename=$csvPath")
    $sampler = [Diagnostics.Process]::Start($sampleInfo)
    $record.sampler_pid=$sampler.Id; $record.sampler_start_utc=$sampler.StartTime.ToUniversalTime().ToString('o')
    $editorInfo = New-HiddenProcessInfo 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' @(
        (Join-Path $projectRoot 'unreal/SmokeEmIfYouGotEm.uproject'),
        '-ExecCmds=Automation RunTests RaftSim.WaterDetail.Reconstructed;Quit',
        '-TestExit=Automation Test Queue Empty',"-ReportExportPath=$reportDirectory",
        '-unattended','-nosound','-nop4','-RenderOffscreen','-d3d12',"-AbsLog=$logPath",
        "-RaftSimReconstructedPolynomialFixture=$(Join-Path $projectRoot 'tmp/south-fork-reconstructed-polynomial-native-v1-20260914.bin')",
        "-RaftSimReconstructedCGOutput=$outputPath",'-RaftSimReconstructedCGParallelReductions')
    if ($PairedReductionFusion) {
        $editorInfo.ArgumentList.Add('-RaftSimReconstructedCGPairedReductionFusion')
        $editorInfo.ArgumentList.Add('-RaftSimReconstructedCGSlotMajor')
    } elseif ($PairedFusion) {
        $editorInfo.ArgumentList.Add('-RaftSimReconstructedCGPairedFusion')
        $editorInfo.ArgumentList.Add('-RaftSimReconstructedCGSlotMajor')
    } else { $editorInfo.ArgumentList.Add('-RaftSimReconstructedCGPairedLayouts') }
    if ($ResidentBurst) { $editorInfo.ArgumentList.Add('-RaftSimReconstructedCGResidentBurst') }
    if ($Control) { $editorInfo.ArgumentList.Add("-RaftSimReconstructedCGControl=$Control") }
    $editor = [Diagnostics.Process]::Start($editorInfo)
    $record.editor_pid=$editor.Id; $record.editor_start_utc=$editor.StartTime.ToUniversalTime().ToString('o')
    # Observation waits never restart/kill the editor or any original live work.
    while (-not $editor.WaitForExit(1000)) { }
    $record.editor_exit_code=$editor.ExitCode
    if ($sampler.HasExited) { throw 'Telemetry sampler exited before explicit cleanup' }
    # Retain a short post-run tail as well; later analysis must verify actual
    # CSV coverage rather than assume that buffered telemetry reached disk.
    for ($tailSecond=0;$tailSecond -lt 5;++$tailSecond) {
        if ($sampler.WaitForExit(1000)) { throw 'Telemetry sampler exited during post-run tail' }
    }
} catch {
    $record.error=$_.Exception.Message
    throw
} finally {
    # Only the dedicated read-only sampler created above is stopped. No process
    # name search, PID reuse, cook/replay suspension or power-state changes.
    if ($null -ne $sampler) {
        if (-not $sampler.HasExited) { $sampler.Kill(); $sampler.WaitForExit() }
        $record.sampler_stopped=$sampler.HasExited
    }
    $record.end_utc=[DateTime]::UtcNow.ToString('o')
    [IO.File]::WriteAllText($recordPath,($record | ConvertTo-Json -Depth 5)+"`n")
    $record | ConvertTo-Json -Depth 5 -Compress
}
if ($record.editor_exit_code -ne 0) { throw 'Native GPU telemetry run failed; preserve its artifacts' }
