# Package a Windows build of RaftSim (release-1.0-plan.md P1/P6).
# Run on a Windows machine with UE 5.8 installed.
# Usage: powershell -File unreal\Scripts\package_win.ps1 [-Config Development|Shipping] [-OutputDir <dir>]
param(
    [string]$Config = "Development",
    [string]$OutputDir = "",
    [string]$UeRoot = "C:\Program Files\Epic Games\UE_5.8"
)

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$busy=@(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|SmokeEmIfYouGotEm.*|ShaderCompileWorker|UnrealPak|link|raftsim_cartesian_cook|raftsim_water_solver)\.exe$' -or
    ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
})
if($busy.Count){throw 'Shared engine/build is busy; no DLL replacement or duplicate cook started'}
foreach($pending in Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'tmp') -Filter 'pinball-reference-install-*.pending.json' -ErrorAction SilentlyContinue){
    if(!(Test-Path -LiteralPath ($pending.FullName -replace '\.pending\.json$','.json'))){
        throw "Unfinished paired terrain/flow installation: $($pending.FullName). Finalize it after Unreal exits before packaging."
    }
}
if ($OutputDir -eq "") {
    $OutputDir = Join-Path $RepoRoot "unreal\Packaged\Win64-$Config"
}

$Project = Join-Path $RepoRoot "unreal\SmokeEmIfYouGotEm.uproject"
$ZambeziMap = Join-Path $RepoRoot "unreal\Content\RaftSim\Maps\L_Zambezi.umap"
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
    -platform=Win64 "-clientconfig=$Config" `
    -build -cook -stage -pak -package `
    -archive -archivedirectory="$OutputDir" `
    -nop4 -utf8output -unattended

if ($LASTEXITCODE -ne 0) { throw "Windows packaging failed with exit code $LASTEXITCODE" }
Write-Host "Packaged: $OutputDir"
