<#
Windows PowerShell 5.1 counterpart of `profile_south_fork_current_map.ps1 -NormalMenuLaunch -NoCookWorkload`.

The main profiler uses ProcessStartInfo.ArgumentList (PowerShell 7 / .NET Core
only). This script launches the same Editor-hosted game with the same game
arguments (project default Boot map, real main-menu scenario command, native
post-travel CSV hook), confirms Boot -> menu -> FullReach -> one CSV capture in
order, and reports frame statistics against the current 20 FPS desktop goal
(every audited frame <=50 ms; p95 and hitches are descriptive). Rows 30..N-30 are audited like the
September 26 receipt. No review station, solver override or quality change.
#>
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label,
    [ValidateRange(300, 2400)][int]$ProfileFrames = 1200,
    [int]$TimeoutS = 900,
    # A cooked Windows stage (containing SmokeEmIfYouGotEm/), not an editor game.
    [string]$PackagedRoot = '',
    # Optional diagnostic: a direct FullReach review-station start instead of
    # the normal Boot/menu launch, to cover other parts of the run.
    [ValidateRange(-1, 33280)][int]$ReviewStationM = -1,
    # Optional diagnostic console variables, e.g. 'r.Shadow.Virtual.Enable 0'
    # (';'-separated). Recorded in the receipt; never a normal-launch result.
    [ValidatePattern('^[a-zA-Z0-9_. ;-]*$')][string]$DiagnosticExecCmds = '',
    # Same-build reference only; receipt explicitly identifies the non-default search.
    [switch]$LegacyBreakingSearch,
    # Same v21+ binary, original all-edge detail refinement. Never normal play.
    [switch]$LegacyDetailEdges,
    [switch]$ExhaustiveLandscapeFaces,
    [switch]$RigidOnlyMovingFaceTree,
    [switch]$OriginalFaceTreeAudit,
    # Same-build original deep-copy diagnostic; never normal configuration.
    [switch]$ReferenceSnapshotCopy,
    # Explicit rejected copy-reuse experiment; not the normal default.
    [switch]$ExactSnapshotCopy,
    # Same-build complete original rest-attribute scan instead of sealed ownership.
    [switch]$ReferenceRestKey
)
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project = Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'
$gameBinary = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$gameWorkingDirectory = $root
$logFile = Join-Path $root "unreal/Saved/Logs/$Label.log"
$csvDir = Join-Path $root 'unreal/Saved/Profiling/CSV'
function Get-RaftSimPackagedLaunchPaths([string]$RepositoryRoot, [string]$StageRoot) {
    $stage = [IO.Path]::GetFullPath($StageRoot)
    $allowed = [IO.Path]::GetFullPath((Join-Path $RepositoryRoot 'tmp')) + [IO.Path]::DirectorySeparatorChar
    if (-not $stage.StartsWith($allowed, [StringComparison]::OrdinalIgnoreCase)) { throw 'Use a retained project-local tmp stage' }
    $gameRoot = Join-Path $stage 'SmokeEmIfYouGotEm'
    $binary = Join-Path $gameRoot 'Binaries/Win64/SmokeEmIfYouGotEm.exe'
    if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw 'Cooked inner executable missing' }
    if (-not (Test-Path -LiteralPath (Join-Path $gameRoot 'Content/Paks') -PathType Container)) { throw 'Cooked Paks missing' }
    @{ Binary=$binary; CsvDirectory=(Join-Path $gameRoot 'Saved/Profiling/CSV'); WorkingDirectory=$stage }
}
if ($PackagedRoot -ne '') {
    $paths = Get-RaftSimPackagedLaunchPaths $root $PackagedRoot
    $gameBinary = $paths.Binary; $csvDir = $paths.CsvDirectory; $gameWorkingDirectory = $paths.WorkingDirectory
}
$receipt = Join-Path $root "unreal/Saved/RaftSimValidation/$Label-frame-audit.json"
function Get-RaftSimRuntimeErrors([string]$LogText) {
    # A fast frame after a failed water subsystem is not a healthy performance pass.
    @([regex]::Matches($LogText, '(?m)^.*\bLog\w+: (?:Error|Fatal):[^\r\n]*') |
        ForEach-Object { $_.Value })
}
function Get-RaftSimDetailEdgeMode([string]$LogText, [bool]$Legacy) {
    # Require actual runtime confirmation, not a command-line echo. Retain
    # every report so conflicting components cannot masquerade as one mode.
    $prefix = '(?m)^.*\bLogTemp: Display: Crest selective detail edges: '
    $lines = @([regex]::Matches($LogText, $prefix + '[^\r\n]*'))
    if (-not $lines.Count) { throw 'Detail-edge runtime mode missing; use a v21+ binary' }
    $expected = if ($Legacy) { 'enabled=0 legacy_override=1;' } else { 'enabled=1 legacy_override=0;' }
    foreach ($line in $lines) {
        if ($line.Value -notmatch ($prefix + [regex]::Escape($expected))) {
            throw 'Missing, malformed or conflicting detail-edge runtime mode'
        }
    }
    @{ selective_enabled = (-not $Legacy); legacy_override = $Legacy; confirmed_reports = $lines.Count }
}
function Get-RaftSimRestKeyObservation([string[]]$Header,[string[]]$Rows,[bool]$ReferenceRequested) {
    $sealed=[Array]::IndexOf($Header,'RaftSimHull/RestKeySealedChecks')
    $reference=[Array]::IndexOf($Header,'RaftSimHull/RestKeyReferenceChecks')
    if($sealed -lt 0 -and $reference -lt 0){
        if($ReferenceRequested){throw 'Rest-key diagnostic requires actual native counters'}
        return $null
    }
    if($sealed -lt 0 -or $reference -lt 0 -or -not $Rows.Count){throw 'Incomplete native rest-key counters'}
    $sealedSum=0.0;$referenceSum=0.0
    foreach($row in $Rows){
        $cells=$row.Split(',');$values=@()
        foreach($column in @($sealed,$reference)){
            if($column -ge $cells.Count -or $cells[$column] -eq ''){throw 'Incomplete native rest-key observation'}
            $value=[double]::Parse($cells[$column],[Globalization.CultureInfo]::InvariantCulture)
            if([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt 0 -or $value -ne [math]::Floor($value)){throw 'Invalid native rest-key observation'}
            $values+=@($value)
        }
        $sealedSum+=$values[0];$referenceSum+=$values[1]
    }
    if($ReferenceRequested -and ($sealedSum -ne 0 -or $referenceSum -le 0)){throw 'Actual original rest scan not confirmed'}
    if(-not $ReferenceRequested -and $sealedSum -le 0){throw 'Actual sealed rest-key path not confirmed'}
    @{audited_frames=$Rows.Count;sealed_checks_sum=$sealedSum;reference_checks_sum=$referenceSum;reference_requested=$ReferenceRequested}
}
function Test-RaftSimProfileWorkload($Process) {
    $Process.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|raftsim_cartesian_cook)' -or
    ($Process.Name -in @('dotnet.exe','cmd.exe') -and $Process.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool') -or
    ($Process.Name -match '^python(w)?(\.exe)?$' -and $Process.CommandLine -match 'audit_south_fork[^\s]*')
}
if (Test-Path -LiteralPath $logFile) { throw "Log already exists: $logFile" }
$started = Get-Date
$review = $ReviewStationM -ge 0
$csvCommands = 'csv.UseLegacyFrameTime 0,csv.TargetFrameRateOverride 20,CsvCategory FMsgLogf disable'
if ($DiagnosticExecCmds -ne '') { $csvCommands += ',' + (($DiagnosticExecCmds.Split(';') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }) -join ',') }
$gameArgs = @()
if ($PackagedRoot -eq '') { $gameArgs += "`"$project`"" }
if ($review) { $gameArgs += '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach' }
$gameArgs += @(
    '-game', '-RenderOffscreen', '-Unattended', '-NoSplash', '-NoSound',
    '-ResX=1280', '-ResY=720', '-Windowed', '-RaftSimEphemeralProfile',
    '-RaftSimScenario=south_fork_full_descent', '-csvCompression=0', "`"-abslog=$logFile`"",
    '-ExitAfterCsvProfiling')
