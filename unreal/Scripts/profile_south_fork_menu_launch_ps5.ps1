<#
Windows PowerShell 5.1 counterpart of `profile_south_fork_current_map.ps1 -NormalMenuLaunch -NoCookWorkload`.

The main profiler uses ProcessStartInfo.ArgumentList (PowerShell 7 / .NET Core
only). This script launches the same Editor-hosted game with the same game
arguments (project default Boot map, real main-menu scenario command, native
post-travel CSV hook), confirms Boot -> menu -> FullReach -> one CSV capture in
order, and reports frame statistics against the current 20 FPS desktop goal
(50 ms p95; a hitch is any frame over 100 ms). Rows 30..N-30 are audited like the
September 26 receipt. No review station, solver override or quality change.
#>
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label,
    [ValidateRange(300, 2400)][int]$ProfileFrames = 1200,
    [int]$TimeoutS = 900,
    # Optional diagnostic: a direct FullReach review-station start instead of
    # the normal Boot/menu launch, to cover other parts of the run.
    [ValidateRange(-1, 33280)][int]$ReviewStationM = -1
)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project = Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'
$logFile = Join-Path $root "unreal/Saved/Logs/$Label.log"
$csvDir = Join-Path $root 'unreal/Saved/Profiling/CSV'
$receipt = Join-Path $root "unreal/Saved/RaftSimValidation/$Label-frame-audit.json"
if (Test-Path -LiteralPath $logFile) { throw "Log already exists: $logFile" }
$started = Get-Date
$review = $ReviewStationM -ge 0
$csvCommands = 'csv.UseLegacyFrameTime 0,csv.TargetFrameRateOverride 20,CsvCategory FMsgLogf disable'
$gameArgs = @("`"$project`"")
if ($review) { $gameArgs += '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach' }
$gameArgs += @(
    '-game', '-RenderOffscreen', '-Unattended', '-NoSplash', '-NoSound',
    '-ResX=1280', '-ResY=720', '-Windowed', '-RaftSimEphemeralProfile',
    '-RaftSimScenario=south_fork_full_descent', '-csvCompression=0', "`"-abslog=$logFile`"",
    '-ExitAfterCsvProfiling')
