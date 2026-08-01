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

$Project = Join-Path $RepoRoot "unreal\SmokeEmIfYouGotEm.uproject"
$ZambeziMap = Join-Path $RepoRoot "unreal\Content\RaftSim\Maps\EnvironmentPreviews\LandscapeCandidates\L_ZambeziBatokaGorge_PhysicalCorridorCandidate.umap"
if (-not (Test-Path $ZambeziMap)) {
    & "$UeRoot\Engine\Build\BatchFiles\Build.bat" `
        SmokeEmIfYouGotEmEditor Win64 Development $Project `
        -WaitMutex -NoHotReload
    if ($LASTEXITCODE -ne 0) { throw "Windows editor build for Zambezi map generation failed" }
    & "$UeRoot\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
        $Project -unattended -nop4 -nosplash -NoSound -RenderOffscreen `
        -RaftSimCreateLandscapeImportCandidateMaps `
        -RaftSimLandscapeImportCandidateRiverId=zambezi_batoka_gorge `
        -RaftSimExitAfterEnvironmentAutomation
    if ($LASTEXITCODE -ne 0) { throw "Zambezi runnable map generation failed" }
}
if (-not (Test-Path $ZambeziMap)) {
    throw "Zambezi runnable map was not generated: $ZambeziMap"
}

& "$UeRoot\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun `
    -project="$Project" `
    -platform=Win64 -clientconfig=$Config `
    -build -cook -stage -pak -package `
    -archive -archivedirectory="$OutputDir" `
    -nop4 -utf8output -unattended

Write-Host "Packaged: $OutputDir"
