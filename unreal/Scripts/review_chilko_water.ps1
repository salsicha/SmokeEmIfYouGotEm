param(
    [ValidatePattern('^[a-z0-9_]+$')][string]$Label = 'chilko_verified',
    [int[]]$Stations = @(24, 228, 300, 340, 520),
    [int]$FrameCount = 8,
    [float]$CameraLateral = 2.0,
    [ValidateRange(1, 60)][float]$SettleSeconds = 8.0
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Project = Join-Path $ProjectRoot 'SmokeEmIfYouGotEm.uproject'
$EditorExe = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
foreach ($Station in $Stations) {
    if ($Station -lt 0 -or $Station -gt 600) { throw 'Station is outside LavaCanyon.' }
    $CaptureLabel = "${Label}_${Station}"
    $LogPath = Join-Path $ProjectRoot "Saved/Logs/${CaptureLabel}.log"
    Write-Output "Reviewing Chilko station $Station m"
    & $EditorExe $Project /Game/RaftSim/Maps/L_LavaCanyon `
        -game -Unattended -NoSplash -RenderOffscreen -ResX=1280 -ResY=720 -windowed `
        "-ExecCmds=RaftSim.CaptureRaftSeries $SettleSeconds $FrameCount 0.3 $CaptureLabel 3.2 $CameraLateral 1.7 8 station=$Station" `
        "-abslog=$LogPath"
    if ($LASTEXITCODE -ne 0) { throw "Chilko capture failed: $Station" }
    $LogText = Get-Content -LiteralPath $LogPath -Raw
    if ($LogText -notmatch 'walk finished') { throw 'Review station walk did not finish.' }
    if ($LogText -match 'Failed to compile Material') { throw 'Material compilation failed.' }
    for ($Frame = 0; $Frame -lt $FrameCount; ++$Frame) {
        $Suffix = '{0:D3}' -f $Frame
        $ImagePath = Join-Path $ProjectRoot "Saved/Screenshots/${CaptureLabel}_${Suffix}.png"
        if (!(Test-Path -LiteralPath $ImagePath)) { throw "Missing capture: $ImagePath" }
    }
    Write-Output "Verified: $ImagePath"
}
