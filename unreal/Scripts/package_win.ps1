# Package a Windows build of RaftSim (release-1.0-plan.md P1/P6).
# Run on a Windows machine with UE 5.8 installed.
# Usage: powershell -File unreal\Scripts\package_win.ps1 [-Config Development|Shipping] [-OutputDir <dir>]
param(
    [string]$Config = "Development",
    [string]$OutputDir = "",
    [string]$UeRoot = "C:\Program Files\Epic Games\UE_5.8"
)

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
if ($OutputDir -eq "") {
    $OutputDir = Join-Path $RepoRoot "unreal\Packaged\Win64-$Config"
}

& "$UeRoot\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun `
    -project="$RepoRoot\unreal\SmokeEmIfYouGotEm.uproject" `
    -platform=Win64 -clientconfig=$Config `
    -build -cook -stage -pak -package `
    -archive -archivedirectory="$OutputDir" `
    -nop4 -utf8output -unattended

Write-Host "Packaged: $OutputDir"
