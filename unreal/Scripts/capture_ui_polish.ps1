# Capture the actual packaged front end and South Fork HUD. No scene/content edits.
param(
    [Parameter(Mandatory = $true)][string]$PackageRoot,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$CapturePrefix = 'ui-polish',
    [ValidateSet('intro', 'rivers', 'career', 'settings', 'compact', 'south-fork-pause', 'south-fork-hud')]
    [string[]]$Only = @()
)
$ErrorActionPreference = 'Stop'
$PackageRoot = (Resolve-Path -LiteralPath $PackageRoot).Path
$GameRoot = Join-Path $PackageRoot 'Windows/SmokeEmIfYouGotEm'
$Exe = Join-Path $GameRoot 'Binaries/Win64/SmokeEmIfYouGotEm.exe'
if (-not (Test-Path -LiteralPath $Exe)) { throw "Missing packaged executable: $Exe" }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$OutputDir = (Resolve-Path -LiteralPath $OutputDir).Path
$Cases = @(
    @{ Label = 'intro'; Screen = 'intro'; Width = 1600; Height = 900 },
    @{ Label = 'rivers'; Screen = 'main'; Width = 1600; Height = 900 },
    @{ Label = 'career'; Screen = 'career'; Width = 1600; Height = 900 },
    @{ Label = 'settings'; Screen = 'settings'; Width = 1600; Height = 900 },
    @{ Label = 'compact'; Screen = 'main'; Width = 900; Height = 900 },
    @{ Label = 'south-fork-pause'; Screen = 'pause'; Width = 1600; Height = 900; River = $true },
    @{ Label = 'south-fork-hud'; Screen = 'none'; Width = 1600; Height = 900; River = $true }
)
$Results = @()
foreach ($Case in $Cases) {
    if ($Only.Count -gt 0 -and $Case.Label -notin $Only) { continue }
    $Busy = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(UnrealEditor.*|SmokeEmIfYouGotEm.*)\.exe$'
    }
    if ($Busy) { throw 'Another engine instance is active; capture not started.' }
    $Label = $CapturePrefix + '-' + $Case.Label
    $Screenshot = Join-Path $GameRoot "Saved/Screenshots/$Label.png"
    if (Test-Path -LiteralPath $Screenshot) { throw "Use a fresh package/capture label; refusing stale screenshot: $Screenshot" }
    $Log = Join-Path $OutputDir "$Label.log"
    $Command = if ($Case.River) { 'RaftSim.HudScreen' } else { 'RaftSim.MenuScreen' }
    $Arguments = @('-RenderOffscreen', '-unattended', '-NoSound', '-nosplash', '-windowed', '-ForceRes',
        '-RaftSimEphemeralProfile', "-ResX=$($Case.Width)", "-ResY=$($Case.Height)",
        "-abslog=`"$Log`"", "-ExecCmds=`"$Command $($Case.Screen) capture=$Label`"")
    if ($Case.River) {
        $Arguments = @('/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach',
            '-RaftSimScenario=south_fork_full_descent') + $Arguments
    }
    $Process = Start-Process -FilePath $Exe -ArgumentList $Arguments -WindowStyle Hidden -PassThru
    if (-not $Process.WaitForExit(240000)) { throw "Capture still active after four minutes: PID $($Process.Id). Inspect before retrying." }
    $Process.Refresh()
    if ($Process.ExitCode -ne 0) { throw "Capture $Label failed: $($Process.ExitCode). See $Log" }
    if (-not (Test-Path -LiteralPath $Screenshot)) { throw "No native screenshot produced: $Screenshot" }
    $Errors = Select-String -LiteralPath $Log -Pattern 'Fatal error:|Assertion failed:|Ensure condition failed:|GPU crashed|video memory has been exhausted|out of video memory' -Quiet
    if ($Errors) { throw "Native runtime error in $Log" }
    $Copy = Join-Path $OutputDir "$Label.png"
    Copy-Item -LiteralPath $Screenshot -Destination $Copy
    $Results += [ordered]@{ case = $Case.Label; exit_code = $Process.ExitCode; screenshot = $Copy;
        sha256 = (Get-FileHash -LiteralPath $Copy -Algorithm SHA256).Hash; width = $Case.Width; height = $Case.Height }
    Write-Host "Captured $Label"
}
[ordered]@{ executable = $Exe; executable_sha256 = (Get-FileHash -LiteralPath $Exe -Algorithm SHA256).Hash;
    cases = $Results; manual_pixel_review_required = $true } | ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath (Join-Path $OutputDir 'index.json') -Encoding utf8