if ($LegacyBreakingSearch) { $gameArgs += '-RaftSimLegacyBreakingSearch' }
if ($LegacyDetailEdges) { $gameArgs += '-RaftSimLegacyDetailEdges' }
$collisionArguments=@()
if($ExhaustiveLandscapeFaces){$collisionArguments+='-RaftSimExhaustiveLandscapeFaces'}
if($RigidOnlyMovingFaceTree){$collisionArguments+='-RaftSimRigidOnlyMovingFaceTree'}
if($OriginalFaceTreeAudit){$collisionArguments+=@('-RaftSimLandscapeFaceTreeAudit','-RaftSimMovingEndpointTreeAudit')}
$gameArgs+=$collisionArguments
if($ReferenceSnapshotCopy){$gameArgs+='-RaftSimReferenceSnapshotCopy'}
if($ExactSnapshotCopy){$gameArgs+='-RaftSimExactSnapshotCopy'}
if($ReferenceRestKey){$gameArgs+='-RaftSimReferenceRestKey'}
if ($review) {
    $gameArgs += @("-RaftSimWaterReviewStation=$ReviewStationM",
        "`"-ExecCmds=$csvCommands,csvprofile STARTFILE=$Label,csvprofile FRAMES=$ProfileFrames`"")
} else {
    $gameArgs += @("-RaftSimPostTravelCsvFrames=$ProfileFrames",
        "`"-ExecCmds=RaftSim.MenuScreen main start=south_fork_full_descent,$csvCommands`"")
}
$busy = @(Get-CimInstance Win32_Process | Where-Object {
    Test-RaftSimProfileWorkload $_
})
if ($busy.Count) { throw 'Isolated profiling requires no other game, engine, build, hydraulic cook or South Fork source audit' }
$binaryHash = (Get-FileHash -LiteralPath $gameBinary -Algorithm SHA256).Hash.ToLower()
$game = Start-Process -FilePath $gameBinary -ArgumentList $gameArgs -WorkingDirectory $gameWorkingDirectory -WindowStyle Hidden -PassThru
if (-not $game.WaitForExit($TimeoutS * 1000)) {
    Stop-Process -Id $game.Id -Force -Confirm:$false
    throw "Game timed out after $TimeoutS s"
}
$game.WaitForExit()
if ($game.ExitCode -ne 0) { throw "Game failed with exit code $($game.ExitCode)" }
if ((Get-FileHash -LiteralPath $gameBinary -Algorithm SHA256).Hash.ToLower() -ne $binaryHash) { throw 'Game binary changed during profiling' }
$log = Get-Content -LiteralPath $logFile -Raw -Encoding UTF8
$runtimeErrors = @(Get-RaftSimRuntimeErrors $log)
$detailEdgeMode = Get-RaftSimDetailEdgeMode $log ([bool]$LegacyDetailEdges)
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
    $elapsed=[double]::Parse($cells[$frameIndex], [Globalization.CultureInfo]::InvariantCulture)
    if([double]::IsNaN($elapsed) -or [double]::IsInfinity($elapsed) -or $elapsed -le 0){throw 'Finite positive actual elapsed frame time required'}
    $times.Add($elapsed)
}
if ($times.Count -lt $ProfileFrames) { throw "CSV has $($times.Count) frames, expected $ProfileFrames" }
$window = $times.GetRange(30, $times.Count - 60).ToArray()
$sorted = $window | Sort-Object
$p95 = $sorted[[int][Math]::Ceiling(0.95 * $sorted.Count) - 1]
$mean = ($window | Measure-Object -Average).Average
$max = ($window | Measure-Object -Maximum).Maximum
$twoFrame = 0.0
for ($i = 1; $i -lt $window.Count; $i++) { $twoFrame = [Math]::Max($twoFrame, $window[$i] + $window[$i - 1]) }
$copyObservation=$null
$assignedColumn=[Array]::IndexOf($header,'RaftSimHull/PreparedArraysAssigned')
$retainedColumn=[Array]::IndexOf($header,'RaftSimHull/PreparedArraysRetained')
if($assignedColumn -ge 0 -and $retainedColumn -ge 0){
    $assignedSum=0.0;$retainedSum=0.0
    for($row=30;$row -lt $times.Count-30;$row++){
        $cells=$lines[$row+1].Split(',')
        foreach($column in @($assignedColumn,$retainedColumn)){
            if($column -ge $cells.Count -or $cells[$column] -eq ''){throw 'Incomplete native snapshot-copy observation'}
            $value=[double]::Parse($cells[$column],[Globalization.CultureInfo]::InvariantCulture)
            if([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt 0){throw 'Invalid native snapshot-copy observation'}
        }
        $assignedSum+=[double]::Parse($cells[$assignedColumn],[Globalization.CultureInfo]::InvariantCulture)
        $retainedSum+=[double]::Parse($cells[$retainedColumn],[Globalization.CultureInfo]::InvariantCulture)
    }
    if($ReferenceSnapshotCopy -and ($retainedSum -ne 0 -or $assignedSum -le 0)){throw 'Actual native original-copy path not confirmed'}
    if($ExactSnapshotCopy -and -not $ReferenceSnapshotCopy -and $retainedSum -le 0){throw 'Actual experimental reuse path not confirmed'}
    $copyObservation=@{audited_frames=$window.Count;assigned_sum=$assignedSum;retained_sum=$retainedSum;reference_path_confirmed=([bool]$ReferenceSnapshotCopy);experimental_exact_path_confirmed=([bool]$ExactSnapshotCopy -and -not $ReferenceSnapshotCopy)}
}elseif($ReferenceSnapshotCopy -or $ExactSnapshotCopy){throw 'Copy diagnostic requires actual native copy counters'}
$restObservation=Get-RaftSimRestKeyObservation $header $lines[31..($times.Count-30)] ([bool]$ReferenceRestKey)
$result = [ordered]@{
    schema = 'raftsim.south_fork_menu_launch_frame_audit.v1'; label = $Label
    launch_mode = $(if ($review) { "review_station_$ReviewStationM" } else { 'boot_menu' })
    execution_host = $(if ($PackagedRoot -eq '') { 'editor_game' } else { 'cooked_standalone' })
    game_binary = $gameBinary; game_binary_sha256 = $binaryHash
    diagnostic_exec_cmds = $DiagnosticExecCmds
    diagnostic_legacy_breaking_search = [bool]$LegacyBreakingSearch
    diagnostic_legacy_detail_edges = [bool]$LegacyDetailEdges
    diagnostic_reference_snapshot_copy = [bool]$ReferenceSnapshotCopy
    diagnostic_exact_snapshot_copy = [bool]$ExactSnapshotCopy
    diagnostic_reference_rest_key = [bool]$ReferenceRestKey
    native_rest_key_observation = $restObservation
    native_snapshot_copy_observation = $copyObservation
    detail_edge_mode = $detailEdgeMode
    normal_configuration = ($DiagnosticExecCmds -eq '' -and -not $LegacyBreakingSearch -and -not $LegacyDetailEdges -and -not $ReferenceSnapshotCopy -and -not $ExactSnapshotCopy -and -not $ReferenceRestKey -and $collisionArguments.Count -eq 0)
    game_exit_code = $game.ExitCode; csv = $csv; csv_sha256 = (Get-FileHash -LiteralPath $csv -Algorithm SHA256).Hash.ToLower()
    frames_total = $times.Count; audited_rows = "30..$($times.Count - 31)"; audited_frames = $window.Count
    mean_ms = [Math]::Round($mean, 4); p95_ms = [Math]::Round($p95, 4); max_ms = [Math]::Round($max, 4)
    max_consecutive_pair_ms = [Math]::Round($twoFrame, 4); frames_over_100ms = @($window | Where-Object { $_ -gt 100 }).Count
    frames_below_20fps = @($window | Where-Object { $_ -gt 50 }).Count
    minimum_fps = 1000.0 / $max
    target_fps = 20; p95_budget_ms = 50; two_frame_hitch_ms = 100
    # Hitch = any single frame over two 50 ms frame budgets (as in the Sept 26 receipt).
    p95_passes = ($p95 -le 50); hitch_passes = (@($window | Where-Object { $_ -gt 100 }).Count -eq 0)
    runtime_error_count = $runtimeErrors.Count; runtime_errors = $runtimeErrors
    runtime_health_passes = ($runtimeErrors.Count -eq 0)
    healthy_timing_passes = ($runtimeErrors.Count -eq 0 -and @($window | Where-Object { $_ -gt 50 }).Count -eq 0)
    all_map_flythrough_accepted = $false
    physical_acceptance = $false
    diagnostic_collision_arguments = $collisionArguments
    production_collision_defaults = (-not $ExhaustiveLandscapeFaces -and -not $RigidOnlyMovingFaceTree -and -not $OriginalFaceTreeAudit)
}
New-Item -ItemType Directory -Force -Path (Split-Path $receipt) | Out-Null
$result | ConvertTo-Json | Set-Content -LiteralPath $receipt -Encoding UTF8
$result | ConvertTo-Json
