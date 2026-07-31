# Build, Authenticode-sign, exercise, archive, and checksum the Windows x64 RC.
param(
    [string]$RcRoot = "C:\RaftSimRC\1.0.0-rc1",
    [string]$UeRoot = "C:\Program Files\Epic Games\UE_5.8",
    [string]$CertificateThumbprint = $env:RAFTSIM_WINDOWS_SIGNING_THUMBPRINT,
    [switch]$AllowDirty
)
$ErrorActionPreference = "Stop"

function Assert-NoCompetingUnrealProcesses {
    param([string]$Phase)
    $Competing = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -in @("UnrealEditor", "UnrealEditor-Cmd", "SmokeEmIfYouGotEm")
    }
    if ($Competing) {
        $Summary = ($Competing | ForEach-Object { "$($_.Id) $($_.ProcessName)" }) -join "; "
        throw "Release qualification requires an isolated Unreal/GPU session ($Phase): $Summary"
    }
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$PackageRoot = Join-Path $RcRoot "package"
$ArtifactRoot = Join-Path $RcRoot "artifacts"
Assert-NoCompetingUnrealProcesses "before packaging"
New-Item -ItemType Directory -Force -Path $PackageRoot, $ArtifactRoot | Out-Null

& (Join-Path $PSScriptRoot "package_win.ps1") -Config Shipping -OutputDir $PackageRoot -UeRoot $UeRoot
if ($LASTEXITCODE -ne 0) { throw "Windows package failed" }

$Executable = Get-ChildItem -Path $PackageRoot -Filter "SmokeEmIfYouGotEm.exe" -Recurse | Select-Object -First 1
if ($null -eq $Executable) { throw "Packaged executable not found" }
if ([string]::IsNullOrWhiteSpace($CertificateThumbprint)) {
    throw "RAFTSIM_WINDOWS_SIGNING_THUMBPRINT is required for an RC"
}

$SignTool = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Filter signtool.exe -Recurse |
    Sort-Object FullName -Descending | Select-Object -First 1
if ($null -eq $SignTool) { throw "signtool.exe was not found" }
& $SignTool.FullName sign /sha1 $CertificateThumbprint /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $Executable.FullName
if ($LASTEXITCODE -ne 0) { throw "Authenticode signing failed" }
if ((Get-AuthenticodeSignature $Executable.FullName).Status -ne "Valid") { throw "Authenticode signature is invalid" }

$RapidReport = Join-Path $ArtifactRoot "packaged_rapid_regression.json"
$QaReport = Join-Path $ArtifactRoot "release_candidate_qa.json"
$FreshProfileReport = Join-Path $ArtifactRoot "fresh_profile_first_run.json"
$PerfReport = Join-Path $ArtifactRoot "full_reach_performance_soak.json"

& $Executable.FullName -RaftSimPackagedRegression "-RaftSimValidationOutput=$RapidReport" -NullRHI -NoSound -Unattended -stdout -FullStdOutLogOutput
if ($LASTEXITCODE -ne 0) { throw "Packaged rapid regression failed" }
& $Executable.FullName -RaftSimReleaseCandidateQA "-RaftSimValidationOutput=$QaReport" -NullRHI -NoSound -Unattended -stdout -FullStdOutLogOutput
if ($LASTEXITCODE -ne 0) { throw "Packaged RC QA failed" }
$FreshProfileRoot = Join-Path $RcRoot "fresh-profile-user"
if (Test-Path $FreshProfileRoot) { throw "Fresh-profile QA requires an unused user directory: $FreshProfileRoot" }
& $Executable.FullName -RaftSimFreshProfileQA "-UserDir=$FreshProfileRoot" "-RaftSimValidationOutput=$FreshProfileReport" -NullRHI -NoSound -Unattended -stdout -FullStdOutLogOutput
if ($LASTEXITCODE -ne 0) { throw "Packaged fresh-profile QA failed" }
Assert-NoCompetingUnrealProcesses "before the player-presentation performance soak"
& $Executable.FullName `
    "-UserDir=$FreshProfileRoot" `
    -RaftSimPerformanceSoakSeconds=30 -RaftSimPerformanceWarmupSeconds=10 `
    -RaftSimPerformanceTravelMap=/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach `
    -RaftSimPerformanceRequiredMap=L_SouthForkAmerican_FullReach `
    -RaftSimPerformanceScreenPercentage=75 `
    -RaftSimPerformanceViewDistanceQuality=2 `
    -RaftSimPerformanceAntiAliasingQuality=2 `
    -RaftSimPerformanceGlobalIlluminationQuality=2 `
    -RaftSimPerformanceReflectionQuality=2 `
    -RaftSimPerformanceShadowQuality=2 `
    -RaftSimPerformancePostProcessQuality=2 `
    -RaftSimPerformanceTextureQuality=2 `
    -RaftSimPerformanceEffectsQuality=2 `
    -RaftSimPerformanceFoliageQuality=2 `
    -RaftSimPerformanceShadingQuality=2 `
    -RaftSimPerformanceAntiAliasingMethod=4 `
    -RaftSimPerformanceBloomQuality=5 `
    -RaftSimPerformanceSkeletalMeshLodBias=0 `
    -RaftSimPerformanceLumenTranslucencyRadianceCacheEnabled=0 `
    -RaftSimPerformanceNaniteEnabled=1 `
    -RaftSimPerformanceVolumetricCloudEnabled=1 `
    -ExecCmds="Scalability 2" -unattended -NoSound `
    -windowed -ForceRes -ResX=1920 -ResY=1080 -stdout -FullStdOutLogOutput `
    "-RaftSimValidationOutput=$PerfReport"
if ($LASTEXITCODE -ne 0) { throw "Packaged performance soak failed" }

$Arguments = @(
    (Join-Path $RepoRoot "Scripts\release_candidate.py"), "finalize",
    "--platform", "windows", "--package-root", $PackageRoot,
    "--output-dir", $ArtifactRoot, "--configuration", "Shipping",
    "--signature-policy", "any-valid",
    "--qa-report", $RapidReport, "--qa-report", $QaReport,
    "--qa-report", $FreshProfileReport, "--qa-report", $PerfReport
)
if ($AllowDirty) { $Arguments += "--allow-dirty" }
& python @Arguments
if ($LASTEXITCODE -ne 0) { throw "Release artifact finalization failed" }

$VerifyArguments = @(
    (Join-Path $RepoRoot "Scripts\release_candidate.py"), "verify-artifact",
    "--manifest", (Join-Path $ArtifactRoot "windows-x64-release-manifest.json"),
    "--artifact-dir", $ArtifactRoot, "--platform", "windows",
    "--output", (Join-Path $ArtifactRoot "windows-x64-release-verification.json")
)
if ($AllowDirty) { $VerifyArguments += "--allow-dirty" }
& python @VerifyArguments
if ($LASTEXITCODE -ne 0) { throw "Release artifact verification failed" }

Write-Host "Windows RC artifacts: $ArtifactRoot"
