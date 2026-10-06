param(
    [ValidatePattern('^[a-z0-9_]+$')][string]$Label = 'pacuare_verified',
    [int[]]$Stations = @(24, 280, 310, 380),
    [int]$FrameCount = 8,
    [float]$CameraLateral = 2.0
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Project = Join-Path $ProjectRoot 'SmokeEmIfYouGotEm.uproject'
$EditorExe = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
foreach ($Station in $Stations) {
    if ($Station -lt 0 -or $Station -gt 600) { throw 'Station is outside Upper Huacas.' }
    $CaptureLabel = "${Label}_${Station}"
    $LogPath = Join-Path $ProjectRoot "Saved/Logs/${CaptureLabel}.log"
    Write-Output "Reviewing Pacuare station $Station m"
    & $EditorExe $Project /Game/RaftSim/Maps/L_UpperHuacas `
        -game -Unattended -NoSplash -RenderOffscreen -ResX=1280 -ResY=720 -windowed `
        "-ExecCmds=RaftSim.CaptureRaftSeries 8 $FrameCount 0.3 $CaptureLabel 3.2 $CameraLateral 1.7 8 station=$Station" `
        "-abslog=$LogPath"
    if ($LASTEXITCODE -ne 0) { throw "Pacuare capture failed: $Station" }
    $LogText = Get-Content -LiteralPath $LogPath -Raw
    if ($LogText -notmatch 'walk finished') { throw 'Review station walk did not finish.' }
    if ($LogText -match 'Failed to compile Material') { throw 'Material compilation failed.' }
    $ImagePath = Join-Path $ProjectRoot "Saved/Screenshots/${CaptureLabel}_000.png"
    if (!(Test-Path -LiteralPath $ImagePath)) { throw "Missing capture: $ImagePath" }
    Write-Output "Verified: $ImagePath"
}