if ($review) {
    $gameArgs += @("-RaftSimWaterReviewStation=$ReviewStationM",
        "`"-ExecCmds=$csvCommands,csvprofile STARTFILE=$Label,csvprofile FRAMES=$ProfileFrames`"")
} else {
    $gameArgs += @("-RaftSimPostTravelCsvFrames=$ProfileFrames",
        "`"-ExecCmds=RaftSim.MenuScreen main start=south_fork_full_descent,$csvCommands`"")
}
$game = Start-Process -FilePath 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' -ArgumentList $gameArgs -PassThru
if (-not $game.WaitForExit($TimeoutS * 1000)) {
    Stop-Process -Id $game.Id -Force -Confirm:$false
    throw "Game timed out after $TimeoutS s"
}
$log = Get-Content -LiteralPath $logFile -Raw -Encoding UTF8
$csvEnded = 'LogCsvProfiler: Display: Capture Ended\. Writing CSV to file : [^\r\n]*[/\\]([^/\\\r\n]+\.csv)\s*$'
$patterns = if ($review) { @(
    'LogLoad: LoadMap: /Game/RaftSim/Maps/L_SouthForkAmerican_FullReach(?:\?|\s|$)', $csvEnded)
} else { @(
    'LogLoad: LoadMap: /Game/RaftSim/Maps/L_RaftSimBoot(?:\?|\s|$)',
    'LogTemp: Display: RaftSim\.MenuScreen: showing main',
    'LogLoad: LoadMap: /Game/RaftSim/Maps/L_SouthForkAmerican_FullReach(?:\?|\s|$)',
    'LogTemp: Display: RaftSim post-travel CSV event: world=/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach\.',
    ('LogTemp: Display: RaftSim post-travel CSV capture: frames=' + $ProfileFrames + '(?:\s|$)'),
    $csvEnded) }
$previous = -1; $leaf = ''
foreach ($pattern in $patterns) {
    $m = [regex]::Matches($log, $pattern, [Text.RegularExpressions.RegexOptions]::Multiline)
    if ($m.Count -ne 1 -or $m[0].Index -le $previous) { throw "Launch order not confirmed at: $pattern" }
    $previous = $m[0].Index
    if ($m[0].Groups.Count -gt 1) { $leaf = $m[0].Groups[1].Value }
}
$csv = Join-Path $csvDir $leaf
if (-not (Test-Path -LiteralPath $csv) -or (Get-Item -LiteralPath $csv).LastWriteTime -lt $started) { throw 'CSV missing or stale' }
$lines = Get-Content -LiteralPath $csv
# Unreal appends a column whenever a stat first appears, so early rows are
# narrower and the authoritative header is the one repeated after the data.
# Existing columns never move, so the footer header's index applies to every row.
$footer = -1
for ($i = $lines.Count - 1; $i -gt 0; $i--) { if ($lines[$i].StartsWith('EVENTS,')) { $footer = $i; break } }
if ($footer -lt 0) { throw 'CSV footer header missing' }
$header = $lines[$footer].Split(',')
$frameIndex = [Array]::IndexOf($header, 'FrameTime')
if ($frameIndex -lt 0 -or [Array]::IndexOf($lines[0].Split(','), 'FrameTime') -ne $frameIndex) { throw 'FrameTime column missing or moved' }
$times = New-Object System.Collections.Generic.List[double]
for ($i = 1; $i -lt $footer; $i++) {
    $cells = $lines[$i].Split(',')
    if ($cells.Count -le $frameIndex -or $cells.Count -gt $header.Count) { throw "Malformed CSV row $i" }
    $times.Add([double]::Parse($cells[$frameIndex], [Globalization.CultureInfo]::InvariantCulture))
}
if ($times.Count -lt $ProfileFrames) { throw "CSV has $($times.Count) frames, expected $ProfileFrames" }
$window = $times.GetRange(30, $times.Count - 60).ToArray()
$sorted = $window | Sort-Object
$p95 = $sorted[[int][Math]::Ceiling(0.95 * $sorted.Count) - 1]
$mean = ($window | Measure-Object -Average).Average
$max = ($window | Measure-Object -Maximum).Maximum
$twoFrame = 0.0
for ($i = 1; $i -lt $window.Count; $i++) { $twoFrame = [Math]::Max($twoFrame, $window[$i] + $window[$i - 1]) }
$result = [ordered]@{
    schema = 'raftsim.south_fork_menu_launch_frame_audit.v1'; label = $Label
    launch_mode = $(if ($review) { "review_station_$ReviewStationM" } else { 'boot_menu' })
    game_exit_code = $game.ExitCode; csv = $csv; csv_sha256 = (Get-FileHash -LiteralPath $csv -Algorithm SHA256).Hash.ToLower()
    frames_total = $times.Count; audited_rows = "30..$($times.Count - 31)"; audited_frames = $window.Count
    mean_ms = [Math]::Round($mean, 4); p95_ms = [Math]::Round($p95, 4); max_ms = [Math]::Round($max, 4)
    max_consecutive_pair_ms = [Math]::Round($twoFrame, 4); frames_over_100ms = @($window | Where-Object { $_ -gt 100 }).Count
    target_fps = 20; p95_budget_ms = 50; two_frame_hitch_ms = 100
    # Hitch = any single frame over two 50 ms frame budgets (as in the Sept 26 receipt).
    p95_passes = ($p95 -le 50); hitch_passes = (@($window | Where-Object { $_ -gt 100 }).Count -eq 0)
}
New-Item -ItemType Directory -Force -Path (Split-Path $receipt) | Out-Null
$result | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding UTF8
$result | ConvertTo-Json
