<#
Windows PowerShell 5.1 frame audit for a directly launched reference map
(for example L_Hance), editor-hosted game, same CSV rules as
profile_south_fork_menu_launch_ps5.ps1: rows 30..N-30 are audited against the
20 FPS desktop goal (50 ms p95; a hitch is any frame over 100 ms).

-StationM moves the player raft with RaftSim.SurveyReach before the capture
(it settles there and drifts on; the survey exits after the capture window),
so a rapid can be profiled instead of the put-in. Refuses to run while another
game, editor, build or hydraulic cook is live.
#>
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^L_[A-Za-z0-9_]+$')][string]$Map,
    [Parameter(Mandatory = $true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label,
    [ValidateRange(300, 2400)][int]$ProfileFrames = 1200,
    [ValidateRange(-1, 100000)][int]$StationM = -1,
    [int]$TimeoutS = 900,
    [ValidatePattern('^[a-zA-Z0-9_. ;=-]*$')][string]$DiagnosticExecCmds = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project = Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'
$gameBinary = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$logFile = Join-Path $root "unreal/Saved/Logs/$Label.log"
$csvDir = Join-Path $root 'unreal/Saved/Profiling/CSV'
$receipt = Join-Path $root "unreal/Saved/RaftSimValidation/$Label-frame-audit.json"
if (Test-Path -LiteralPath $logFile) { throw "Log already exists: $logFile" }
$busy = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|raftsim_cartesian_cook|raftsim_water_solver|blender)' -or
    ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
})
if ($busy.Count) { throw 'Isolated profiling requires no other game, engine, build, Blender job or hydraulic cook' }
$started = Get-Date
$commands = 'csv.UseLegacyFrameTime 0,csv.TargetFrameRateOverride 20,CsvCategory FMsgLogf disable'
if ($StationM -ge 0) { $commands += ",RaftSim.SurveyReach $StationM $StationM 100 600 $Label-station 30" }
if ($DiagnosticExecCmds -ne '') { $commands += ',' + (($DiagnosticExecCmds.Split(';') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }) -join ',') }
$commands += ",csvprofile STARTFILE=$Label,csvprofile FRAMES=$ProfileFrames"
$gameArgs = @("`"$project`"", "/Game/RaftSim/Maps/$Map",
    '-game', '-RenderOffscreen', '-Unattended', '-NoSplash', '-NoSound',
    '-ResX=1280', '-ResY=720', '-Windowed', '-RaftSimEphemeralProfile', '-csvCompression=0',
    "`"-abslog=$logFile`"", '-ExitAfterCsvProfiling', "`"-ExecCmds=$commands`"")
$binaryHash = (Get-FileHash -LiteralPath $gameBinary -Algorithm SHA256).Hash.ToLower()
$game = Start-Process -FilePath $gameBinary -ArgumentList $gameArgs -WorkingDirectory $root -WindowStyle Hidden -PassThru
if (-not $game.WaitForExit($TimeoutS * 1000)) {
    Stop-Process -Id $game.Id -Force -Confirm:$false
    throw "Game timed out after $TimeoutS s"
}
$game.WaitForExit()
$log = Get-Content -LiteralPath $logFile -Raw -Encoding UTF8
$runtimeErrors = @([regex]::Matches($log, '(?m)^.*\bLog\w+: (?:Error|Fatal):[^\r\n]*') | ForEach-Object { $_.Value })
$m = [regex]::Matches($log, 'LogCsvProfiler: Display: Capture Ended\. Writing CSV to file : [^\r\n]*[/\\]([^/\\\r\n]+\.csv)\s*$', [Text.RegularExpressions.RegexOptions]::Multiline)
if ($m.Count -ne 1) { throw 'CSV capture not confirmed in log' }
$csv = Join-Path $csvDir $m[0].Groups[1].Value
if (-not (Test-Path -LiteralPath $csv) -or (Get-Item -LiteralPath $csv).LastWriteTime -lt $started) { throw 'CSV missing or stale' }
$lines = Get-Content -LiteralPath $csv
$footer = -1
for ($i = $lines.Count - 1; $i -gt 0; $i--) { if ($lines[$i].StartsWith('EVENTS,')) { $footer = $i; break } }
if ($footer -lt 0) { throw 'CSV footer header missing' }
$header = $lines[$footer].Split(',')
$frameIndex = [Array]::IndexOf($header, 'FrameTime')
$gameIndex = [Array]::IndexOf($header, 'GameThreadTime')
$gpuIndex = [Array]::IndexOf($header, 'GPUTime')
$times = New-Object System.Collections.Generic.List[double]; $gt = New-Object System.Collections.Generic.List[double]; $gpu = New-Object System.Collections.Generic.List[double]
for ($i = 1; $i -lt $footer; $i++) {
    $cells = $lines[$i].Split(',')
    $times.Add([double]::Parse($cells[$frameIndex], [Globalization.CultureInfo]::InvariantCulture))
    if ($gameIndex -ge 0 -and $cells.Count -gt $gameIndex) { $gt.Add([double]::Parse($cells[$gameIndex], [Globalization.CultureInfo]::InvariantCulture)) }
    if ($gpuIndex -ge 0 -and $cells.Count -gt $gpuIndex) { $gpu.Add([double]::Parse($cells[$gpuIndex], [Globalization.CultureInfo]::InvariantCulture)) }
}
if ($times.Count -lt $ProfileFrames) { throw "CSV has $($times.Count) frames, expected $ProfileFrames" }
$window = $times.GetRange(30, $times.Count - 60).ToArray()
$sorted = $window | Sort-Object
$p95 = $sorted[[int][Math]::Ceiling(0.95 * $sorted.Count) - 1]
$result = [ordered]@{
    schema = 'raftsim.reference_map_frame_audit.v1'; label = $Label; map = $Map; station_m = $StationM
    game_binary_sha256 = $binaryHash; diagnostic_exec_cmds = $DiagnosticExecCmds; csv = $csv
    frames_total = $times.Count; audited_frames = $window.Count
    mean_ms = [Math]::Round(($window | Measure-Object -Average).Average, 3); p95_ms = [Math]::Round($p95, 3)
    max_ms = [Math]::Round(($window | Measure-Object -Maximum).Maximum, 3)
    frames_over_100ms = @($window | Where-Object { $_ -gt 100 }).Count
    game_thread_mean_ms = $(if ($gt.Count) { [Math]::Round(($gt | Measure-Object -Average).Average, 3) } else { $null })
    gpu_mean_ms = $(if ($gpu.Count) { [Math]::Round(($gpu | Measure-Object -Average).Average, 3) } else { $null })
    runtime_errors = $runtimeErrors
    passes_20fps_goal = ($p95 -le 50.0 -and @($window | Where-Object { $_ -gt 100 }).Count -eq 0 -and $runtimeErrors.Count -eq 0)
}
New-Item -ItemType Directory -Force -Path (Split-Path $receipt) | Out-Null
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receipt -Encoding UTF8
$result | ConvertTo-Json -Depth 4
