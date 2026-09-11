param(
    [ValidatePattern('^[a-z0-9_]+$')][string]$Label = 'southfork_water_final',
    [int[]]$Stations = @(120, 12000, 27170, 48000),
    [int]$FrameCount = 8
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$EditorExe = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$Project = Join-Path $ProjectRoot 'SmokeEmIfYouGotEm.uproject'
foreach ($Station in $Stations) {
    if ($Station -lt 0 -or $Station -gt 48900) { throw 'Review station is outside the full South Fork reach.' }
    $CaptureLabel = "${Label}_${Station}"
    $LogPath = Join-Path $ProjectRoot "Saved/Logs/${CaptureLabel}.log"
    Write-Output "Reviewing full-reach station $Station m"
    & $EditorExe $Project /Game/RaftSim/Maps/L_SouthForkAmerican_FullReach `
        -game -Unattended -NoSplash -RenderOffscreen -ResX=1280 -ResY=720 -windowed `
        "-RaftSimWaterReviewStation=$Station" `
        "-ExecCmds=RaftSim.CaptureRaftSeries 10 $FrameCount 0.25 $CaptureLabel 4 0 1.4 14" `
        "-abslog=$LogPath"
    if ($LASTEXITCODE -ne 0) { throw "Game capture failed at $Station m" }
    $LogText = Get-Content -LiteralPath $LogPath -Raw
    if ($LogText -notmatch "no checkpoint near station $Station m") {
        throw "Capture did not verify the requested station $Station m"
    }
    $ImagePath = Join-Path $ProjectRoot "Saved/Screenshots/${CaptureLabel}_000.png"
    if (!(Test-Path -LiteralPath $ImagePath)) { throw "Missing capture: $ImagePath" }
    Write-Output "Verified capture: $ImagePath"
}
