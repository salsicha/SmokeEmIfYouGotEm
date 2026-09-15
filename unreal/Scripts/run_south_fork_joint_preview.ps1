param(
    [Parameter(Mandatory = $true)][string]$Manifest,
    [Parameter(Mandatory = $true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$Label,
    [ValidateSet('source', 'shore', 'fixed')][string]$Camera = 'source',
    [string]$Editor = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
)
$ErrorActionPreference = 'Stop'
$repoPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$manifestFile = [IO.Path]::GetFullPath((Join-Path $repoPath $Manifest))
$tmpRoot = Join-Path $repoPath 'tmp'
if (-not $manifestFile.StartsWith($tmpRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Preview descriptor must be inside this repository tmp directory'
}
$descriptor = Get-Content -LiteralPath $manifestFile -Raw | ConvertFrom-Json
if ($descriptor.schema -ne 'raftsim.south_fork_joint_preview.v1' -or $descriptor.candidate -ne $true -or $descriptor.production_promoted -ne $false) {
    throw 'An explicit unaccepted joint-preview descriptor is required'
}
$relativeManifest = [IO.Path]::GetRelativePath($repoPath, $manifestFile).Replace('\', '/')
$logFile = Join-Path $tmpRoot ($Label + '.log')
$reportFile = Join-Path $tmpRoot ($Label + '-run.json')
$screenRoot = Join-Path $repoPath 'unreal/Saved/Screenshots'
if ((Test-Path -LiteralPath $logFile) -or (Test-Path -LiteralPath $reportFile) -or
    (Get-ChildItem -LiteralPath $screenRoot -Filter ($Label + '_*.png') -ErrorAction SilentlyContinue)) {
    throw 'Use a fresh label; existing evidence will not be overwritten'
}
$pose = switch ($Camera) {
    'source' { '-545095 -362309 1800 -27.8 18.075' }
    'shore' { 'shore_left' }
    'fixed' { 'river_station_downstream focusstation=8350 focuslateral=0' }
}
$editorArgs = @(
    (Join-Path $repoPath 'unreal/SmokeEmIfYouGotEm.uproject'),
    '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach', '-game', '-RenderOffscreen',
    '-Unattended', '-NoSplash', '-NoSound', '-ResX=1280', '-ResY=720', '-Windowed', '-d3d12',
    '-RaftSimEphemeralProfile', '-RaftSimScenario=south_fork_full_descent', '-RaftSimWaterReviewStation=8330',
    "-RaftSimJointReconstructionPreview=$relativeManifest",
    "-ExecCmds=RaftSim.CaptureSeries 12 3 1 $Label $pose record", "-abslog=$logFile"
)
& $Editor @editorArgs
$engineExitCode = $LASTEXITCODE
$logText = Get-Content -LiteralPath $logFile -Raw
# UE Windows graceful shutdown requested during EngineInit can return 0 even
# after RequestExitWithStatus(false, 1). Require positive runtime evidence too.
$installed = [regex]::Matches($logText, 'RaftSim joint reconstruction preview installed before BeginPlay: cap=(\w+) source_time=([\d.]+)')
$refused = $logText -match 'Joint reconstruction preview refused before BeginPlay'
$singleSurface = $logText -match 'RaftSim water surface mode: carrier=1 volumeCore=1 singleSurface=1'
$recorded = $logText -match 'RaftSim recording saved: .+\.mp4 \(\d+ source_frames, [\d.]+ s;'
$screens = @(Get-ChildItem -LiteralPath $screenRoot -Filter ($Label + '_*.png') -ErrorAction SilentlyContinue)
$passed = $engineExitCode -eq 0 -and -not $refused -and $installed.Count -eq 1 -and
    $installed[0].Groups[1].Value -eq $descriptor.source_cap_sha256 -and
    [Math]::Abs([double]$installed[0].Groups[2].Value - $descriptor.source_time_seconds) -le 1e-9 -and
    $singleSurface -and $recorded -and $screens.Count -eq 3
[ordered]@{
    schema = 'raftsim.joint_preview_run.v1'
    runtime_capture_completed = $passed
    descriptor_sha256 = (Get-FileHash -LiteralPath $manifestFile -Algorithm SHA256).Hash.ToLowerInvariant()
    engine_exit_code = $engineExitCode
    preflight_refused = $refused
    install_count = $installed.Count
    single_surface_started = $singleSurface
    recording_finalized = $recorded
    screenshot_count = $screens.Count
    log_sha256 = (Get-FileHash -LiteralPath $logFile -Algorithm SHA256).Hash.ToLowerInvariant()
    camera = $Camera
    visual_accepted = $false
    performance_accepted = $false
    production_promoted = $false
} | ConvertTo-Json | Set-Content -LiteralPath $reportFile
if (-not $passed) { throw "Joint preview failed; see $logFile (engine exit $engineExitCode is not sufficient evidence)" }
Write-Output "Verified runtime capture completed: $reportFile; visual/performance acceptance remains open"
